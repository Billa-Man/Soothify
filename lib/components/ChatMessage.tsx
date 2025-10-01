'use client';

import { ChatMessage as ChatMessageType } from '@/lib/hooks/useChat';

interface ChatMessageProps {
  message: ChatMessageType;
  isLast?: boolean;
}

export function ChatMessage({ message, isLast = false }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`
          inline-block max-w-[80%] px-4 py-3 rounded-lg
          ${isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
          }
          ${isLast && !isUser ? 'animate-pulse' : ''}
        `}
      >
        <div className="whitespace-pre-wrap break-words">
          {message.content || (isLast && !isUser ? '...' : '')}
        </div>
      </div>
    </div>
  );
}
