import React from 'react';
import { AlertOctagon, CheckCircle2 } from 'lucide-react';

export default function ConflictViewer({ conflicts = [] }) {
  if (conflicts.length === 0) {
    return (
      <div className="p-4 rounded-2xl border border-[#00e676]/30 bg-[#1e2430] flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-[#00e676]" />
          <div>
            <h4 className="text-sm font-bold text-[#f8fafc]">Full Multi-Agent Alignment</h4>
            <p className="text-xs text-[#94a3b8] font-mono">No perception or rule contradictions detected across active agents.</p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold text-[#00e676] px-2.5 py-1 rounded-lg bg-[#00e676]/10 border border-[#00e676]/30">
          0 CONFLICTS
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-[#cc0000] flex items-center gap-2 font-mono">
          <AlertOctagon className="w-4 h-4 animate-bounce text-[#cc0000]" />
          AUTOMATED CONFLICT DETECTOR ({conflicts.length} EVENT{conflicts.length > 1 ? 'S' : ''})
        </h3>
        <span className="text-[11px] font-mono text-[#94a3b8]">Cross-Agent Disagreement Detected</span>
      </div>

      {conflicts.map((conflict, idx) => (
        <div
          key={conflict.id || idx}
          className="p-4 rounded-2xl border border-[#cc0000]/40 bg-[#1e2430] glow-red transition-all shadow-xl"
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold font-mono text-[#f8fafc] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#cc0000] animate-ping" />
              [{conflict.id}] {conflict.type}
            </span>
            <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-md bg-[#cc0000]/20 text-[#cc0000] border border-[#cc0000]/40 font-bold uppercase">
              {conflict.severity} SEVERITY
            </span>
          </div>

          <p className="text-xs text-[#f8fafc] mb-3 leading-relaxed font-sans">
            {conflict.description}
          </p>

          {/* Competing proposals */}
          <div className="bg-[#161b26] p-3 rounded-xl border border-[#2d3748]">
            <span className="text-[10px] font-mono uppercase text-[#94a3b8] block mb-1.5 font-bold">
              Competing Agent Proposals:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
              {conflict.competing_proposals &&
                Object.entries(conflict.competing_proposals).map(([agent, proposal]) => (
                  <div key={agent} className="flex items-center justify-between bg-[#1e2430] p-2 rounded-lg border border-[#2d3748]">
                    <span className="text-[#94a3b8] font-medium truncate">{agent}:</span>
                    <span className="text-[#cc0000] font-bold uppercase px-1.5 py-0.5 rounded bg-[#cc0000]/10 border border-[#cc0000]/30 text-[10px]">
                      {typeof proposal === 'object' ? proposal.action || JSON.stringify(proposal) : proposal}
                    </span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
