'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import lottie from 'lottie-web';
import { VoiceProvider, useVoice } from '@humeai/voice-react';

function Visualizer() {
  const { status } = useVoice();
  const lottieContainerRef = useRef<HTMLDivElement | null>(null);
  const lottieAnimRef = useRef<ReturnType<typeof lottie.loadAnimation> | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const obsRef = useRef<MutationObserver | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch('/media/hume.json');
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
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      try { audioCtxRef.current?.close(); } catch {}
      obsRef.current?.disconnect();
    };
  }, []);

  useEffect(() => {
    const attachToAudio = (el: HTMLAudioElement) => {
      try {
        const AudioCtx = (window.AudioContext || (window as any).webkitAudioContext);
        const ctx = audioCtxRef.current || new AudioCtx();
        audioCtxRef.current = ctx;
        const src = ctx.createMediaElementSource(el);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        src.connect(analyser);
        analyser.connect(ctx.destination);
        analyserRef.current = analyser;
        const data = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          analyser.getByteFrequencyData(data);
          const avg = data.reduce((a,b)=>a+b,0) / data.length / 255;
          const anim = lottieAnimRef.current;
          if (anim) {
            anim.setSpeed(0.6 + avg * 2.0);
            if (lottieContainerRef.current) {
              const scale = 1 + Math.min(0.35, avg * 0.8);
              lottieContainerRef.current.style.transform = `scale(${scale})`;
            }
          }
          rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
      } catch {}
    };

    // Try initial attach
    const initial = document.querySelector('audio') as HTMLAudioElement | null;
    if (initial) attachToAudio(initial);

    // Observe for audio elements added by the SDK
    const obs = new MutationObserver((muts) => {
      for (const m of muts) {
        m.addedNodes.forEach((n) => {
          if (n instanceof HTMLAudioElement) attachToAudio(n);
          if (n instanceof HTMLElement) {
            const a = n.querySelector('audio') as HTMLAudioElement | null;
            if (a) attachToAudio(a);
          }
        });
      }
    });
    obs.observe(document.body, { childList: true, subtree: true });
    obsRef.current = obs;

    return () => {
      obs.disconnect();
    };
  }, [status]);

  return (
    <div className="flex justify-center">
      <div ref={lottieContainerRef} style={{ width: 220, height: 220 }} />
    </div>
  );
}

function Inner({ accessToken, configId }: { accessToken: string; configId?: string }) {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { connect, disconnect, status } = useVoice();
  const isConnected = (() => {
    const s: any = status as any;
    const statusValue = typeof s === 'string' ? s : (s?.value || s?.state || s?.code);
    return statusValue === 'connected';
  })();
  const stopRequestedRef = useRef(false);
  const reconnectAttemptsRef = useRef(0);

  const onStart = useCallback(async () => {
    setError(null);
    setConnecting(true);
    try {
      console.log('[hume] connect start');
      stopRequestedRef.current = false;
      // Prime microphone permission to avoid silent permission denials
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        try { stream.getTracks().forEach(t => t.stop()); } catch {}
      } catch (e) {
        console.warn('[hume] mic permission not granted yet', e);
      }
      const opts: any = { 
        auth: { type: 'accessToken', value: accessToken },
        configId,
        // Configure retry options to prevent "Max retries (0) reached" error
        reconnectAttempts: 5,
        debug: true  // Enable debug mode to get more detailed error information
      } as any;
      await connect(opts);
      console.log('[hume] connect success');
    } catch (e: any) {
      console.error('[hume] connect error', e);
      setError(e?.message || 'Failed to connect');
    } finally {
      setConnecting(false);
    }
  }, [connect, accessToken, configId]);

  const onStop = useCallback(() => {
    console.log('[hume] stop requested by user');
    setError(null);
    setConnecting(false);
    stopRequestedRef.current = true;
    reconnectAttemptsRef.current = 0;
    try {
      disconnect();
      console.log('[hume] disconnect called successfully');
    } catch (e: any) {
      console.error('[hume] error during disconnect:', e);
      setError('Error stopping connection: ' + (e?.message || 'Unknown error'));
    }
  }, [disconnect]);

  // Log status transitions and attempt auto-reconnect on unexpected closes
  useEffect(() => {
    const sVal: any = status as any;
    const s = typeof sVal === 'string' ? sVal : (sVal?.state || sVal?.value || sVal?.code || JSON.stringify(sVal));
    console.log('[hume] status', typeof sVal === 'object' ? sVal : s);
    
    // More detailed error handling
    if (sVal && typeof sVal === 'object' && sVal.value === 'error') {
      const reason = sVal.reason || 'Unknown error';
      console.error('[hume] connection error:', reason);
      
      // Check for specific WebSocket connection issues
      if (reason.includes('Max retries') || reason.includes('websocket connection could not be established')) {
        console.warn('[hume] WebSocket connection failed. Please check your network connection and Hume AI service status.');
      }
      
      // Check for credit exhaustion and stop reconnecting
      if (reason.includes('credit balance') || reason.includes('Exhausted credit balance')) {
        console.error('[hume] ❌ Credit exhaustion detected. Stopping reconnection attempts.');
        console.error('[hume] 💳 Please visit https://platform.hume.ai/billing to add credits to your account.');
        stopRequestedRef.current = true; // Prevent further reconnection attempts
        setError('Credit balance exhausted. Please add credits to your Hume AI account.');
        return;
      }
    }
    
    const shouldReconnect = !stopRequestedRef.current && s !== 'connected' && s !== 'connecting' && s !== 'error';
    if (shouldReconnect) {
      const attempt = (reconnectAttemptsRef.current = Math.min(reconnectAttemptsRef.current + 1, 6));
      const delayMs = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
      console.log('[hume] scheduling reconnect attempt', attempt, 'in', delayMs, 'ms');
      const t = setTimeout(() => {
        console.log('[hume] attempting reconnect, attempt', attempt);
        onStart().catch((e) => {
          console.error('[hume] reconnect failed:', e);
        });
      }, delayMs);
      return () => clearTimeout(t);
    }
    if (s === 'connected') {
      reconnectAttemptsRef.current = 0;
      console.log('[hume] connection established successfully');
    }
  }, [status, onStart]);

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-4">
      <h1 className="text-2xl font-semibold text-center">Hume Voice Chat</h1>
      <Visualizer />
      <div className="flex gap-2 justify-center">
        <button 
          className={`px-4 py-2 rounded font-medium ${isConnected || connecting ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-500 text-white hover:bg-indigo-600 cursor-pointer'}`} 
          disabled={isConnected || connecting} 
          onClick={onStart}
        >
          Start Chat
        </button>
        <button 
          className={`px-4 py-2 rounded font-medium ${isConnected ? 'bg-red-500 text-white hover:bg-red-600 cursor-pointer' : 'bg-slate-400 cursor-not-allowed'}`} 
          disabled={!isConnected} 
          onClick={onStop}
        >
          Stop Chat
        </button>
      </div>
      <div className="text-center text-xs text-gray-600">
        <p>Connection Status: <span className="font-mono">{isConnected ? '🟢 Connected' : connecting ? '🟡 Connecting' : '🔴 Disconnected'}</span></p>
        <p>Stop Button: <span className="font-mono">{isConnected ? '✅ Enabled' : '❌ Disabled'}</span></p>
      </div>
      <p className="text-center text-sm muted">Status: {(() => { const s:any = status as any; return typeof s === 'string' ? s : (s?.value || s?.state || s?.code || 'unknown'); })()}{connecting ? ' (connecting...)' : ''}</p>
      {(() => { const s:any = status as any; const reason = s?.reason; return reason ? <p className="text-center text-xs" style={{ color: '#b91c1c' }}>{String(reason)}</p> : null; })()}
      <p className="text-center text-xs muted">Tip: allow microphone and speak within ~30s to keep the session alive.</p>
      {error && (
        <div className="text-center">
          <p className="text-red-600 text-sm">{error}</p>
          {error.includes('credit') && (
            <p className="text-xs text-blue-600 mt-2">
              <a href="https://platform.hume.ai/billing" target="_blank" rel="noopener noreferrer" className="underline">
                → Add credits to your Hume AI account
              </a>
            </p>
          )}
        </div>
      )}
      <Diagnostics />
    </main>
  );
}

function Diagnostics() {
  const [secure, setSecure] = useState<boolean | null>(null);
  const [micPerm, setMicPerm] = useState<string | null>(null);
  useEffect(() => {
    setSecure(typeof window !== 'undefined' ? window.isSecureContext : null);
    try {
      (navigator as any).permissions?.query({ name: 'microphone' as any }).then((res: any) => setMicPerm(res?.state || 'unknown')).catch(() => setMicPerm('unknown'));
    } catch {
      setMicPerm('unknown');
    }
  }, []);
  return (
    <div className="text-xs muted text-center">
      <div>Secure Context: {String(secure)}</div>
      <div>Mic Permission: {micPerm}</div>
    </div>
  );
}

export default function HumeClient({ accessToken, configId }: { accessToken: string; configId?: string }) {
  return (
    <VoiceProvider>
      <Inner accessToken={accessToken} configId={configId} />
    </VoiceProvider>
  );
}


