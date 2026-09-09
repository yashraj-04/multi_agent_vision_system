import React from 'react';
import { X, Sparkles, Eye, ShieldAlert, Cpu } from 'lucide-react';

export default function VisionLLMModal({ isOpen, onClose, sceneAgentData, modelName }) {
  if (!isOpen || !sceneAgentData) return null;

  const evidence = sceneAgentData.evidence || {};
  const vlmInfo = evidence.vlm_verification || sceneAgentData.reasoning;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="bg-cyber-panel border border-cyber-accent/40 rounded-2xl w-full max-w-2xl p-6 shadow-2xl space-y-5 glow-accent">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-cyber-border pb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyber-accent/20 text-cyber-accent border border-cyber-accent/40">
              <Sparkles className="w-5 h-5 animate-spin" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                VisionLLM Reasoning Engine
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyber-accent/20 text-cyber-accent font-semibold border border-cyber-accent/30">
                  {modelName}
                </span>
              </h3>
              <p className="text-xs text-slate-400 font-mono">Semantic Visual Reasoning & Anomaly Verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-cyber-dark transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* VisionLLM Analysis Overview */}
        <div className="space-y-4 text-xs font-sans">
          <div className="p-4 rounded-xl bg-cyber-dark/80 border border-cyber-border/60 space-y-2">
            <h4 className="font-mono text-cyber-accent font-bold uppercase text-[11px] flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5" /> Scene Understanding Rationale
            </h4>
            <p className="text-slate-200 leading-relaxed font-sans text-sm">
              "{sceneAgentData.reasoning}"
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-cyber-dark/60 border border-cyber-border/40 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Weather Conditions</span>
              <p className="text-white font-mono font-medium">{evidence.weather || "Clear Visibility"}</p>
            </div>
            <div className="p-3 rounded-lg bg-cyber-dark/60 border border-cyber-border/40 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Road Surface</span>
              <p className="text-white font-mono font-medium">{evidence.road_condition || "Dry Paved Road"}</p>
            </div>
          </div>

          {/* VLM Verification & Hidden Risk */}
          {evidence.hidden_risk && (
            <div className="p-3.5 rounded-xl bg-cyber-warning/10 border border-cyber-warning/30 space-y-1.5">
              <h4 className="font-mono text-cyber-warning font-bold uppercase text-[11px] flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5" /> Hidden Risk & Blind-Spot Estimation
              </h4>
              <p className="text-slate-200 text-xs leading-relaxed">
                {evidence.hidden_risk.description || "No hidden risks identified."}
              </p>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-cyber-accent text-cyber-dark font-bold text-xs hover:bg-cyber-accent/80 transition-all"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}

