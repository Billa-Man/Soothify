import { useState, useRef, useCallback } from 'react';

export interface AudioRecordingState {
  isRecording: boolean;
  error: string | null;
  duration: number;
}

export interface AudioRecordingControls {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  reset: () => void;
}

export function useAudioRecording(): AudioRecordingState & AudioRecordingControls & {
  audioBlob: Blob | null;
  getAudioFile: () => File | null;
} {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setAudioBlob(null);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        }
      });

      streamRef.current = stream;
      chunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
      };

      mediaRecorder.onerror = (event) => {
        setError('Recording failed. Please check your microphone permissions.');
        console.error('MediaRecorder error:', event);
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);

      // Start duration timer
      setDuration(0);
      durationIntervalRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (err) {
      setError('Failed to start recording. Please check your microphone permissions.');
      console.error('Error starting recording:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
      durationIntervalRef.current = null;
    }

    setIsRecording(false);
  }, []);

  const reset = useCallback(() => {
    stopRecording();
    setError(null);
    setDuration(0);
    setAudioBlob(null);
    chunksRef.current = [];
  }, [stopRecording]);

  const getAudioFile = useCallback((): File | null => {
    if (!audioBlob) return null;

    return new File([audioBlob], `recording-${Date.now()}.webm`, {
      type: 'audio/webm'
    });
  }, [audioBlob]);

  return {
    isRecording,
    error,
    duration,
    audioBlob,
    startRecording,
    stopRecording,
    reset,
    getAudioFile,
  };
}
