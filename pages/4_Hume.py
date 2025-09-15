# 4_Hume.py — clean, full version

import os
import io
import json
import base64
import wave
import atexit
import asyncio
import logging
import threading
import contextlib
from typing import Any, Coroutine, Optional, TypeVar
from concurrent.futures import Future

import streamlit as st
from dotenv import load_dotenv
import pyaudio
import websockets

# =========================
# Config & constants
# =========================
load_dotenv()

FORMAT = pyaudio.paInt16
CHANNELS = 1
CHUNK_SIZE = 1024

WS_HOST = os.getenv("HUME_WS_HOST", "api.hume.ai")     # default prod WS host
OAUTH_HOST = os.getenv("HUME_OAUTH_HOST", WS_HOST)     # keep OAuth & WS aligned
DEFAULT_SR = int(os.getenv("HUME_SAMPLE_RATE", "16000"))
DEFAULT_CONFIG_ID = os.getenv("HUME_CONFIG_ID", "").strip()  # optional: model/voice config id

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
            resp = requests.post(
                f"https://{self.host}/oauth2-cc/token",
                headers=headers,
                data=data,
                timeout=15,
            )
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

# =========================
# Async loop in a background thread
# =========================
T = TypeVar("T")

class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self._stopping = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
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
            try:
                current = asyncio.current_task()
                for task in asyncio.all_tasks():
                    if task is not current:
                        task.cancel()
            except Exception:
                pass
            self.loop.stop()

        with contextlib.suppress(RuntimeError):
            self.loop.call_soon_threadsafe(_cancel_all)

        self.thread.join(timeout=2)
        with contextlib.suppress(Exception):
            self.loop.close()

    def _atexit_cleanup(self):
        with contextlib.suppress(Exception):
            self.stop()

# =========================
# Connection: WS + audio streaming
# =========================
class Connection:
    def __init__(self):
        # Output stream is created lazily when we know WAV params
        self.pa = pyaudio.PyAudio()

    async def run(
        self,
        socket_url: str,
        input_stream,
        output_index: int,
        sample_rate: int,
        stop_event: threading.Event,
    ):
        backoff = 1
        while not stop_event.is_set():
            try:
                async with websockets.connect(
                    socket_url, ping_interval=20, ping_timeout=20, max_size=None
                ) as ws:
                    # Send session settings once (PCM in)
                    session_settings = {
                        "type": "session_settings",
                        "audio": {
                            "encoding": "linear16",           # PCM16 LE
                            "sample_rate": int(sample_rate),
                            "channels": int(CHANNELS),
                        },
                        # optional system prompt
                        "prompt": "Your goal is to provide soothing support to them.",
                    }
                    await ws.send(json.dumps(session_settings))
                    logger.info("WebSocket connected.")

                    send_task = asyncio.create_task(
                        self._send_audio(ws, input_stream, sample_rate, stop_event)
                    )
                    recv_task = asyncio.create_task(
                        self._recv_audio(ws, output_index, sample_rate, stop_event)
                    )
                    stop_waiter = asyncio.create_task(asyncio.to_thread(stop_event.wait))

                    done, pending = await asyncio.wait(
                        {send_task, recv_task, stop_waiter},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # If user hit Stop, close WS to unblock recv loop
                    if stop_waiter in done:
                        logger.info("Stop requested by user.")
                        with contextlib.suppress(Exception):
                            await ws.close(code=1000, reason="client stop")

                    # Bubble errors (if any)
                    for t in (send_task, recv_task):
                        if t in done:
                            exc = t.exception()
                            if exc:
                                raise exc

                    # Cancel leftovers
                    for t in (send_task, recv_task, stop_waiter):
                        if not t.done():
                            t.cancel()
                            with contextlib.suppress(asyncio.CancelledError):
                                await t

            except asyncio.CancelledError:
                break
            except websockets.ConnectionClosedOK:
                if stop_event.is_set():
                    break
                await asyncio.sleep(1)
                continue
            except Exception as e:
                if stop_event.is_set():
                    break
                logger.warning(f"WebSocket error: {e}; reconnecting in {backoff}s")
                await asyncio.sleep(backoff)
                backoff = min(15, backoff * 2)
            else:
                backoff = 1

            if stop_event.is_set():
                break

    async def _send_audio(
        self, ws, input_stream, _sample_rate: int, stop_event: threading.Event
    ):
        total = 0
        while not stop_event.is_set():
            try:
                data = await asyncio.to_thread(
                    input_stream.read, CHUNK_SIZE, exception_on_overflow=False
                )
                if not data:
                    await asyncio.sleep(0)
                    continue

                await ws.send(
                    json.dumps(
                        {
                            "type": "audio_input",
                            "data": base64.b64encode(data).decode("ascii"),
                        }
                    )
                )
                total += len(data)
                if (total // 2048) % 2 == 0:  # occasional debug
                    logger.debug(f"mic->ws sent ~{len(data)//CHUNK_SIZE} chunks; total_bytes={total}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"_send_audio error: {e}")
                raise

    async def _recv_audio(
        self, ws, output_index: int, sample_rate: int, stop_event: threading.Event
    ):
        out_stream: Optional[pyaudio.Stream] = None
        cur_rate: Optional[int] = None
        cur_channels: Optional[int] = None
        cur_format: Optional[int] = None  # pyaudio format const

        def _open_out(rate: int, channels: int, sampwidth: int):
            fmt_map = {1: pyaudio.paInt8, 2: pyaudio.paInt16, 3: pyaudio.paInt24, 4: pyaudio.paInt32}
            fmt = fmt_map.get(sampwidth, FORMAT)
            stream = self.pa.open(
                format=fmt,
                channels=channels,
                rate=rate,
                output=True,
                output_device_index=output_index,
                frames_per_buffer=CHUNK_SIZE,
            )
            return stream, rate, channels, fmt

        try:
            async for message in ws:
                if stop_event.is_set():
                    break

                # Binary frames (rare): treat as raw PCM with current/default params
                if isinstance(message, (bytes, bytearray)):
                    if out_stream is None:
                        out_stream, cur_rate, cur_channels, cur_format = _open_out(sample_rate, CHANNELS, 2)
                    with contextlib.suppress(Exception):
                        out_stream.write(message)
                    continue

                # Text frames → JSON
                try:
                    msg = json.loads(message)
                except Exception:
                    continue

                mtype = msg.get("type")
                if mtype == "audio_output":
                    b64 = msg.get("data")
                    if not b64:
                        continue
                    wav_bytes = base64.b64decode(b64)

                    # Parse WAV blob (server output)
                    try:
                        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
                            wav_rate = wf.getframerate()
                            wav_channels = wf.getnchannels()
                            wav_width = wf.getsampwidth()
                            pcm = wf.readframes(wf.getnframes())
                    except Exception as e:
                        logger.debug(f"failed to parse WAV from audio_output: {e}")
                        continue

                    # (Re)open output stream if params changed
                    need_new = (
                        out_stream is None
                        or cur_rate != wav_rate
                        or cur_channels != wav_channels
                    )
                    if need_new:
                        if out_stream:
                            with contextlib.suppress(Exception):
                                out_stream.stop_stream()
                                out_stream.close()
                        try:
                            out_stream, cur_rate, cur_channels, cur_format = _open_out(
                                wav_rate, wav_channels, wav_width
                            )
                        except Exception as e:
                            logger.error(f"Failed to open output device #{output_index} @ {wav_rate} Hz: {e}")
                            continue

                    with contextlib.suppress(Exception):
                        out_stream.write(pcm)

                elif mtype == "chat_metadata":
                    logger.debug(f"ws<- msg type=chat_metadata keys={list(msg.keys())}")
                elif mtype == "error":
                    logger.error(f"Server error: {msg}")
                else:
                    logger.debug(f"unhandled msg: {msg.get('type')}")
        finally:
            if out_stream:
                with contextlib.suppress(Exception):
                    out_stream.stop_stream()
                    out_stream.close()

# =========================
# Streamlit UI
# =========================
def ensure_state_defaults():
    st.session_state.setdefault("access_token", "")
    st.session_state.setdefault("token_ok", False)
    st.session_state.setdefault("devices_ok", False)
    st.session_state.setdefault("chat_active", False)
    st.session_state.setdefault("loop_thread", None)
    st.session_state.setdefault("stream_future", None)
    st.session_state.setdefault("stop_event", None)
    st.session_state.setdefault("input_stream", None)
    st.session_state.setdefault("device_in_idx", None)
    st.session_state.setdefault("device_out_idx", None)
    st.session_state.setdefault("selected_sample_rate", DEFAULT_SR)
    st.session_state.setdefault("config_id", DEFAULT_CONFIG_ID)

def render_lottie_mic_visualizer(lottie_json_path: str = "media/hume.json", height: int = 260):
    import json, os
    import streamlit as st
    import streamlit.components.v1 as components

    if not os.path.exists(lottie_json_path):
        st.info("Lottie file not found; skipping animation.")
        return

    try:
        with open(lottie_json_path, "r", encoding="utf-8") as f:
            lottie_js_data = json.dumps(json.load(f))
    except Exception:
        st.info("Invalid Lottie JSON; skipping animation.")
        return

    html = f"""
    <style>
      #viz-wrap {{ width:100%; height:{height}px; display:flex; align-items:center; justify-content:center; }}
      #lottie {{ width:100%; height:100%; transform-origin:center center; }}
      .note {{ font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; font-size:13px; color:#6b7280; text-align:center; margin-top:8px; }}
    </style>
    <div id="viz-wrap"><div id="lottie"></div></div>
    <div class="note">Allow microphone access to see the animation react in real&nbsp;time.</div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.10.2/lottie.min.js"></script>
    <script>
      (async () => {{
        const animationData = {lottie_js_data};
        const container = document.getElementById('lottie');
        const anim = lottie.loadAnimation({{
          container, renderer:'svg', loop:true, autoplay:true, animationData
        }});

        function rms(buf) {{
          let sum = 0;
          for (let i=0; i<buf.length; i++) {{ const v = (buf[i]-128)/128; sum += v*v; }}
          return Math.sqrt(sum / buf.length);
        }}

        try {{
          const stream = await navigator.mediaDevices.getUserMedia({{ audio: {{ echoCancellation:true, noiseSuppression:true }} }});
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
            const speed = 0.5 + Math.min(2.0, level * 3.0);
            anim.setSpeed(speed);
            const scale = 1 + Math.min(0.35, level * 0.8);
            container.style.transform = `scale(${{scale}})`;
            requestAnimationFrame(tick);
          }}
          tick();

          document.addEventListener('click', () => {{ if (ctx.state === 'suspended') ctx.resume(); }});
        }} catch (err) {{
          let t = 0;
          function idle() {{ t += 0.02; const scale = 1 + 0.05 * Math.sin(t); container.style.transform = `scale(${{scale}})`; requestAnimationFrame(idle); }}
          idle();
        }}
      }})();
    </script>
    """
    components.html(html, height=height + 60)

def main():
    st.set_page_config(page_title="Hume Voice Chat (clean)", page_icon="🎧", layout="centered")
    ensure_state_defaults()

    st.title("Hume Voice Chat — clean rewrite")

    # ---- Setup (form): keys + devices + (optional) config_id ----
    st.subheader("Setup")
    pa = pyaudio.PyAudio()
    dev = DeviceManager(pa)
    inputs, outputs = dev.list_devices()
    if not inputs or not outputs:
        st.error("No audio input/output devices found.")
        st.stop()

    in_names = [f"{name} (#{idx}, {sr} Hz)" for idx, name, sr in inputs]
    out_names = [f"{name} (#{idx}, {sr} Hz)" for idx, name, sr in outputs]

    with st.form("hume_setup"):
        c1, c2 = st.columns(2)
        with c1:
            api_key = st.text_input("HUME_API_KEY", os.getenv("HUME_API_KEY", ""), type="password",
                                    disabled=st.session_state.chat_active)
        with c2:
            secret_key = st.text_input("HUME_SECRET_KEY", os.getenv("HUME_SECRET_KEY", ""), type="password",
                                       disabled=st.session_state.chat_active)

        host_choice = st.selectbox("API Host", [WS_HOST, "test-api.hume.ai"],
                                   index=0, disabled=st.session_state.chat_active)

        c3, c4 = st.columns(2)
        with c3:
            ci = st.selectbox("Microphone", in_names, index=0, disabled=st.session_state.chat_active)
        with c4:
            co = st.selectbox("Speaker", out_names, index=0, disabled=st.session_state.chat_active)

        sr_options = sorted({16000, 24000, 32000, 44100, 48000})
        chosen_sr = st.selectbox(
            "Capture sample rate",
            sr_options,
            index=sr_options.index(16000) if 16000 in sr_options else 0,
            help="Use 16000 Hz for best compatibility.",
            disabled=st.session_state.chat_active,
        )

        config_id = st.text_input(
            "Optional: config_id",
            st.session_state.config_id,
            help="If you have an EVI config ID, paste it here.",
            disabled=st.session_state.chat_active,
        )

        submitted = st.form_submit_button("Save setup", disabled=st.session_state.chat_active)
        if submitted:
            if not api_key or not secret_key:
                st.error("Please enter both HUME_API_KEY and HUME_SECRET_KEY.")
            else:
                try:
                    token = Authenticator(api_key, secret_key, host=host_choice).fetch_access_token()
                    st.session_state.access_token = token
                    st.session_state.token_ok = True

                    in_idx = inputs[in_names.index(ci)][0]
                    out_idx = outputs[out_names.index(co)][0]
                    st.session_state.device_in_idx = in_idx
                    st.session_state.device_out_idx = out_idx
                    st.session_state.selected_sample_rate = int(chosen_sr)
                    st.session_state.config_id = config_id.strip()
                    st.session_state.devices_ok = True

                    # helpful log line (matches your earlier style)
                    mic_default_sr = next((sr for idx, _, sr in inputs if idx == in_idx), None)
                    spk_default_sr = next((sr for idx, _, sr in outputs if idx == out_idx), None)
                    logger.info(
                        f"Mic index={in_idx}, mic_default_sr={mic_default_sr}, chosen_capture_rate={chosen_sr}; "
                        f"Speaker index={out_idx}, speaker_default_sr={spk_default_sr}"
                    )
                    st.success("Setup saved. You can start the chat now.")
                except Exception as e:
                    st.session_state.token_ok = False
                    st.error(f"Authentication failed: {e}")

    # ---- Status ----

    def _is_running() -> bool:
        fut = st.session_state.get("stream_future")
        if fut is not None:
            try:
                if not fut.done():
                    return True
            except Exception:
                # if Future got invalidated, treat as not running
                pass
        ev = st.session_state.get("stop_event")
        if ev is not None and not ev.is_set():
            # we created a stop_event for an active session
            return True
        return False

    ready = st.session_state.token_ok and st.session_state.devices_ok

    # Derive real running state and keep the flag in sync
    running = _is_running()
    st.session_state.chat_active = running

    status = "Active" if running else ("Ready" if ready else "Incomplete setup")
    st.info(f"Status: {status}")

    start_disabled = (not ready) or running
    stop_disabled  = not running

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start Chat", disabled=start_disabled):
            if running:
                st.warning("A chat is already running.")
            else:
                try:
                    # Open mic with saved selection
                    input_stream = dev.open_input(
                        st.session_state.device_in_idx,
                        st.session_state.selected_sample_rate,
                    )
                    st.session_state.input_stream = input_stream

                    # Background loop
                    if st.session_state.loop_thread is None:
                        st.session_state.loop_thread = AsyncLoopThread()

                    # Build websocket URL only now (after verified token + devices)
                    qs = (
                        f"access_token={st.session_state.access_token}"
                        f"&verbose_transcription=true"
                    )
                    if st.session_state.config_id:
                        qs += f"&config_id={st.session_state.config_id}"
                    ws_url = f"wss://{host_choice}/v0/evi/chat?{qs}"

                    # Stop signal + connection
                    stop_event = threading.Event()
                    st.session_state.stop_event = stop_event
                    conn = Connection()

                    fut = st.session_state.loop_thread.submit(
                        conn.run(
                            ws_url,
                            input_stream,
                            st.session_state.device_out_idx,
                            st.session_state.selected_sample_rate,
                            stop_event,
                        )
                    )
                    st.session_state.stream_future = fut

                    # immediately reflect running state in UI
                    st.session_state.chat_active = True
                    st.success("Streaming started.")
                    # Force a rerun so the Stop button enables right away
                    (getattr(st, "rerun", st.rerun))()
                except Exception as e:
                    st.error(f"Failed to start: {e}")

    with col2:
        if st.button("Stop Chat", disabled=stop_disabled):
            try:
                # Signal background to stop
                if st.session_state.stop_event:
                    st.session_state.stop_event.set()

                # Close mic stream
                if st.session_state.input_stream is not None:
                    with contextlib.suppress(Exception):
                        st.session_state.input_stream.stop_stream()
                        st.session_state.input_stream.close()
                    st.session_state.input_stream = None

                # Clear future and (optionally) stop loop thread
                st.session_state.stream_future = None
                if st.session_state.loop_thread is not None:
                    with contextlib.suppress(Exception):
                        st.session_state.loop_thread.stop()
                    st.session_state.loop_thread = None

                st.session_state.chat_active = False
                st.success("Stopped.")
                # Force refresh so Start enables and Stop disables immediately
                (getattr(st, "rerun", st.rerun))()
            except Exception as e:
                st.error(f"Failed to stop: {e}")



    st.caption("Built with Streamlit + websockets + PyAudio. PCM in; WAV out. Clean stop & reconnect handling.")

if __name__ == "__main__":
    main()
