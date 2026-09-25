import React, { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Layers, ShieldCheck, Database, Menu, Key } from 'lucide-react';
import { ChatMessage, ChatThread, StageType } from './types';
import Sidebar from './components/Sidebar';
import ChatMessageView from './components/ChatMessageView';
import EmptyState from './components/EmptyState';
import CrmDrawer from './components/CrmDrawer';
import KeySettingsModal from './components/KeySettingsModal';

const STORAGE_KEY = 'mahindra_agent_threads_v1';
const API_KEY_STORAGE = 'mahindra_openrouter_key';
const MODEL_STORAGE = 'mahindra_openrouter_model';

export default function App() {
  const [threads, setThreads] = useState<ChatThread[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch (e) {
      console.error(e);
    }
    return [
      {
        id: `thread_${Date.now()}`,
        title: 'New Conversation',
        createdAt: Date.now(),
        lastStage: 'new_lead',
        messages: [],
      },
    ];
  });

  const [activeThreadId, setActiveThreadId] = useState<string>(() => threads[0]?.id || `thread_${Date.now()}`);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Custom User OpenRouter Key & Model (BYOK)
  const [userApiKey, setUserApiKey] = useState<string>(() => {
    return localStorage.getItem(API_KEY_STORAGE) || '';
  });
  const [userModel, setUserModel] = useState<string>(() => {
    return localStorage.getItem(MODEL_STORAGE) || 'nvidia/nemotron-3-ultra-550b-a55b:free';
  });

  const activeThread = threads.find((t) => t.id === activeThreadId) || threads[0];
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync threads to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
    } catch (e) {
      console.error(e);
    }
  }, [threads]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeThread?.messages, isLoading]);

  const handleSaveKey = (key: string, model: string) => {
    setUserApiKey(key);
    setUserModel(model);
    if (key) {
      localStorage.setItem(API_KEY_STORAGE, key);
    } else {
      localStorage.removeItem(API_KEY_STORAGE);
    }
    if (model) {
      localStorage.setItem(MODEL_STORAGE, model);
    } else {
      localStorage.removeItem(MODEL_STORAGE);
    }
  };

  const handleClearKey = () => {
    setUserApiKey('');
    localStorage.removeItem(API_KEY_STORAGE);
  };

  const handleNewThread = () => {
    const newId = `thread_${Date.now()}`;
    const newThread: ChatThread = {
      id: newId,
      title: 'New Conversation',
      createdAt: Date.now(),
      lastStage: 'new_lead',
      messages: [],
    };
    setThreads((prev) => [newThread, ...prev]);
    setActiveThreadId(newId);
  };

  const handleDeleteThread = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (threads.length <= 1) {
      handleNewThread();
      return;
    }
    const updated = threads.filter((t) => t.id !== id);
    setThreads(updated);
    if (activeThreadId === id) {
      setActiveThreadId(updated[0].id);
    }
  };

  const handleSend = async (customText?: string) => {
    const textToSend = (customText || input).trim();
    if (!textToSend || isLoading) return;

    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    // Update thread title if first message
    const isFirstMessage = activeThread.messages.length === 0;
    const computedTitle = isFirstMessage
      ? textToSend.length > 30
        ? `${textToSend.slice(0, 30)}...`
        : textToSend
      : activeThread.title;

    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThread.id
          ? {
              ...t,
              title: computedTitle,
              messages: [...t.messages, userMessage],
            }
          : t
      )
    );

    if (!customText) setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: textToSend,
          thread_id: activeThread.id,
          session_id: activeThread.id,
          openrouter_key: userApiKey || undefined,
          openrouter_model: userModel || undefined,
        }),
      });

      if (!res.body) return;

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = '';
      let detectedStage: StageType = 'new_lead';
      let currentToolChips: any[] = [];
      const agentMsgId = `agt-${Date.now()}`;

      // Insert empty placeholder message for progressive streaming
      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeThread.id
            ? {
                ...t,
                messages: [
                  ...t.messages,
                  {
                    id: agentMsgId,
                    sender: 'agent',
                    text: '',
                    stage: 'new_lead',
                    tool_chips: [],
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                  },
                ],
              }
            : t
        )
      );

      // Stream incoming Server-Sent Events
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const textChunk = decoder.decode(value);
        const lines = textChunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));

              if (event.type === 'meta') {
                detectedStage = event.stage || 'new_lead';
                currentToolChips = event.tool_chips || [];
                if (event.requires_custom_key) {
                  setIsKeyModalOpen(true);
                }
              } else if (event.type === 'chunk') {
                accumulatedText += event.text;

                setThreads((prev) =>
                  prev.map((t) =>
                    t.id === activeThread.id
                      ? {
                          ...t,
                          lastStage: detectedStage,
                          messages: t.messages.map((m) =>
                            m.id === agentMsgId
                              ? {
                                  ...m,
                                  text: accumulatedText,
                                  stage: detectedStage,
                                  tool_chips: currentToolChips,
                                }
                              : m
                          ),
                        }
                      : t
                  )
                );
              }
            } catch (e) {
              // Ignore partial chunk parsing
            }
          }
        }
      }
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: 'agent',
        text: "I encountered a momentary connection interruption. Please try again or rephrase.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setThreads((prev) =>
        prev.map((t) =>
          t.id === activeThread.id ? { ...t, messages: [...t.messages, errorMessage] } : t
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getStageLabel = (stage: StageType) => {
    switch (stage) {
      case 'new_lead':
        return { name: 'Stage 1: New Lead Discovery', color: 'text-blue-400 bg-blue-500/10 border-blue-500/30' };
      case 'ongoing_pipeline':
        return { name: 'Stage 2: Ongoing Pipeline', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' };
      case 'booked_vehicle':
        return { name: 'Stage 3: Booked Vehicle', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' };
      case 'post_purchase_service':
        return { name: 'Stage 4: Post-Purchase Service', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' };
      default:
        return { name: 'Clarification Needed', color: 'text-slate-400 bg-slate-500/10 border-slate-500/30' };
    }
  };

  const stageInfo = getStageLabel(activeThread?.lastStage || 'new_lead');

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0b1120] text-slate-100 antialiased font-sans">
      {/* Sidebar with Thread History */}
      <Sidebar
        threads={threads}
        activeThreadId={activeThread?.id}
        onSelectThread={(id) => setActiveThreadId(id)}
        onNewThread={handleNewThread}
        onDeleteThread={handleDeleteThread}
        onOpenCrm={() => setIsDrawerOpen(true)}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Chat View */}
      <div className="flex flex-1 flex-col h-full overflow-hidden bg-[#0b1120]">
        {/* Top Header */}
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-800/80 bg-[#080d18]/80 px-6 backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-white tracking-tight">
              {activeThread?.title}
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            {/* Active Stage Badge */}
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${stageInfo.color}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse"></span>
              <span>{stageInfo.name}</span>
            </div>

            {/* BYOK / API Key Trigger */}
            <button
              onClick={() => setIsKeyModalOpen(true)}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                userApiKey
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20'
                  : 'border-slate-800 bg-slate-900/80 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
              title={userApiKey ? 'Using Custom OpenRouter Key' : 'OpenRouter API Key (BYOK)'}
            >
              <Key className={`h-3.5 w-3.5 ${userApiKey ? 'text-emerald-400' : 'text-rose-400'}`} />
              <span>{userApiKey ? 'Custom Key Active' : 'API Key / Quota'}</span>
            </button>

            {/* CRM Drawer Trigger */}
            <button
              onClick={() => setIsDrawerOpen(true)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
            >
              <Database className="h-3.5 w-3.5 text-blue-400" />
              <span>CRM Drawer</span>
            </button>
          </div>
        </header>

        {/* Message Thread Scroll Area */}
        <main className="flex-1 overflow-y-auto">
          {activeThread?.messages.length === 0 ? (
            <EmptyState onSelectPrompt={(p) => handleSend(p)} />
          ) : (
            <div className="flex flex-col pb-4">
              {activeThread.messages.map((msg) => (
                <ChatMessageView key={msg.id} message={msg} />
              ))}
              {isLoading && (
                <div className="flex w-full gap-4 px-4 py-6 bg-[#0f172a]/60 border-y border-slate-800/40">
                  <div className="mx-auto flex w-full max-w-4xl gap-4 items-center text-xs text-slate-400">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-rose-600 to-rose-500 text-white font-bold text-xs shadow-md shadow-rose-600/20">
                      M
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-3.5 w-3.5 text-rose-400 animate-spin" />
                      <span>Checking vehicle database and synchronizing with Zoho CRM...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        {/* Bottom Input Box (Claude / ChatGPT Style) */}
        <footer className="shrink-0 p-4 border-t border-slate-800/80 bg-[#080d18]/90">
          <div className="mx-auto max-w-3xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="relative flex items-center rounded-2xl border border-slate-700/80 bg-[#111827] shadow-lg shadow-black/30 focus-within:border-slate-500 transition"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about XUV700 specs, Priya's test drive, track MAH-9921, or schedule a service..."
                className="w-full bg-transparent px-4 py-3.5 text-sm text-slate-100 placeholder-slate-500 outline-none pr-12"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2.5 flex h-8 w-8 items-center justify-center rounded-xl bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-30 disabled:hover:bg-rose-600 transition shadow-sm"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
            <div className="mt-2 text-center text-[11px] text-slate-400">
              Stateful multi-turn LangGraph orchestrator • Grounded in Mahindra catalog • Zero price hallucination
            </div>
          </div>
        </footer>
      </div>

      {/* Slide-out CRM Inspector Drawer */}
      <CrmDrawer isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />

      {/* OpenRouter API Key Settings Modal (BYOK) */}
      <KeySettingsModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        apiKey={userApiKey}
        model={userModel}
        onSave={handleSaveKey}
        onClear={handleClearKey}
      />
    </div>
  );
}
