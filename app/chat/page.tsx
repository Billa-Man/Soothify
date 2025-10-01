'use client';
import { useEffect, useRef, useState } from 'react';
import lottie from 'lottie-web';

type Message = { role: 'user' | 'assistant'; content: string };

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const lottieContainerRef = useRef<HTMLDivElement | null>(null);
  const lottieAnimRef = useRef<ReturnType<typeof lottie.loadAnimation> | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch('/media/siri_wave.json');
        const data = await resp.json();
        if (cancelled) return;
        if (lottieContainerRef.current) {
          lottieAnimRef.current = lottie.loadAnimation({
            container: lottieContainerRef.current,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            animationData: data,
          });
          lottieAnimRef.current.setSpeed(0.8);
        }
      } catch {}
    })();
    return () => {
      cancelled = true;
      try { lottieAnimRef.current?.destroy(); } catch {}
    };
  }, []);

  const send = async () => {
    if (!input) return;
    const next: Message[] = [...messages, { role: 'user' as const, content: input }];
    setMessages(next);
    setInput('');

    const res = await fetch('/api/chat', { method: 'POST', body: JSON.stringify({ messages: next }) });
    const reader = res.body?.getReader();
    if (!reader) return;
    let assistant = '';
    setMessages((prev) => [...prev, { role: 'assistant' as const, content: '' }]);
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      assistant += new TextDecoder().decode(value);
      setMessages((prev) => {
        const copy = [...prev];
        copy[copy.length - 1] = { role: 'assistant' as const, content: assistant };
        return copy;
      });
    }

    // TTS playback with Lottie visualizer
    if (assistant) {
      try {
        const resp = await fetch('/api/audio/tts', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ text: assistant }) });
        const buf = await resp.arrayBuffer();
        const AudioCtx = window.AudioContext || (window as typeof window & {webkitAudioContext: typeof AudioContext}).webkitAudioContext;
        const audioCtx = new AudioCtx();
        if (audioCtx.state === 'suspended') await audioCtx.resume();
        const audioBuf = await audioCtx.decodeAudioData(buf.slice(0));
        const source = audioCtx.createBufferSource();
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        source.buffer = audioBuf;
        source.connect(analyser);
        analyser.connect(audioCtx.destination);
        source.start(0);
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          analyser.getByteFrequencyData(dataArray);
          const avg = dataArray.reduce((a,b)=>a+b,0) / dataArray.length / 255; // 0..1
          const anim = lottieAnimRef.current;
          if (anim) {
            anim.setSpeed(0.6 + avg * 2.0);
            if (lottieContainerRef.current) {
              const scale = 1 + Math.min(0.35, avg * 0.8);
              lottieContainerRef.current.style.transform = `scale(${scale})`;
            }
          }
          if (audioCtx.state !== 'closed') requestAnimationFrame(tick);
        };
        tick();
      } catch {}
    }
  };

  return (
    <main className="mx-auto max-w-2xl space-y-4">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">AI Chat</h1>
        <p className="muted">Type or speak — we’ll respond in real time.</p>
      </div>
      <div className="card p-4 space-y-3">
        <div className="flex justify-center">
          <div ref={lottieContainerRef} style={{ width: 200, height: 200 }} />
        </div>
        {messages.map((m, i) => (
          <div key={i} className={m.role==='user' ? 'text-right' : 'text-left'}>
            <div className={`inline-block rounded px-3 py-2 ${m.role==='user' ? 'bg-indigo-600 text-white' : 'bg-slate-100'}`}>{m.content}</div>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input className="input flex-1" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Share your thoughts..." />
        <button className="btn btn-primary" onClick={send}>Send</button>
        <button
          className={`btn ${recording ? 'btn-primary' : 'btn-outline'}`}
          onClick={async () => {
            if (!recording) {
              const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
              const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
              mediaRecorderRef.current = mr;
              chunksRef.current = [];
              mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
              mr.onstop = async () => {
                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                const file = new File([blob], 'audio.webm', { type: 'audio/webm' });
                const fd = new FormData();
                fd.append('file', file);
                const tr = await fetch('/api/audio/stt', { method: 'POST', body: fd });
                const text = await tr.text();
                if (text) {
                  setInput(text);
                }
              };
              mr.start();
              setRecording(true);
            } else {
              mediaRecorderRef.current?.stop();
              setRecording(false);
            }
          }}
        >{recording ? 'Stop' : 'Record'}</button>
      </div>
    </main>
  );
}
