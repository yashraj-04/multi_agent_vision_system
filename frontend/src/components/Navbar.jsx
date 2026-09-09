import React from 'react';
import { Cpu, ShieldAlert, Activity, BarChart3, Database, Layers, LogIn } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, config, onModelChange, onStrategyChange }) {
  return (
    <header className="border-b border-[#2d3748] bg-[#1e2430]/95 backdrop-blur-xl sticky top-0 z-50 px-6 py-3.5 shadow-lg">
      <div className="flex flex-wrap items-center justify-between gap-4 max-w-[1600px] mx-auto">
        {/* Title / Brand Logo (Slate Obsidian Aesthetic) */}
        <div 
          onClick={() => setActiveTab('home')}
          className="flex items-center space-x-3 cursor-pointer group"
        >
          <div className="p-2 bg-[#cc0000]/10 border border-[#cc0000]/30 rounded-xl text-[#cc0000] glow-red group-hover:scale-105 transition-transform">
            <Cpu className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h1 className="text-base font-black tracking-wider uppercase flex items-center gap-2 text-[#f8fafc]">
              MULTI-VISION
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#cc0000]/20 text-[#cc0000] border border-[#cc0000]/40 font-bold">
                v1.0 RESEARCH
              </span>
            </h1>
            <p className="text-[10px] text-[#94a3b8] font-mono tracking-wide hidden sm:block">
              Multi-Agent Perception & Conflict Arbitration System
            </p>
          </div>
        </div>

        {/* Dynamic Controls: VisionLLM & Strategy Selectors */}
        <div className="hidden lg:flex items-center gap-3">
          {/* VisionLLM Selector */}
          <div className="flex items-center gap-2 bg-[#161b26] px-3 py-1.5 rounded-xl border border-[#2d3748] text-xs">
            <Layers className="w-4 h-4 text-[#38bdf8]" />
            <span className="text-[#94a3b8] font-medium font-mono">VisionLLM:</span>
            <select
              value={config.vision_model || 'moondream'}
              onChange={(e) => onModelChange(e.target.value)}
              className="bg-transparent text-[#38bdf8] font-mono font-bold focus:outline-none cursor-pointer"
            >
              {config.supported_models?.map((model) => (
                <option key={model} value={model} className="bg-[#1e2430] text-[#f8fafc]">
                  {model}
                </option>
              ))}
            </select>
          </div>

          {/* Strategy Selector (Tesla Red Highlight) */}
          <div className="flex items-center gap-2 bg-[#161b26] px-3 py-1.5 rounded-xl border border-[#2d3748] text-xs">
            <ShieldAlert className="w-4 h-4 text-[#cc0000]" />
            <span className="text-[#94a3b8] font-medium font-mono">Strategy:</span>
            <select
              value={config.active_strategy || 'Hybrid Arbitration'}
              onChange={(e) => onStrategyChange(e.target.value)}
              className="bg-transparent text-[#cc0000] font-mono font-bold focus:outline-none cursor-pointer"
            >
              {config.supported_strategies?.map((strat) => (
                <option key={strat} value={strat} className="bg-[#1e2430] text-[#f8fafc]">
                  {strat}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Navigation Tabs (Slate Obsidian Surface & Red Active Highlights) */}
        <nav className="hidden md:flex items-center bg-[#161b26] p-1 rounded-xl border border-[#2d3748] text-xs font-medium space-x-1">
          <button
            onClick={() => setActiveTab('home')}
            className={`px-3.5 py-1.5 rounded-lg transition-all font-mono ${
              activeTab === 'home'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            Home
          </button>

          <button
            onClick={() => setActiveTab('solutions')}
            className={`px-3.5 py-1.5 rounded-lg transition-all font-mono ${
              activeTab === 'solutions'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            Solutions
          </button>

          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all font-mono ${
              activeTab === 'dashboard'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            Dashboard
          </button>

          <button
            onClick={() => setActiveTab('benchmark')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all font-mono ${
              activeTab === 'benchmark'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Benchmarks
          </button>

          <button
            onClick={() => setActiveTab('dataset')}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition-all font-mono ${
              activeTab === 'dataset'
                ? 'bg-[#cc0000] text-white font-bold shadow-md glow-red'
                : 'text-[#94a3b8] hover:text-[#f8fafc]'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            Dataset
          </button>
        </nav>
      </div>
    </header>
  );
}
