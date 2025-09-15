import os
import json
import base64
import asyncio
import logging
import threading
from typing import Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
import pyaudio
import websockets

import io
import wave
import random
import queue
import time
import math, struct


# =========================
# Config & constants
# =========================
load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes (16-bit)
CHUNK_SIZE = 1024
WS_HOST = os.getenv("HUME_WS_HOST", "api.hume.ai")  # align with OAuth host
OAUTH_HOST = os.getenv("HUME_OAUTH_HOST", WS_HOST)
CAPTURE_RATE_DEFAULT = int(os.getenv("HUME_CAPTURE_RATE", "16000"))  # common, ASR-friendly

# =========================
# Logging
# =========================
logger = logging.getLogger("hume_app")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# =========================
# Authenticator
# =========================
class Authenticator:
    def __init__(self, api_key: str, secret_key: str, host: str = OAUTH_HOST):
        self.api_key = api_key
        self.secret_key = secret_key
        self.host = host

    def fetch_access_token(self) -> str:
        import requests
        auth_bytes = f"{self.api_key}:{self.secret_key}".encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + base64.b64encode(auth_bytes).decode("utf-8"),
        }
        data = {"grant_type": "client_credentials"}
        try:
            resp = requests.post(f"https://{self.host}/oauth2-cc/token", headers=headers, data=data, timeout=15)
            resp.raise_for_status()
            body = resp.json()
        except Exception as e:
            raise RuntimeError(f"OAuth token request failed: {e}") from e
        token = body.get("access_token")
        if not token:
            raise RuntimeError(f"OAuth response missing access_token: {body}")
        return token

# =========================
# Audio device manager
# =========================
class DeviceManager:
    def __init__(self, pa: pyaudio.PyAudio):
        self.pa = pa

    def list_devices(self):
        n = self.pa.get_device_count()
        ins, outs = [], []

        def _as_int(x, default=0):
            # robustly coerce str/float/None -> int
            try:
                if x is None:
                    return default
                return int(float(x))
            except Exception:
                return default

        for i in range(n):
            try:
                info = self.pa.get_device_info_by_index(i)
            except Exception:
                continue  # skip devices we can't query

            name = str(info.get("name", f"Device {i}"))
            sr = _as_int(info.get("defaultSampleRate"), 16000)
            in_ch = _as_int(info.get("maxInputChannels"), 0)
            out_ch = _as_int(info.get("maxOutputChannels"), 0)

            if in_ch > 0:
                ins.append((i, name, sr))
            if out_ch > 0:
                outs.append((i, name, sr))

        return ins, outs

    def open_input(self, index: int, sample_rate: int):
        return self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=sample_rate,
            input=True,
            input_device_index=index,
            frames_per_buffer=CHUNK_SIZE,
        )

    def open_output(self, index: int, sample_rate: int):
        return self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=sample_rate,
            output=True,
            output_device_index=index,
            frames_per_buffer=CHUNK_SIZE,
        )
        
    def safe_open_output(self, preferred_index: int, rate: int, channels: int, sampwidth: int):
        """
        Try the selected device first; if it fails, fall back to system default,
        then to the first available output device. Returns (stream, used_index).
        """
        fmt_map = {1: pyaudio.paInt8, 2: pyaudio.paInt16, 3: pyaudio.paInt24, 4: pyaudio.paInt32}
        fmt = fmt_map.get(sampwidth, pyaudio.paInt16)

        # 1) Preferred device
        try:
            s = self.pa.open(
                format=fmt, channels=channels, rate=rate,
                output=True, output_device_index=preferred_index,
                frames_per_buffer=CHUNK_SIZE,
            )
            return s, preferred_index
        except Exception as e:
            logger.debug(f"safe_open_output: preferred device #{preferred_index} failed: {e}")

        # 2) System default (omit index)
        try:
            s = self.pa.open(
                format=fmt, channels=channels, rate=rate,
                output=True, frames_per_buffer=CHUNK_SIZE,
            )
            return s, None  # None = default device
        except Exception as e:
            logger.debug(f"safe_open_output: default device failed: {e}")

        # 3) First available output device
        try:
            _, outs = self.list_devices()
            for idx, _name, _sr in outs:
                try:
                    s = self.pa.open(
                        format=fmt, channels=channels, rate=rate,
                        output=True, output_device_index=idx,
                        frames_per_buffer=CHUNK_SIZE,
                    )
                    logger.info(f"safe_open_output: fell back to output device #{idx}")
                    return s, idx
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"safe_open_output: listing outputs failed: {e}")

        raise RuntimeError("No usable output device for the received audio format.")


# =========================
# Async loop in a background thread
# =========================
from typing import Coroutine, Any, TypeVar
from concurrent.futures import Future
import atexit

T = TypeVar("T")

class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self._stopping = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        # Ensure cleanup if the process exits without clicking Stop
        atexit.register(self._atexit_cleanup)

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro: Coroutine[Any, Any, T]) -> Future[T]:
        if not self.loop.is_running():
            raise RuntimeError("Background loop is not running")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def stop(self) -> None:
        if self._stopping.is_set():
            return
        self._stopping.set()

        def _cancel_all():
            # Runs inside the loop thread
            try:
                current = asyncio.current_task()
                for task in asyncio.all_tasks():
                    if task is not current:
                        task.cancel()
            except Exception:
                pass
            # stop the loop after scheduling cancels
            self.loop.stop()

        try:
            self.loop.call_soon_threadsafe(_cancel_all)
        except RuntimeError:
            # loop might already be closed
            pass

        # Wait briefly for thread to exit run_forever()
        self.thread.join(timeout=2)

        # Close the loop to release resources
        try:
            self.loop.close()
        except Exception:
            pass

    def _atexit_cleanup(self):
        # Best-effort cleanup at interpreter shutdown
        try:
            self.stop()
        except Exception:
            pass


# =========================
# Connection: WS + audio streaming
# =========================
class Connection:
    def __init__(self, pa: pyaudio.PyAudio):
        self.pa = pa

    async def run(
        self,
        socket_url: str,
        input_stream,
        output_index: int,
        sample_rate: int,
        stop_event: threading.Event,
        ui_queue: Optional[queue.Queue] = None,
    ):
        backoff = 1.0
        MAX_BACKOFF = 20.0

        while not stop_event.is_set():
            send_task = recv_task = None
            try:
                # Tighter timeouts; big frames allowed
                async with websockets.connect(
                    socket_url,
                    ping_interval=15,
                    ping_timeout=15,
                    close_timeout=5,
                    max_size=16 * 1024 * 1024,
                ) as ws:
                    logger.info("WebSocket connected.")
                    # Make UI queue visible to receiver tasks
                    self._ui_queue = ui_queue
                    if ui_queue:
                        ui_queue.put({"ts": time.time(), "level": "info", "msg": "WebSocket connected."})

                    backoff = 1.0  # reset on successful connect

                    # Send session settings ONCE per connection
                    session_settings = {
                        "type": "session_settings",
                        "audio": {
                            "encoding": "linear16",
                            "sample_rate": int(sample_rate),
                            "channels": int(CHANNELS),
                        },
                        "prompt": "Your goal is to provide soothing support to them.",
                    }
                    await ws.send(json.dumps(session_settings))

                    # Start workers
                    send_task = asyncio.create_task(
                        self._send_audio(ws, input_stream, sample_rate, stop_event)
                    )
                    recv_task = asyncio.create_task(
                        self._recv_audio(ws, output_index, sample_rate, stop_event)
                    )

                    # If either task fails, bubble up
                    done, pending = await asyncio.wait(
                        {send_task, recv_task},
                        return_when=asyncio.FIRST_EXCEPTION,
                    )
                    for t in done:
                        exc = t.exception()
                        if exc:
                            raise exc
                    for t in pending:
                        t.cancel()

            except asyncio.CancelledError:
                # shutting down
                break
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket closed ({e.code}: {e.reason}). Reconnecting in {backoff:.1f}s…")
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff = min(MAX_BACKOFF, backoff * 1.7)
            except Exception as e:
                logger.warning(f"WebSocket error: {e}. Reconnecting in {backoff:.1f}s…")
                await asyncio.sleep(backoff + random.uniform(0, 0.5))
                backoff = min(MAX_BACKOFF, backoff * 1.7)
            finally:
                # Ensure tasks are cancelled between reconnects
                for t in (send_task, recv_task):
                    if t and not t.done():
                        try:
                            t.cancel()
                        except Exception:
                            pass

    async def _send_audio(self, ws, input_stream, _sample_rate: int, stop_event: threading.Event):
        CHUNKS_PER_BATCH = 4
        chunks = []
        total_bytes = 0
        try:
            while not stop_event.is_set():
                data = await asyncio.to_thread(
                    input_stream.read, CHUNK_SIZE, exception_on_overflow=False
                )
                if not data:
                    await asyncio.sleep(0.002)
                    continue

                chunks.append(data)
                total_bytes += len(data)

                if len(chunks) >= CHUNKS_PER_BATCH:
                    payload = base64.b64encode(b"".join(chunks)).decode("ascii")
                    chunks.clear()

                    await ws.send(json.dumps({
                        "type": "audio_input",
                        "data": payload,
                    }))
                    logger.debug(f"mic->ws sent ~{CHUNKS_PER_BATCH} chunks; total_bytes={total_bytes}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug(f"_send_audio error: {e}")
            raise


    async def _recv_audio(self, ws, output_index: int, sample_rate: int, stop_event: threading.Event):
        import io, wave
        from typing import Optional
        
        ui_queue = getattr(self, "_ui_queue", None)

        out_stream: Optional[pyaudio.Stream] = None
        cur_rate: Optional[int] = None
        cur_channels: Optional[int] = None
        cur_format: Optional[int] = None  # pyaudio format constant

        def _open_out(rate: int, channels: int, sampwidth: int):
            try:
                stream, used_idx = DeviceManager(self.pa).safe_open_output(output_index, rate, channels, sampwidth)
                fmt_map = {1: pyaudio.paInt8, 2: pyaudio.paInt16, 3: pyaudio.paInt24, 4: pyaudio.paInt32}
                fmt = fmt_map.get(sampwidth, FORMAT)
                logger.debug(f"opened output stream: rate={rate}, ch={channels}, sampwidth={sampwidth}, device={'default' if used_idx is None else used_idx}")
                return stream, rate, channels, fmt
            except Exception as e:
                logger.error(f"Failed to open any output device (rate={rate}, ch={channels}, width={sampwidth}): {e}")
                return None, None, None, None

        try:
            async for message in ws:
                if stop_event.is_set():
                    break

                # Binary frames (rare): treat as raw PCM with current/default params
                if isinstance(message, (bytes, bytearray)):
                    if out_stream is None:
                        out_stream, cur_rate, cur_channels, cur_format = _open_out(sample_rate, CHANNELS, 2)
                    stream = out_stream
                    if stream is None:
                        continue  # safety for type-checkers
                    try:
                        stream.write(message)
                    except Exception as e:
                        logger.debug(f"audio write (binary) failed: {e}")
                    continue

                # Text frames → JSON
                # Text frames → JSON
                try:
                    msg = json.loads(message)
                except Exception:
                    continue

                mtype = msg.get("type")
                logger.debug(f"ws<- msg type={mtype} keys={list(msg.keys())}")

                if mtype == "audio_output":
                    # Accept both 'data' (WAV b64) and 'audio' (may be WAV or raw PCM)
                    b64 = msg.get("data") or msg.get("audio")
                    if not b64:
                        logger.debug("audio_output with empty payload")
                        continue

                    blob = base64.b64decode(b64)
                    logger.debug(f"audio_output bytes={len(blob)}")

                    # Try to detect WAV (RIFF header)
                    is_wav = len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WAVE"

                    pcm = None
                    wav_rate = None
                    wav_channels = None
                    wav_width = None

                    if is_wav:
                        # Parse WAV container
                        try:
                            with wave.open(io.BytesIO(blob), "rb") as wf:
                                wav_rate = wf.getframerate()
                                wav_channels = wf.getnchannels()
                                wav_width = wf.getsampwidth()
                                pcm = wf.readframes(wf.getnframes())
                            logger.debug(f"parsed WAV: rate={wav_rate}, ch={wav_channels}, width={wav_width}, frames={len(pcm)}")
                        except Exception as e:
                            logger.debug(f"failed to parse WAV from audio_output: {e}")
                            continue
                    else:
                        # Try raw PCM path (server may send format hints)
                        fmt = msg.get("audio_format") or {}
                        wav_rate = int(fmt.get("sample_rate") or sample_rate)
                        wav_channels = int(fmt.get("channels") or CHANNELS)
                        # Default to s16le (2 bytes)
                        wav_width = int(fmt.get("sampwidth") or 2)
                        pcm = blob
                        logger.debug(f"treating audio_output as RAW PCM: rate={wav_rate}, ch={wav_channels}, width={wav_width}, frames={len(pcm)}")

                    # (Re)open output if needed
                    need_new = (
                        out_stream is None
                        or cur_rate != wav_rate
                        or cur_channels != wav_channels
                    )
                    if need_new:
                        if out_stream:
                            try:
                                out_stream.stop_stream()
                                out_stream.close()
                            except Exception:
                                pass
                        out_stream, cur_rate, cur_channels, cur_format = _open_out(wav_rate, wav_channels, wav_width)
                        if out_stream is None:
                            logger.error("Unable to open any output device; dropping audio chunk.")
                            continue

                    # UI event: audio arrived
                    if ui_queue and pcm is not None:
                        ui_queue.put({"ts": time.time(), "level": "info",
                                    "msg": f"audio_output: {len(pcm)} bytes, {wav_rate} Hz, ch={wav_channels}, w={wav_width}"})

                    # Tiny jitter buffer/batching to reduce underruns
                    try:
                        if len(pcm) > CHUNK_SIZE * wav_channels * wav_width:
                            buf = memoryview(pcm)
                            frame_bytes = CHUNK_SIZE * wav_channels * wav_width
                            offset = 0
                            while offset < len(buf):
                                end = min(len(buf), offset + frame_bytes)
                                out_stream.write(buf[offset:end])
                                offset = end
                        else:
                            out_stream.write(pcm)
                    except Exception as e:
                        logger.debug(f"audio write failed: {e}. Attempting to reopen output and retry once.")
                        try:
                            if out_stream:
                                try:
                                    out_stream.stop_stream()
                                    out_stream.close()
                                except Exception:
                                    pass
                            out_stream, cur_rate, cur_channels, cur_format = _open_out(wav_rate, wav_channels, wav_width)
                            if out_stream:
                                out_stream.write(pcm)
                            else:
                                logger.error("Reopen failed; dropping audio.")
                        except Exception as e2:
                            logger.error(f"Reopen+retry failed: {e2}")

                elif mtype in ("assistant_message", "assistant_text", "message"):
                    text = msg.get("text") or msg.get("message") or msg.get("content")
                    if text:
                        logger.info(f"assistant: {text[:200]}")
                        if ui_queue:
                            ui_queue.put({"ts": time.time(), "level": "assistant", "msg": text})

                elif isinstance(mtype, str) and mtype.startswith("transcript"):
                    text = msg.get("text") or msg.get("content")
                    if text:
                        logger.debug(f"{mtype}: {text[:200]}")
                        if ui_queue:
                            ui_queue.put({"ts": time.time(), "level": "transcript", "msg": f"{mtype}: {text}"})

                elif mtype == "error":
                    code = msg.get("code")
                    slug = msg.get("slug")
                    detail = msg.get("message")
                    req = msg.get("request_id")
                    full = f"code={code}, slug={slug}, message={detail}, request_id={req}"
                    logger.error(f"Server error: {full}")
                    if ui_queue:
                        ui_queue.put({"ts": time.time(), "level": "error", "msg": full})

                else:
                    logger.debug(f"unhandled msg: {msg}")

        finally:
            if out_stream:
                try:
                    out_stream.stop_stream()
                    out_stream.close()
                except Exception:
                    pass

    async def tts_probe(
        self,
        socket_url: str,
        output_index: int,
        sample_rate: int,
        text: str,
        stop_event: threading.Event,
        ui_queue: Optional[queue.Queue] = None,
    ):
        """Open a short-lived WS, request TTS for `text`, play first audio_output, post events to UI."""
        def _open_out(rate: int, channels: int, sampwidth: int):
            try:
                stream, _ = DeviceManager(self.pa).safe_open_output(output_index, rate, channels, sampwidth)
                return stream
            except Exception as e:
                logger.error(f"TTS probe: output open failed: {e}")
                return None

        async with websockets.connect(
            socket_url,
            ping_interval=15, ping_timeout=15, close_timeout=5, max_size=16 * 1024 * 1024
        ) as ws:
            # Session settings (define audio format once)
            await ws.send(json.dumps({
                "type": "session_settings",
                "audio": {"encoding": "linear16", "sample_rate": int(sample_rate), "channels": int(CHANNELS)}
            }))

            # Send a user text turn and ask the assistant to respond
            await ws.send(json.dumps({"type": "user_input", "text": text}))

            out_stream = None
            try:
                async for message in ws:
                    if isinstance(message, (bytes, bytearray)):
                        continue

                    try:
                        msg = json.loads(message)
                    except Exception:
                        continue

                    mtype = msg.get("type")
                    if mtype == "audio_output":
                        b64 = msg.get("data") or msg.get("audio")
                        if not b64:
                            continue
                        blob = base64.b64decode(b64)

                        # WAV or raw PCM?
                        if len(blob) >= 12 and blob[:4] == b"RIFF" and blob[8:12] == b"WAVE":
                            with wave.open(io.BytesIO(blob), "rb") as wf:
                                rate = wf.getframerate()
                                ch = wf.getnchannels()
                                w = wf.getsampwidth()
                                pcm = wf.readframes(wf.getnframes())
                        else:
                            rate = sample_rate; ch = CHANNELS; w = 2; pcm = blob

                        if ui_queue:
                            ui_queue.put({"ts": time.time(), "level": "info",
                                        "msg": f"[TTS] audio_output: {len(pcm)} bytes @ {rate} Hz, ch={ch}, w={w}"})

                        if out_stream is None:
                            out_stream = _open_out(rate, ch, w)
                            if out_stream is None:
                                if ui_queue:
                                    ui_queue.put({"ts": time.time(), "level": "error",
                                                "msg": "TTS probe: unable to open output device."})
                                return

                        out_stream.write(pcm)
                        return  # stop after first audio chunk

                    elif mtype in ("assistant_message", "assistant_text"):
                        txt = msg.get("text") or ""
                        if ui_queue and txt:
                            ui_queue.put({"ts": time.time(), "level": "assistant", "msg": f"[TTS] {txt}"})

                    elif mtype == "error":
                        full = f"code={msg.get('code')}, slug={msg.get('slug')}, message={msg.get('message')}, request_id={msg.get('request_id')}"
                        logger.error(f"TTS probe error: {full}")
                        if ui_queue:
                            ui_queue.put({"ts": time.time(), "level": "error", "msg": f"[TTS] {full}"})
                        return
            finally:
                try:
                    if out_stream:
                        out_stream.stop_stream(); out_stream.close()
                except Exception:
                    pass


# =========================
# UI helpers (Lottie kept separate)
# =========================

def render_lottie_mic_visualizer(lottie_json_path: str = "media/hume.json", height: int = 260):
    """Render a Lottie animation that reacts to the live microphone in the browser (Web Audio API)."""
    import streamlit.components.v1 as components
    if not os.path.exists(lottie_json_path):
        st.info("Lottie file not found; skipping animation.")
        return
    try:
        with open(lottie_json_path, "r", encoding="utf-8") as f:
            lottie_json = f.read()
        # Ensure safe embedding by round-tripping through json
        lottie_js_data = json.dumps(json.loads(lottie_json))
    except Exception:
        st.info("Invalid Lottie JSON; skipping animation.")
        return

    html = f"""
    <style>
      #viz-wrap {{
        width: 100%;
        height: {height}px;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      #lottie {{
        width: 100%;
        height: 100%;
        transform-origin: center center;
      }}
      .note {{
        font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
        font-size: 13px;
        color: #6b7280;
        text-align: center;
        margin-top: 8px;
      }}
    </style>
    <div id="viz-wrap"><div id="lottie"></div></div>
    <div class="note">Allow microphone access to see the animation react in real&nbsp;time.</div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.10.2/lottie.min.js"></script>
    <script>
      (async () => {{
        const animationData = {lottie_js_data};
        const container = document.getElementById('lottie');
        const anim = lottie.loadAnimation({{
          container,
          renderer: 'svg',
          loop: true,
          autoplay: true,
          animationData
        }});

        function rms(buf) {{
          let sum = 0;
          for (let i = 0; i < buf.length; i++) {{
            const v = (buf[i] - 128) / 128; // center & normalize 0..255 -> -1..1
            sum += v * v;
          }}
          return Math.sqrt(sum / buf.length); // 0..~1
        }}

        try {{
          const stream = await navigator.mediaDevices.getUserMedia({{ audio: {{ echoCancellation: true, noiseSuppression: true }} }});
          const Ctx = window.AudioContext || window.webkitAudioContext;
          const ctx = new Ctx();
          const src = ctx.createMediaStreamSource(stream);
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 1024;
          src.connect(analyser);
          const buf = new Uint8Array(analyser.fftSize);

          function tick() {{
            analyser.getByteTimeDomainData(buf);
            const level = rms(buf);
            // Map level -> speed & subtle scale
            const speed = 0.5 + Math.min(2.0, level * 3.0);
            anim.setSpeed(speed);
            const scale = 1 + Math.min(0.35, level * 0.8);
            container.style.transform = `scale(${{scale}})`;
            requestAnimationFrame(tick);
          }}
          tick();

          // Resume context on first user gesture (Safari/iOS autoplay policies)
          document.addEventListener('click', () => {{ if (ctx.state === 'suspended') ctx.resume(); }});
        }} catch (err) {{
          console.warn('Mic permission/init failed:', err);
          // Gentle idle pulse fallback
          let t = 0;
          function idle() {{
            t += 0.02;
            const scale = 1 + 0.05 * Math.sin(t);
            container.style.transform = `scale(${{scale}})`;
            requestAnimationFrame(idle);
          }}
          idle();
        }}
      }})();
    </script>
    """
    components.html(html, height=height + 60)
    
def preflight_audio_open(dev: DeviceManager, in_idx: int, out_idx: int, sample_rate: int) -> Optional[str]:
    # Probe mic
    try:
        s_in = dev.open_input(in_idx, sample_rate)
        s_in.stop_stream(); s_in.close()
    except Exception as e:
        return f"Microphone cannot open at {sample_rate} Hz: {e}"

    # Probe speaker
    try:
        s_out = dev.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=sample_rate,
            output=True,
            output_device_index=out_idx,
            frames_per_buffer=CHUNK_SIZE,
        )
        s_out.stop_stream(); s_out.close()
    except Exception as e:
        return f"Speaker cannot open at {sample_rate} Hz: {e}"

    return None

def drain_ui_queue_and_render(events_placeholder):
    """Pull events from the background WS thread and render a short log in the UI."""
    q = st.session_state.ui_queue
    if not q:
        return

    # Drain without blocking
    pulled = 0
    while True:
        try:
            evt = q.get_nowait()
        except queue.Empty:
            break
        else:
            pulled += 1
            st.session_state.ui_events.append(evt)
            # trim
            if len(st.session_state.ui_events) > st.session_state.max_ui_events:
                st.session_state.ui_events = st.session_state.ui_events[-st.session_state.max_ui_events:]

    # Render (most recent last)
    if st.session_state.ui_events:
        lines = []
        for e in st.session_state.ui_events[-50:]:  # keep it readable
            ts = time.strftime("%H:%M:%S", time.localtime(e.get("ts", time.time())))
            lvl = e.get("level", "info")
            msg = e.get("msg", "")
            if lvl == "error":
                prefix = "🛑"
            elif lvl == "warn":
                prefix = "⚠️"
            elif lvl == "assistant":
                prefix = "🗣️"
            elif lvl == "transcript":
                prefix = "🎙️"
            else:
                prefix = "ℹ️"
            lines.append(f"{ts} {prefix} {msg}")
        events_placeholder.code("\n".join(lines))

def play_test_tone(pa: pyaudio.PyAudio, out_idx: int, rate: int = 16000, freq: int = 440, dur: float = 0.7):
    """Plays a short sine beep to verify your output path/device independent of the server."""
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=rate,
                     output=True, output_device_index=out_idx, frames_per_buffer=CHUNK_SIZE)
    try:
        frames = bytearray()
        amp = int(32767 * 0.2)
        total = int(dur * rate)
        for n in range(total):
            sample = int(amp * math.sin(2 * math.pi * freq * n / rate))
            frames += struct.pack("<h", sample)
        stream.write(bytes(frames))
    finally:
        try:
            stream.stop_stream(); stream.close()
        except Exception:
            pass


# =========================
# Main App
# =========================

def ensure_state_defaults():
    st.session_state.setdefault("access_token", "")
    st.session_state.setdefault("chat_active", False)
    st.session_state.setdefault("loop_thread", None)
    st.session_state.setdefault("stream_future", None)
    st.session_state.setdefault("stop_event", None)
    st.session_state.setdefault("input_stream", None)
    st.session_state.setdefault("config_id", "")
    st.session_state.setdefault("debug_logs", False)
    st.session_state.setdefault("last_error", "")
    st.session_state.setdefault("ui_queue", None)   # thread-safe bridge from WS -> UI
    st.session_state.setdefault("ui_events", [])    # rendered event history
    st.session_state.setdefault("max_ui_events", 200)

def main():
    st.set_page_config(page_title="Hume Voice Chat (clean)", page_icon="🎧", layout="centered")
    ensure_state_defaults()

    st.title("Hume Voice Chat — clean rewrite")
    # Branding (optional)
    logo_path = "media/mainlogo.png"
    if hasattr(st, "logo") and os.path.exists(logo_path):
        st.logo(logo_path)
    elif os.path.exists(logo_path):
        st.image(logo_path, width=160)

    # ===== Auth =====
    with st.sidebar:
        st.header("Authentication")
        api_key = st.text_input("HUME_API_KEY", os.getenv("HUME_API_KEY", ""), type="password")
        secret_key = st.text_input("HUME_SECRET_KEY", os.getenv("HUME_SECRET_KEY", ""), type="password")
        host_choice = st.selectbox("API Host", [WS_HOST, "test-api.hume.ai"], index=0)
        debug_on = st.checkbox("Enable debug logs", value=bool(os.getenv("HUME_DEBUG", "0") == "1"))
        st.session_state.debug_logs = debug_on
        logger.setLevel(logging.DEBUG if debug_on else logging.INFO)
        config_id = st.text_input("EVI Config ID", os.getenv("HUME_CONFIG_ID", ""))
        st.session_state.config_id = config_id.strip()   
        oauth_host = host_choice
        if st.button("Get Token"):
            try:
                token = Authenticator(api_key, secret_key, host=oauth_host).fetch_access_token()
                st.session_state.access_token = token
                st.success("Access token acquired.")
            except Exception as e:
                st.error(str(e))

    token_ok = bool(st.session_state.access_token)

    # ===== Devices =====
    st.subheader("Audio Devices")
    pa = pyaudio.PyAudio()
    dev = DeviceManager(pa)
    inputs, outputs = dev.list_devices()
    if not inputs or not outputs:
        st.error("No audio input/output devices found.")
        return

    in_names = [f"{name} (#{idx}, {sr} Hz)" for idx, name, sr in inputs]
    out_names = [f"{name} (#{idx}, {sr} Hz)" for idx, name, sr in outputs]

    ci = st.selectbox("Mic", in_names, index=0)
    co = st.selectbox("Speaker", out_names, index=0)

    in_idx = inputs[in_names.index(ci)][0]
    in_sr  = inputs[in_names.index(ci)][2]   # mic’s advertised default
    out_idx, out_sr = outputs[out_names.index(co)][0], outputs[out_names.index(co)][2]

    # Prefer a stable capture rate (16k). If the mic can't open at 16k, fall back to its advertised default.
    capture_rate = CAPTURE_RATE_DEFAULT
    try:
        # probe-open and immediately close to validate support
        _probe = dev.open_input(in_idx, capture_rate)
        _probe.stop_stream(); _probe.close()
    except Exception:
        capture_rate = in_sr

    sample_rate = capture_rate
    logger.info(f"Mic index={in_idx}, mic_default_sr={in_sr}, chosen_capture_rate={sample_rate}; "
            f"Speaker index={out_idx}, speaker_default_sr={out_sr}")

    # ===== Lottie (optional) =====
    with st.expander("Visualizer", expanded=False):
        render_lottie_mic_visualizer()

    # ===== Controls =====
    col1, col2 = st.columns(2)
    status = "Active" if st.session_state.chat_active else "Idle"
    st.info(f"Status: {status}")
    
    st.subheader("Session Events")
    events_placeholder = st.empty()
    drain_ui_queue_and_render(events_placeholder)

    # Build socket URL from chosen host
    ws_url = (
        f"wss://{host_choice}/v0/evi/chat"
        f"?access_token={st.session_state.access_token}"
        f"&verbose_transcription=true"
    )
    
    ws_url += f"&config_id={st.session_state.config_id}"
    
    safe_ws_url = ws_url
    if st.session_state.access_token:
        safe_ws_url = safe_ws_url.replace(st.session_state.access_token, "***")
    logger.info(f"Connecting WebSocket: {safe_ws_url}")


    # Start
    with col1:
        start_disabled = (
            not token_ok
            or st.session_state.chat_active
            or not bool(st.session_state.get("config_id"))
        )
        
        if st.button("Start Chat", disabled=start_disabled):
            # Validate inputs before touching devices
            if not st.session_state.config_id:
                st.error("EVI config_id is required. Add it in the sidebar.")
                return
            if not st.session_state.access_token:
                st.error("Access token missing. Click 'Get Token' in the sidebar.")
                return

            # Run preflight at the selected capture rate
            err = preflight_audio_open(dev, in_idx, out_idx, sample_rate)
            if err:
                st.session_state.last_error = err
                st.error(err)
                return

            try:
                st.session_state.ui_queue = queue.Queue()
                st.session_state.ui_events = []
                # Open mic stream (we already probed, but now open for real)
                input_stream = dev.open_input(in_idx, sample_rate)
                st.session_state.input_stream = input_stream

                # Create background loop if not exists
                if st.session_state.loop_thread is None:
                    st.session_state.loop_thread = AsyncLoopThread()

                # Stop signal and connection
                stop_event = threading.Event()
                st.session_state.stop_event = stop_event
                conn = Connection(pa)

                # Submit the coroutine to the background loop
                fut = st.session_state.loop_thread.submit(
                    conn.run(
                        ws_url,
                        input_stream,
                        out_idx,
                        sample_rate,
                        stop_event,
                        st.session_state.ui_queue,   # <-- new
                    )
                )
                st.session_state.stream_future = fut
                st.session_state.chat_active = True
                st.success("Streaming started.")
                logger.info("Streaming started.")
            except Exception as e:
                # Cleanup on failure
                st.session_state.last_error = str(e)
                logger.exception("Failed to start streaming")
                try:
                    if st.session_state.input_stream is not None:
                        st.session_state.input_stream.stop_stream()
                        st.session_state.input_stream.close()
                except Exception:
                    pass
                st.session_state.input_stream = None

                if st.session_state.loop_thread is not None:
                    try:
                        st.session_state.loop_thread.stop()
                    except Exception:
                        pass
                    st.session_state.loop_thread = None

                st.session_state.chat_active = False
                st.error(f"Failed to start: {e}")


    # Stop
    with col2:
        if st.button("Stop Chat", disabled=not st.session_state.chat_active):
            logger.info("Stop requested by user.")
            try:
                # signal the running tasks
                if st.session_state.stop_event:
                    st.session_state.stop_event.set()

                # attempt to cancel the running future (best effort)
                fut = st.session_state.stream_future
                if fut is not None:
                    try:
                        fut.cancel()
                    except Exception:
                        pass
                st.session_state.stream_future = None

                # close mic stream
                if st.session_state.input_stream is not None:
                    try:
                        st.session_state.input_stream.stop_stream()
                        st.session_state.input_stream.close()
                    except Exception:
                        pass
                    st.session_state.input_stream = None

                # stop background asyncio loop
                if st.session_state.loop_thread is not None:
                    try:
                        st.session_state.loop_thread.stop()
                    except Exception:
                        pass
                    st.session_state.loop_thread = None

                st.session_state.chat_active = False
                st.session_state.ui_queue = None
                st.session_state.ui_events = []
                st.success("Stopped.")
            except Exception as e:
                st.session_state.last_error = str(e)
                logger.exception("Failed to stop cleanly")
                st.error(f"Failed to stop: {e}")
                
    with st.expander("Diagnostics", expanded=False):
        if st.button("Play test tone"):
            try:
                play_test_tone(pa, out_idx, rate=sample_rate)
                st.success("Played test tone on selected speaker.")
            except Exception as e:
                st.error(f"Tone failed: {e}")

        tts_text = st.text_input("TTS probe text", "Hello there, this is a voice test.")
        if st.button("Run TTS probe"):
            if not st.session_state.access_token or not st.session_state.config_id:
                st.error("Need access token and config_id.")
            else:
                try:
                    # Ensure a queue exists to show probe events
                    if not st.session_state.ui_queue:
                        st.session_state.ui_queue = queue.Queue()
                    # Ensure background loop exists
                    if st.session_state.loop_thread is None:
                        st.session_state.loop_thread = AsyncLoopThread()
                    conn = Connection(pa)
                    st.session_state.loop_thread.submit(
                        conn.tts_probe(
                            ws_url, out_idx, sample_rate, tts_text, threading.Event(), st.session_state.ui_queue
                        )
                    )
                    st.info("TTS probe started; watch Session Events for results.")
                except Exception as e:
                    st.error(f"TTS probe failed to launch: {e}")

    # Footer
    st.caption("Built with Streamlit + websockets + PyAudio. Clean architecture, background asyncio loop.")
    if st.session_state.debug_logs and st.session_state.last_error:
        st.warning(f"Last error: {st.session_state.last_error}")


if __name__ == "__main__":
    main()
