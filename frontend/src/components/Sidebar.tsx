import React from 'react';
import { Plus, MessageSquare, Trash2, Database, ChevronLeft, ChevronRight, Layers } from 'lucide-react';
import { ChatThread } from '../types';

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string;
  onSelectThread: (id: string) => void;
  onNewThread: () => void;
  onDeleteThread: (id: string, e: React.MouseEvent) => void;
  onOpenCrm: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export default function Sidebar({
  threads,
  activeThreadId,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  onOpenCrm,
  isCollapsed,
  onToggleCollapse,
}: SidebarProps) {
  return (
    <aside
      className={`relative flex flex-col h-full bg-[#070b14] border-r border-slate-800/80 transition-all duration-300 ease-in-out z-20 ${
        isCollapsed ? 'w-16' : 'w-72'
      }`}
    >
      {/* Brand & New Chat */}
      <div className="p-3.5 border-b border-slate-800/80 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-rose-600 to-rose-500 font-extrabold text-white text-sm shadow-md shadow-rose-600/20">
                M
              </div>
              <div className="flex flex-col">
                <span className="font-semibold text-sm tracking-tight text-white">Mahindra AI</span>
                <span className="text-[10px] text-slate-400">Conversational Concierge</span>
              </div>
            </div>
          )}
          {isCollapsed && (
            <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-rose-600 font-extrabold text-white text-sm">
              M
            </div>
          )}
          <button
            onClick={onToggleCollapse}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition"
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <button
          onClick={onNewThread}
          className={`flex items-center justify-center gap-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700/60 py-2.5 transition font-medium text-xs shadow-sm hover:border-slate-600 ${
            isCollapsed ? 'px-0 w-full' : 'px-4'
          }`}
        >
          <Plus className="h-4 w-4 text-rose-400" />
          {!isCollapsed && <span>New Conversation</span>}
        </button>
      </div>

      {/* Threads List */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {!isCollapsed && (
          <div className="px-3 pb-1.5 text-[11px] font-medium tracking-wider uppercase text-slate-400">
            Recent Conversations
          </div>
        )}
        {threads.map((thread) => {
          const isActive = thread.id === activeThreadId;
          return (
            <div
              key={thread.id}
              onClick={() => onSelectThread(thread.id)}
              className={`group flex items-center justify-between rounded-lg px-3 py-2 cursor-pointer text-xs transition border ${
                isActive
                  ? 'bg-slate-800/90 text-white border-slate-700 shadow-sm'
                  : 'text-slate-400 hover:bg-slate-900/80 hover:text-slate-200 border-transparent'
              } ${isCollapsed ? 'justify-center px-0' : ''}`}
              title={thread.title}
            >
              <div className="flex items-center gap-2.5 truncate">
                <MessageSquare className={`h-3.5 w-3.5 shrink-0 ${isActive ? 'text-rose-400' : 'text-slate-400'}`} />
                {!isCollapsed && <span className="truncate">{thread.title}</span>}
              </div>

              {!isCollapsed && threads.length > 1 && (
                <button
                  onClick={(e) => onDeleteThread(thread.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition"
                  title="Delete chat thread"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer / Zoho CRM Drawer Link */}
      <div className="p-3 border-t border-slate-800/80 bg-[#060910]">
        <button
          onClick={onOpenCrm}
          className={`flex items-center gap-2.5 w-full rounded-xl border border-slate-800 hover:border-slate-700 bg-slate-900/60 hover:bg-slate-800/80 p-2.5 text-xs text-slate-300 transition ${
            isCollapsed ? 'justify-center' : ''
          }`}
          title="Open Zoho CRM Live Database Inspector"
        >
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-blue-500/10 text-blue-400">
            <Database className="h-3.5 w-3.5" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col text-left">
              <span className="font-semibold text-slate-200">Zoho CRM Sync</span>
              <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span> Live REST v8
              </span>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
}
