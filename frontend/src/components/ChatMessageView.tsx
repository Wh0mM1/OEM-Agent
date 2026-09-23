import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, User, CheckCircle2, AlertCircle } from 'lucide-react';
import { ChatMessage, ToolChipData } from '../types';

interface MessageProps {
  message: ChatMessage;
}

export default function ChatMessageView({ message }: MessageProps) {
  const isUser = message.sender === 'user';

  return (
    <div
      className={`group flex w-full gap-4 px-4 py-6 transition ${
        isUser ? 'bg-[#0b1120]' : 'bg-[#0f172a]/60 border-y border-slate-800/40'
      }`}
    >
      <div className="mx-auto flex w-full max-w-4xl gap-4">
        {/* Avatar */}
        <div className="shrink-0 pt-0.5">
          {isUser ? (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
              <User className="h-4 w-4" />
            </div>
          ) : (
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-rose-600 to-rose-500 text-white font-bold text-xs shadow-md shadow-rose-600/20">
              M
            </div>
          )}
        </div>

        {/* Message Content */}
        <div className="flex-1 space-y-3 overflow-hidden text-sm leading-relaxed text-slate-200">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs text-slate-300">
              {isUser ? 'You' : 'Mahindra Advisor'}
            </span>
            <span className="text-[10px] text-slate-400">{message.timestamp}</span>
          </div>

          {/* Markdown Body */}
          <div className="prose-table prose-invert max-w-none text-slate-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.text}
            </ReactMarkdown>
          </div>

          {/* Tool Chips */}
          {message.tool_chips && message.tool_chips.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2">
              {message.tool_chips.map((chip: ToolChipData, idx: number) => {
                const isSuccess = chip.status === 'success';
                return (
                  <span
                    key={idx}
                    className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-mono font-medium border shadow-xs ${
                      isSuccess
                        ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                        : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                    }`}
                  >
                    {isSuccess ? (
                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                    ) : (
                      <AlertCircle className="h-3 w-3 text-rose-400" />
                    )}
                    <span>{chip.label}</span>
                  </span>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
