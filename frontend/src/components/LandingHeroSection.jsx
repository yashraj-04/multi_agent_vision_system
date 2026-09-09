import React from 'react';
import { ArrowRight, Eye, Cpu, Shield, Zap, Database, BarChart3 } from 'lucide-react';

export default function LandingHeroSection({ onNavigateTab }) {
  return (
    <section className="relative w-full py-16 px-6 max-w-[1600px] mx-auto space-y-16 bg-[#12161f]">
      {/* Hero Headline & Intro */}
      <div className="text-center max-w-4xl mx-auto space-y-6">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#cc0000]/10 border border-[#cc0000]/30 text-xs font-mono text-[#cc0000] font-bold">
          <Zap className="w-4 h-4 text-[#cc0000]" />
          MULTIMODAL PERCEPTION ENGINE • RESEARCH v1.0
        </div>

        <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-[#f8fafc] uppercase font-sans leading-tight">
          INNOVATION THROUGH <br />
          <span className="gradient-text-red">VISUAL TECH</span>
        </h1>

        <p className="text-base sm:text-lg text-[#94a3b8] font-sans leading-relaxed max-w-2xl mx-auto font-normal">
          Empowering autonomous systems with multi-agent computer vision, 
          real-time conflict arbitration, and high-precision VisionLLM abstraction.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <button
            onClick={() => onNavigateTab('dashboard')}
            className="flex items-center gap-3 px-6 py-3.5 rounded-xl bg-[#cc0000] text-white font-mono font-bold text-sm hover:brightness-110 transition-all shadow-md group cursor-pointer glow-red"
          >
            <Eye className="w-5 h-5 text-white" />
            LAUNCH PERCEPTION DASHBOARD
            <ArrowRight className="w-4 h-4 text-white group-hover:translate-x-1 transition-transform" />
          </button>

          <button
            onClick={() => onNavigateTab('benchmark')}
            className="flex items-center gap-3 px-6 py-3.5 rounded-xl bg-[#1e2430] border border-[#2d3748] text-[#f8fafc] font-mono font-bold text-sm hover:border-[#cc0000] hover:text-[#cc0000] transition-all cursor-pointer"
          >
            <BarChart3 className="w-5 h-5 text-[#cc0000]" />
            EXPLORE 10-STRATEGY BENCHMARKS
          </button>
        </div>
      </div>

      {/* Platform Stats Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 rounded-2xl bg-[#1e2430] border border-[#2d3748] shadow-xl">
        <div className="text-center space-y-1 p-2">
          <span className="text-xs font-mono text-[#94a3b8] uppercase tracking-wider font-bold">Perception Agents</span>
          <p className="text-3xl font-black font-mono text-[#f8fafc]">6 AI Models</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Object, Lane, Sign, Scene, Risk</span>
        </div>
        <div className="text-center space-y-1 p-2 border-l border-[#2d3748]">
          <span className="text-xs font-mono text-[#94a3b8] uppercase tracking-wider font-bold">Conflict Algorithms</span>
          <p className="text-3xl font-black font-mono text-[#cc0000]">10 Strategies</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Voting, Bayesian, Entropy</span>
        </div>
        <div className="text-center space-y-1 p-2 border-l border-[#2d3748]">
          <span className="text-xs font-mono text-[#94a3b8] uppercase tracking-wider font-bold">VisionLLMs Supported</span>
          <p className="text-3xl font-black font-mono text-[#38bdf8]">5 Frameworks</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Moondream, LLaVA, Qwen2.5</span>
        </div>
        <div className="text-center space-y-1 p-2 border-l border-[#2d3748]">
          <span className="text-xs font-mono text-[#94a3b8] uppercase tracking-wider font-bold">Arbitration Speed</span>
          <p className="text-3xl font-black font-mono text-[#00e676]">&lt; 1.0 ms</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Real-time sub-millisecond</span>
        </div>
      </div>

      {/* Feature Architecture Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div 
          onClick={() => onNavigateTab('dashboard')}
          className="p-6 rounded-2xl bg-[#1e2430] border border-[#2d3748] hover:border-[#cc0000] transition-all space-y-4 group cursor-pointer hover:scale-[1.02] shadow-lg hover:shadow-[0_0_30px_rgba(204,0,0,0.15)]"
        >
          <div className="w-12 h-12 rounded-xl bg-[#cc0000]/10 border border-[#cc0000]/20 flex items-center justify-center text-[#cc0000]">
            <Cpu className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-[#f8fafc] font-mono flex items-center justify-between">
            Multi-Agent Perception
            <ArrowRight className="w-4 h-4 text-[#cc0000] opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed font-sans">
            Independent specialized vision agents analyze road frames concurrently, detecting obstacles, traffic signals, lanes, and risk factors with weighted confidence bounds.
          </p>
        </div>

        <div 
          onClick={() => onNavigateTab('benchmark')}
          className="p-6 rounded-2xl bg-[#1e2430] border border-[#2d3748] hover:border-[#cc0000] transition-all space-y-4 group cursor-pointer hover:scale-[1.02] shadow-lg hover:shadow-[0_0_30px_rgba(204,0,0,0.15)]"
        >
          <div className="w-12 h-12 rounded-xl bg-[#cc0000]/10 border border-[#cc0000]/20 flex items-center justify-center text-[#cc0000]">
            <Shield className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-[#f8fafc] font-mono flex items-center justify-between">
            Conflict Resolution Suite
            <ArrowRight className="w-4 h-4 text-[#cc0000] opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed font-sans">
            Compare 10 mathematical arbitration strategies (Majority Voting, Bayesian Fusion, Dynamic Entropy Ensembles) to resolve agent perception discrepancies.
          </p>
        </div>

        <div 
          onClick={() => onNavigateTab('dataset')}
          className="p-6 rounded-2xl bg-[#1e2430] border border-[#2d3748] hover:border-[#cc0000] transition-all space-y-4 group cursor-pointer hover:scale-[1.02] shadow-lg hover:shadow-[0_0_30px_rgba(204,0,0,0.15)]"
        >
          <div className="w-12 h-12 rounded-xl bg-[#cc0000]/10 border border-[#cc0000]/20 flex items-center justify-center text-[#cc0000]">
            <Database className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-[#f8fafc] font-mono flex items-center justify-between">
            Dataset & Model Training
            <ArrowRight className="w-4 h-4 text-[#cc0000] opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p className="text-xs text-[#94a3b8] leading-relaxed font-sans">
            Inspect autonomous dataset distribution metrics, mAP scores, mIoU lane metrics, and fine-tuning history for local perception models.
          </p>
        </div>
      </div>
    </section>
  );
}
