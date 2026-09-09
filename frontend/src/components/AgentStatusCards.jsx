import React from 'react';
import { Eye, Navigation, Shield, EyeOff, AlertTriangle, Disc, Gauge, Zap, Sliders } from 'lucide-react';

const AGENT_ICONS = {
  "Object Detection Agent": Eye,
  "Lane Detection Agent": Navigation,
  "Traffic Rule Agent": Shield,
  "Scene Understanding Agent": EyeOff,
  "Risk Assessment Agent": AlertTriangle,
  "Planning Agent": Disc,
  "Strategy Selector Agent": Sliders
};

export default function AgentStatusCards({ agentOutputs = [] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {agentOutputs.map((agent) => {
        const IconComponent = AGENT_ICONS[agent.agent_name] || Gauge;
        const isMetaAgent = agent.agent_name === "Strategy Selector Agent";
        const isPlanning = agent.agent_name === "Planning Agent";

        return (
          <div
            key={agent.agent_name}
            className={`p-4 rounded-2xl border transition-all ${
              isMetaAgent
                ? 'bg-[#1e2430] border-[#cc0000]/60 shadow-lg glow-red'
                : isPlanning
                ? 'bg-[#1e2430] border-[#cc0000]/30'
                : 'bg-[#1e2430] border-[#2d3748] hover:border-[#94a3b8]'
            }`}
          >
            {/* Card Header */}
            <div className="flex items-center justify-between border-b border-[#2d3748] pb-2.5 mb-3">
              <div className="flex items-center gap-2.5">
                <div className={`p-1.5 rounded-lg bg-[#161b26] border ${isMetaAgent ? 'text-[#cc0000] border-[#cc0000]/40' : 'text-[#94a3b8] border-[#2d3748]'}`}>
                  <IconComponent className="w-4 h-4" />
                </div>
                <h3 className="text-xs font-bold text-[#f8fafc] tracking-wide truncate">{agent.agent_name}</h3>
              </div>
              <div className="flex items-center gap-1 text-[10px] font-mono text-[#94a3b8]">
                <Zap className="w-3 h-3 text-[#cc0000]" />
                {agent.latency_ms} ms
              </div>
            </div>

            {/* Decision & Confidence */}
            <div className="flex items-center justify-between mb-3">
              <div>
                <span className="text-[10px] uppercase font-mono text-[#94a3b8] block mb-0.5">Decision</span>
                <span className={`text-xs font-bold font-mono px-2 py-0.5 rounded uppercase ${
                  isMetaAgent
                    ? 'bg-[#cc0000]/20 text-[#cc0000] border border-[#cc0000]/40'
                    : agent.decision.includes("STOP") || agent.decision.includes("BRAKE") || agent.decision.includes("WARNING")
                    ? 'bg-[#cc0000]/20 text-[#cc0000] border border-[#cc0000]/40'
                    : agent.decision.includes("GO") || agent.decision.includes("CLEAR")
                    ? 'bg-[#00e676]/20 text-[#00e676] border border-[#00e676]/40'
                    : 'bg-[#fbbf24]/20 text-[#fbbf24] border border-[#fbbf24]/40'
                }`}>
                  {agent.decision}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] uppercase font-mono text-[#94a3b8] block mb-0.5">Confidence</span>
                <span className="text-xs font-bold font-mono text-[#f8fafc]">
                  {(agent.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Confidence Progress Bar */}
            <div className="w-full bg-[#161b26] rounded-full h-1.5 overflow-hidden mb-3 border border-[#2d3748]">
              <div
                className={`h-1.5 rounded-full transition-all duration-500 ${
                  agent.confidence >= 0.85 ? 'bg-[#00e676]' : agent.confidence >= 0.6 ? 'bg-[#fbbf24]' : 'bg-[#cc0000]'
                }`}
                style={{ width: `${agent.confidence * 100}%` }}
              />
            </div>

            {/* Reasoning Note */}
            {agent.reasoning && (
              <p className="text-[11px] text-[#94a3b8] font-mono leading-tight truncate">
                {agent.reasoning}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}

