'use client';

import { useChat } from '@/lib/hooks/useChat';
import { useAudioRecording } from '@/lib/hooks/useAudioRecording';
import { useTTS } from '@/lib/hooks/useTTS';
import { AudioVisualizer } from '@/lib/components/AudioVisualizer';
import { ChatMessage } from '@/lib/components/ChatMessage';
import { ChatInput } from '@/lib/components/ChatInput';
import { useEffect, useRef, useCallback } from 'react';

export default function Chat() {
  const { messages, isLoading, error, sendMessage, clearMessages } = useChat();
  const { isRecording, error: recordingError, duration, startRecording, stopRecording, getAudioFile } = useAudioRecording();
  const { analyser, speak } = useTTS();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const transcribeAudio = useCallback(async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/audio/stt', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }

      const transcribedText = await response.text();
      if (transcribedText.trim()) {
        await sendMessage(transcribedText.trim());
      }
    } catch (error) {
      console.error('Transcription error:', error);
    }
  }, [sendMessage]);

  // Auto-play TTS for assistant messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === 'assistant' && lastMessage.content && !isLoading) {
      speak(lastMessage.content).catch(console.error);
    }
  }, [messages, isLoading, speak]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  const handleVoiceRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  // Handle completed voice recording
  useEffect(() => {
    if (!isRecording && getAudioFile()) {
      const file = getAudioFile();
      if (file) {
        // Transcribe the recorded audio
        transcribeAudio(file);
      }
    }
  }, [isRecording, getAudioFile, transcribeAudio]);

  const getDisplayError = () => {
    return error || recordingError;
  };

  return (
    <main className="mx-auto max-w-4xl space-y-6">
      <div className="text-center">
        <h1 className="text-3xl font-semibold mb-2">AI Chat</h1>
        <p className="text-muted">Type or speak — we&apos;ll respond in real time.</p>
      </div>

      <div className="card p-6 space-y-4">
        <div className="flex justify-center mb-4">
          <AudioVisualizer
            analyser={analyser}
            width={200}
            height={200}
          />
        </div>

        {getDisplayError() && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
            <p className="text-red-600 dark:text-red-400 text-sm">
              {getDisplayError()}
            </p>
          </div>
        )}

        <div className="space-y-4 max-h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center text-muted py-8">
              Start a conversation by typing a message or recording your voice.
            </div>
          ) : (
            messages.map((message, index) => (
              <ChatMessage
                key={index}
                message={message}
                isLast={index === messages.length - 1 && isLoading}
              />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="flex gap-3">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          placeholder="Share your thoughts..."
        />

        <button
          onClick={handleVoiceRecording}
          disabled={isLoading}
          className={`btn px-4 ${isRecording ? 'btn-primary' : 'btn-outline'}`}
          title={isRecording ? `Recording... (${Math.floor(duration / 60)}:${(duration % 60).toString().padStart(2, '0')})` : 'Start voice recording'}
        >
          {isRecording ? '⏹️' : '🎤'}
        </button>

        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            disabled={isLoading}
            className="btn btn-outline text-slate-500 hover:text-slate-700"
            title="Clear conversation"
          >
            🗑️
          </button>
        )}
      </div>
    </main>
  );
}
