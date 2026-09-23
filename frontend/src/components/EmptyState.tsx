import React from 'react';
import { Compass, Calendar, Truck, Wrench, ArrowUpRight } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export default function EmptyState({ onSelectPrompt }: EmptyStateProps) {
  const cards = [
    {
      stage: 'Stage 1: Discovery',
      title: 'XUV700 Specs & Pricing',
      description: 'Explore AX7L variants, Level-2 ADAS, and book a test drive slot.',
      prompt: 'Tell me the price and specs of the XUV700 AX7L, and book a test drive for Rajesh Sharma, 9820011223, Mumbai.',
      icon: Compass,
      color: 'from-blue-500/20 to-cyan-500/20 text-blue-400 border-blue-500/30',
    },
    {
      stage: 'Stage 2: Pipeline',
      title: 'Priya Patel Test Drive',
      description: 'Review Worli dealership appointment and update WhatsApp preferences.',
      prompt: 'Can you check the test drive status for Priya Patel? Registered phone is 9819988776.',
      icon: Calendar,
      color: 'from-amber-500/20 to-yellow-500/20 text-amber-400 border-amber-500/30',
    },
    {
      stage: 'Stage 3: Allocation',
      title: 'Track Scorpio-N Delivery',
      description: 'Verify VIN allocation, factory transit status, and balance due.',
      prompt: 'What is the allocation and delivery status of my booked Scorpio-N? Booking reference MAH-9921.',
      icon: Truck,
      color: 'from-purple-500/20 to-violet-500/20 text-purple-400 border-purple-500/30',
    },
    {
      stage: 'Stage 4: Ownership',
      title: 'Book Service Appointment',
      description: 'Log 15,000 km periodic maintenance linked to vehicle registration.',
      prompt: 'I want to schedule a 15,000 km periodic service for my Scorpio-N. Reg MH02CD1234, odometer 15000 km, phone 9822334455.',
      icon: Wrench,
      color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30',
    },
  ];

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-12 max-w-4xl mx-auto text-center">
      {/* Header Badge */}
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-rose-600 via-rose-500 to-red-600 text-white font-black text-2xl shadow-xl shadow-rose-600/20 mb-6">
        M
      </div>

      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white mb-2">
        Mahindra Automotive AI Concierge
      </h1>
      <p className="text-sm text-slate-400 max-w-lg mb-10">
        Enterprise multi-stage conversational assistant maintaining real-time bidirectional synchronization with Zoho CRM across discovery, sales, and service.
      </p>

      {/* Grid of Prompt Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full text-left">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              onClick={() => onSelectPrompt(card.prompt)}
              className="group relative flex flex-col justify-between rounded-xl border border-slate-800/90 bg-[#0d1424]/70 hover:bg-[#111a30] p-4 transition-all duration-200 cursor-pointer hover:border-slate-700 hover:shadow-lg hover:shadow-black/40"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`flex h-7 w-7 items-center justify-center rounded-lg border bg-gradient-to-br ${card.color}`}>
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      {card.stage}
                    </span>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-slate-600 group-hover:text-rose-400 transition" />
                </div>
                <h3 className="text-sm font-semibold text-slate-200 group-hover:text-white mb-1">
                  {card.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {card.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
