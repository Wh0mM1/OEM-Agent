import React, { useState, useEffect } from 'react';
import { Key, X, Check, Trash2, Cpu, ExternalLink, Activity } from 'lucide-react';

interface KeySettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  apiKey: string;
  model: string;
  onSave: (key: string, model: string) => void;
  onClear: () => void;
}

const POPULAR_MODELS = [
  { id: 'nvidia/nemotron-3-ultra-550b-a55b:free', name: 'Nvidia Nemotron 3 Ultra (Free)' },
  { id: 'meta-llama/llama-3.3-70b-instruct', name: 'Meta Llama 3.3 70B Instruct' },
  { id: 'mistralai/mistral-small-24b-instruct-2501:free', name: 'Mistral Small 24B (Free)' },
  { id: 'google/gemini-2.0-flash-lite:free', name: 'Google Gemini 2.0 Flash Lite (Free)' },
  { id: 'deepseek/deepseek-chat', name: 'DeepSeek V3' },
];

export default function KeySettingsModal({
  isOpen,
  onClose,
  apiKey,
  model,
  onSave,
  onClear,
}: KeySettingsModalProps) {
  const [localKey, setLocalKey] = useState(apiKey);
  const [localModel, setLocalModel] = useState(model || 'nvidia/nemotron-3-ultra-550b-a55b:free');
  const [quotaStatus, setQuotaStatus] = useState<{ used_last_hour: number; max_per_hour: number; remaining: number } | null>(null);

  useEffect(() => {
    setLocalKey(apiKey);
    setLocalModel(model || 'nvidia/nemotron-3-ultra-550b-a55b:free');
  }, [apiKey, model, isOpen]);

  useEffect(() => {
    if (isOpen) {
      fetch('/api/rate-limit/status')
        .then((res) => res.json())
        .then((data) => setQuotaStatus(data))
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700/80 bg-[#0f172a] shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-[#080d18]">
          <div className="flex items-center gap-2.5 text-white font-semibold text-base">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/20 text-rose-400 border border-rose-500/30">
              <Key className="h-4 w-4" />
            </div>
            <span>OpenRouter Settings (BYOK)</span>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 text-sm">
          {/* Shared Quota Banner */}
          <div className="rounded-xl border border-slate-800 bg-[#162032] p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-blue-400" />
              <div>
                <div className="font-medium text-slate-200 text-xs">Shared Server Quota</div>
                <div className="text-slate-400 text-xs">
                  {quotaStatus ? `${quotaStatus.used_last_hour} / ${quotaStatus.max_per_hour} requests this hour` : '30 requests / hour limit'}
                </div>
              </div>
            </div>
            {quotaStatus && (
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                quotaStatus.remaining > 5
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                  : 'text-rose-400 bg-rose-500/10 border-rose-500/30'
              }`}>
                {quotaStatus.remaining} remaining
              </span>
            )}
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            The system provides a free shared quota of 30 requests/hour. To bypass this limit or use your own custom LLM, enter your personal OpenRouter API key. Your key is stored solely in your browser.
          </p>

          {/* API Key Input */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center justify-between">
              <span>OpenRouter API Key</span>
              <a
                href="https://openrouter.ai/keys"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] font-normal text-rose-400 hover:underline flex items-center gap-1"
              >
                Get Free Key <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </label>
            <input
              type="password"
              value={localKey}
              onChange={(e) => setLocalKey(e.target.value)}
              placeholder="sk-or-v1-..."
              className="w-full rounded-xl border border-slate-700 bg-[#080d18] px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:border-rose-500 outline-none transition"
            />
          </div>

          {/* Model Selection */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-slate-400" />
              <span>Preferred Model</span>
            </label>
            <select
              value={POPULAR_MODELS.some((m) => m.id === localModel) ? localModel : 'custom'}
              onChange={(e) => {
                if (e.target.value !== 'custom') setLocalModel(e.target.value);
              }}
              className="w-full rounded-xl border border-slate-700 bg-[#080d18] px-3 py-2 text-sm text-slate-100 focus:border-rose-500 outline-none transition"
            >
              {POPULAR_MODELS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
              <option value="custom">Custom Model ID...</option>
            </select>

            <input
              type="text"
              value={localModel}
              onChange={(e) => setLocalModel(e.target.value)}
              placeholder="e.g. meta-llama/llama-3.3-70b-instruct"
              className="w-full mt-2 rounded-xl border border-slate-800 bg-[#080d18] px-3.5 py-2 text-xs text-slate-300 placeholder-slate-600 focus:border-rose-500 outline-none transition"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-4 bg-[#080d18]">
          {apiKey ? (
            <button
              onClick={() => {
                setLocalKey('');
                onClear();
              }}
              className="flex items-center gap-1.5 text-xs text-rose-400 hover:text-rose-300 transition"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Remove Key</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                onSave(localKey.trim(), localModel.trim());
                onClose();
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-rose-500 text-white font-semibold text-xs shadow-md shadow-rose-600/20 hover:from-rose-500 hover:to-rose-400 transition"
            >
              <Check className="h-3.5 w-3.5" />
              <span>Save & Apply</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
