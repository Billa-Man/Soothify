import { useCallback, useRef } from 'react';

export interface TTSOptions {
  speed?: number;
  voice?: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
}

export interface TTSState {
  isPlaying: boolean;
  isLoading: boolean;
  error: string | null;
  analyser: AnalyserNode | null;
}

export interface TTSActions {
  speak: (text: string, options?: TTSOptions) => Promise<void>;
  stop: () => void;
}

export function useTTS(): TTSState & TTSActions {
  const currentAudioContextRef = useRef<AudioContext | null>(null);
  const currentSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const currentAnalyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const speak = useCallback(async (text: string, options: TTSOptions = {}): Promise<void> => {
    if (!text.trim()) {
      throw new Error('Text cannot be empty');
    }

    if (text.length > 4000) {
      throw new Error('Text exceeds maximum length of 4000 characters');
    }

    try {
      const response = await fetch('/api/audio/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text.trim(),
          ...options,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const audioBuffer = await response.arrayBuffer();

      // Create audio context if it doesn't exist
      if (!currentAudioContextRef.current) {
        currentAudioContextRef.current = new (window.AudioContext || (window as typeof window & {webkitAudioContext: typeof AudioContext}).webkitAudioContext)();
      }

      // Resume context if suspended (required by some browsers)
      if (currentAudioContextRef.current.state === 'suspended') {
        await currentAudioContextRef.current.resume();
      }

      // Stop any currently playing audio
      if (currentSourceRef.current) {
        currentSourceRef.current.stop();
        currentSourceRef.current.disconnect();
      }

      // Decode and play the audio
      const buffer = await currentAudioContextRef.current.decodeAudioData(audioBuffer.slice(0));

      const source = currentAudioContextRef.current.createBufferSource();
      const analyser = currentAudioContextRef.current.createAnalyser();

      analyser.fftSize = 256;
      source.buffer = buffer;
      source.connect(analyser);
      analyser.connect(currentAudioContextRef.current.destination);

      currentSourceRef.current = source;
      currentAnalyserRef.current = analyser;

      source.start(0);

      return new Promise((resolve, reject) => {
        if (!source) {
          resolve();
          return;
        }

        source.onended = () => {
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
          }
          currentSourceRef.current = null;
          currentAnalyserRef.current = null;
          resolve();
        };

        // AudioBufferSourceNode doesn't have onerror, but we can catch decode errors
        try {
          source.start(0);
        } catch (startError) {
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
          }
          currentSourceRef.current = null;
          currentAnalyserRef.current = null;
          reject(startError);
        }
      });

    } catch (error) {
      throw new Error(
        error instanceof Error
          ? `TTS Error: ${error.message}`
          : 'Failed to convert text to speech'
      );
    }
  }, []);

  const stop = useCallback(() => {
    if (currentSourceRef.current) {
      currentSourceRef.current.stop();
      currentSourceRef.current.disconnect();
      currentSourceRef.current = null;
    }

    if (currentAnalyserRef.current) {
      currentAnalyserRef.current.disconnect();
      currentAnalyserRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // Close audio context if no longer needed
    if (currentAudioContextRef.current && currentAudioContextRef.current.state !== 'closed') {
      currentAudioContextRef.current.close();
      currentAudioContextRef.current = null;
    }
  }, []);

  return {
    isPlaying: currentSourceRef.current !== null,
    isLoading: false, // We don't track loading state since it's handled by the API call
    error: null,
    analyser: currentAnalyserRef.current,
    speak,
    stop,
  };
}
