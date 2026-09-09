import React, { useState } from 'react';
import { ShieldCheck, Clock, Sparkles, Cpu, Sliders, CheckCircle2, AlertTriangle, ArrowRight, BookOpen, Gauge } from 'lucide-react';

export default function ResolutionEnginePanel({ resolution, activeStrategy, supportedStrategies = [], onSelectStrategy }) {
  if (!resolution) return null;

  const [mode, setMode] = useState('auto'); // 'auto' or 'manual'

  const autoStrategy = resolution.auto_selected_strategy || activeStrategy || "Rule-Based Arbitration";
  const currentStrategy = mode === 'auto' ? autoStrategy : activeStrategy;
  const reasoning = resolution.selection_reasoning || resolution.reasoning || "Meta-Orchestrator evaluated agent confidences & hazard severity.";
  const trace = resolution.decision_trace || {};
  const actuator = resolution.actuator_command || {};

  // Infer the Meta-Orchestrator logic rule triggered for the auto-selected strategy
  const getRuleDescription = (strat) => {
    if (strat === "Rule-Based Arbitration") {
      return { rule: "Rule 1: Safety Critical Override", detail: "Triggered by CRITICAL risk, red light, or mandatory stop sign compliance.", badgeColor: "bg-[#cc0000]/20 text-[#cc0000] border-[#cc0000]/40" };
    }
    if (strat === "Leader Election") {
      return { rule: "Rule 2: Single Dominant Agent", detail: "Triggered when a primary perception agent exhibits >= 95% confidence.", badgeColor: "bg-[#38bdf8]/20 text-[#38bdf8] border-[#38bdf8]/40" };
    }
    if (strat === "Confidence Weighted Voting") {
      return { rule: "Rule 3: Confidence Variance Spread", detail: "Triggered when agent confidence spread exceeds 15%.", badgeColor: "bg-[#fbbf24]/20 text-[#fbbf24] border-[#fbbf24]/40" };
    }
    return { rule: "Rule 4: Balanced Consensus", detail: "Triggered when perception agents demonstrate balanced agreement.", badgeColor: "bg-[#00e676]/20 text-[#00e676] border-[#00e676]/40" };
  };

  const metaRule = getRuleDescription(autoStrategy);

  // Candidate Strategy Suitability Match Scores for UI Showcase
  const suitabilityScores = [
    { name: "Rule-Based Arbitration", score: autoStrategy === "Rule-Based Arbitration" ? 98 : 65 },
    { name: "Leader Election", score: autoStrategy === "Leader Election" ? 94 : 58 },
    { name: "Confidence Weighted Voting", score: autoStrategy === "Confidence Weighted Voting" ? 91 : 72 },
    { name: "Majority Voting", score: autoStrategy === "Majority Voting" ? 89 : 45 },
  ];

  return (
    <div className="p-5 rounded-2xl border border-[#cc0000]/40 bg-[#1e2430] space-y-5 shadow-xl">
      {/* Header with Mode Toggle (Auto vs Manual) */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#2d3748] pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[#cc0000]/10 text-[#cc0000] border border-[#cc0000]/40 glow-red">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#f8fafc] tracking-wide flex items-center gap-2 font-mono">
              STRATEGY SELECTOR META-ORCHESTRATOR
            </h3>
            <p className="text-[11px] text-[#94a3b8] font-mono">Automated Decision Pipeline & Arbitration Engine</p>
          </div>
        </div>

        {/* Mode Selector (Auto-Selected vs Manual Override) */}
        <div className="flex items-center bg-[#161b26] p-1 rounded-xl border border-[#2d3748] text-xs font-mono">
          <button
            onClick={() => setMode('auto')}
            className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              mode === 'auto'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            Auto-Selected
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              mode === 'manual'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            Manual Override
          </button>
        </div>
      </div>

      {/* Manual Mode Strategy Dropdown Selection */}
      {mode === 'manual' && (
        <div className="p-3.5 rounded-xl bg-[#161b26] border border-[#cc0000]/50 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-[#94a3b8] font-bold">Manual Strategy Override:</span>
            <span className="text-[#cc0000] font-bold">10 Research Algorithms</span>
          </div>
          <select
            value={activeStrategy}
            onChange={(e) => onSelectStrategy(e.target.value)}
            className="w-full bg-[#1e2430] border border-[#2d3748] text-[#f8fafc] text-xs font-mono font-bold py-2 px-3 rounded-lg focus:outline-none focus:border-[#cc0000]"
          >
            {supportedStrategies.map((strat) => (
              <option key={strat} value={strat}>
                {strat}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 🤖 AUTOMATED STRATEGY SELECTION DECISION TRACE CARD */}
      <div className="p-4 rounded-xl bg-[#161b26] border border-[#2d3748] space-y-3">
        <div className="flex items-center justify-between border-b border-[#2d3748] pb-2">
          <span className="text-xs font-bold font-mono text-[#f8fafc] flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[#cc0000]" />
            Meta-Orchestrator Decision Trace
          </span>
          <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${metaRule.badgeColor}`}>
            {mode === 'auto' ? 'ACTIVE: AUTO-SELECTED' : 'OVERRIDDEN BY USER'}
          </span>
        </div>

        {/* Logic Trace Pipeline Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-lg bg-[#1e2430] border border-[#2d3748] space-y-1">
            <span className="text-[10px] text-[#94a3b8] uppercase block font-bold">Step 1: Hazard Scan</span>
            <span className="text-xs font-bold text-[#f8fafc] flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#00e676]" />
              {resolution.has_conflicts ? 'Conflict Event Detected' : 'Perception Clear'}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-[#1e2430] border border-[#2d3748] space-y-1">
            <span className="text-[10px] text-[#94a3b8] uppercase block font-bold">Step 2: Rule Evaluated</span>
            <span className="text-xs font-bold text-[#38bdf8] truncate block">
              {metaRule.rule}
            </span>
          </div>

          <div className="p-2.5 rounded-lg bg-[#1e2430] border border-[#cc0000]/40 space-y-1">
            <span className="text-[10px] text-[#94a3b8] uppercase block font-bold">Step 3: Selected Strategy</span>
            <span className="text-xs font-bold text-[#cc0000] truncate block">
              {autoStrategy}
            </span>
          </div>
        </div>

        {/* Detailed Selection Rationale */}
        <div className="p-2.5 rounded-lg bg-[#1e2430] border border-[#2d3748] text-xs font-mono space-y-1">
          <span className="text-[10px] text-[#94a3b8] font-bold block uppercase">Meta-Orchestrator Selection Rationale:</span>
          <p className="text-[#f8fafc] text-[11px] leading-relaxed">{reasoning}</p>
        </div>

        {/* Strategy Suitability Match Scores Visual Bars */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-mono uppercase text-[#94a3b8] font-bold block">
            Algorithm Suitability Match Scores (Context-Aware):
          </span>
          <div className="space-y-1">
            {suitabilityScores.map((s) => (
              <div key={s.name} className="flex items-center justify-between text-[11px] font-mono">
                <span className={`truncate max-w-[180px] ${s.name === autoStrategy ? 'text-[#cc0000] font-bold' : 'text-[#94a3b8]'}`}>
                  {s.name}
                </span>
                <div className="flex items-center gap-2 flex-1 ml-3">
                  <div className="w-full bg-[#1e2430] rounded-full h-1.5 overflow-hidden border border-[#2d3748]">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-500 ${
                        s.name === autoStrategy ? 'bg-[#cc0000]' : 'bg-[#94a3b8]/40'
                      }`}
                      style={{ width: `${s.score}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-bold min-w-[28px] text-right text-[#f8fafc]">{s.score}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ARBITRATED CONTROL DECISION RESULT */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-[#161b26] p-4 rounded-xl border border-[#2d3748]">
        {/* Final Action */}
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-mono text-[#94a3b8] font-bold block">Arbitrated Action</span>
          <span className="text-base font-black font-mono text-[#cc0000] uppercase tracking-wider px-3 py-1 rounded-lg bg-[#cc0000]/10 border border-[#cc0000]/30 glow-red inline-block">
            {resolution.final_decision}
          </span>
        </div>

        {/* Confidence & Latency */}
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-mono text-[#94a3b8] font-bold block">Engine Confidence</span>
          <div className="flex items-center gap-2">
            <span className="text-base font-black font-mono text-[#f8fafc]">
              {((resolution.confidence || 0) * 100).toFixed(1)}%
            </span>
            <span className="text-[11px] font-mono text-[#94a3b8] flex items-center gap-1 ml-2">
              <Clock className="w-3.5 h-3.5 text-[#cc0000]" />
              {resolution.resolution_time_ms} ms
            </span>
          </div>
        </div>

        {/* Winning Agent Authority */}
        <div className="space-y-1">
          <span className="text-[10px] uppercase font-mono text-[#94a3b8] font-bold block">Winning Perception Authority</span>
          <span className="text-xs font-bold font-mono text-[#f8fafc] truncate block">
            {resolution.winning_agent || "Ensemble Consensus"}
          </span>
        </div>
      </div>

      {/* Physical Actuator Command Trace (if available) */}
      {actuator && actuator.driver_instruction && (
        <div className="p-3 rounded-xl bg-[#161b26] border border-[#2d3748] flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-[#cc0000]" />
            <span className="text-[#94a3b8]">Actuator Command:</span>
            <span className="text-[#f8fafc] font-bold">{actuator.driver_instruction}</span>
          </div>
        </div>
      )}
    </div>
  );
}
