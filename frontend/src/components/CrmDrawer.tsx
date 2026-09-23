import React, { useEffect, useState } from 'react';
import { X, RefreshCw, Layers, ExternalLink, CheckCircle2 } from 'lucide-react';
import { CrmRecords } from '../types';

interface CrmDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function CrmDrawer({ isOpen, onClose }: CrmDrawerProps) {
  const [data, setData] = useState<{ mode: string; dc: string; records: CrmRecords } | null>(null);
  const [activeTab, setActiveTab] = useState<'leads' | 'deals' | 'cases'>('deals');
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/crm/status');
      const json = await res.json();
      setData(json);
    } catch (e) {
      console.error('Error fetching CRM status:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchStatus();
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-lg flex-col bg-[#080d18] border-l border-slate-800 shadow-2xl backdrop-blur-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800/80 px-6 py-4 bg-[#0a101f]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10 text-blue-400">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Zoho CRM Live Sync Inspector</h2>
            <p className="text-[11px] text-slate-400">
              {data?.mode === 'live' ? `Live OAuth 2.0 (${data?.dc?.toUpperCase()} DC)` : 'Local Seeded Sandbox'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Refresh CRM Records"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 bg-[#080d18] px-6">
        {(['leads', 'deals', 'cases'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-3 px-4 text-xs font-semibold capitalize border-b-2 transition ${
              activeTab === tab
                ? 'border-rose-500 text-rose-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab} ({data?.records[tab]?.length || 0})
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-3 font-mono text-xs">
        {activeTab === 'leads' && (
          <div className="space-y-3">
            {data?.records.leads?.length === 0 && (
              <div className="text-center py-10 text-slate-500">No leads found.</div>
            )}
            {data?.records.leads?.map((lead: any, idx: number) => (
              <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-100 text-sm">{lead.Full_Name || lead.Last_Name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {lead.Lead_Status || 'New'}
                  </span>
                </div>
                <div className="text-slate-400">Phone: {lead.Phone}</div>
                <div className="text-slate-400">Email: {lead.Email}</div>
                <div className="text-slate-400">City: {lead.City || 'Mumbai'}</div>
                <div className="text-rose-400 font-semibold pt-1">
                  Model: {lead.Vehicle_Model_of_Interest || 'Thar'}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'deals' && (
          <div className="space-y-3">
            {data?.records.deals?.length === 0 && (
              <div className="text-center py-10 text-slate-500">No deals found.</div>
            )}
            {data?.records.deals?.map((deal: any, idx: number) => (
              <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-100 text-sm">{deal.Deal_Name}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    {deal.Stage}
                  </span>
                </div>
                <div className="text-emerald-400 font-semibold">
                  Amount: ₹{Number(deal.Amount || 0).toLocaleString()}
                </div>
                {deal.Description && (
                  <div className="text-[11px] text-slate-400 pt-1 line-clamp-3 leading-relaxed">
                    {deal.Description}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'cases' && (
          <div className="space-y-3">
            {data?.records.cases?.length === 0 && (
              <div className="text-center py-10 text-slate-500">No cases found.</div>
            )}
            {data?.records.cases?.map((c: any, idx: number) => (
              <div key={idx} className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-100 text-sm">{c.Subject}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {c.Priority || 'Normal'}
                  </span>
                </div>
                <div className="text-slate-400">Status: {c.Status}</div>
                {c.Phone && <div className="text-slate-400">Phone: {c.Phone}</div>}
                {c.Deal_Name && (
                  <div className="text-amber-300">
                    Linked Deal: {typeof c.Deal_Name === 'object' ? c.Deal_Name.name : c.Deal_Name}
                  </div>
                )}
                {c.Related_To && (
                  <div className="text-blue-300">
                    Linked Contact: {typeof c.Related_To === 'object' ? c.Related_To.name : c.Related_To}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
