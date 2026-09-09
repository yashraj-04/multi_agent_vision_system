import React, { useState, useEffect, useRef } from 'react';
import SplashScreenCurtain from './components/SplashScreenCurtain';
import Navbar from './components/Navbar';
import LandingHeroSection from './components/LandingHeroSection';
import PerceptionDashboard from './components/PerceptionDashboard';
import ExperimentBenchmark from './components/ExperimentBenchmark';
import DatasetTrainerPanel from './components/DatasetTrainerPanel';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [latestPipelineData, setLatestPipelineData] = useState(null);
  const mainContentRef = useRef(null);

  const [config, setConfig] = useState({
    vision_model: 'moondream',
    supported_models: ['moondream', 'llava', 'gemma3-vision', 'qwen2.5-vl', 'phi-vision'],
    active_strategy: 'Hybrid Arbitration',
    supported_strategies: [
      "Majority Voting",
      "Confidence Weighted Voting",
      "Rule-Based Arbitration",
      "Leader Election",
      "Dynamic Reliability Scoring",
      "Bayesian Fusion",
      "Weighted Consensus",
      "Hybrid Arbitration",
      "Adaptive Reliability Learning",
      "Dynamic Entropy-Weighted Ensemble"
    ]
  });

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const cfg = await api.getConfig();
      setConfig(cfg);
    } catch (err) {
      console.error("Backend config fetch error", err);
    }
  };

  const handleModelChange = async (newModel) => {
    try {
      const updated = await api.updateConfig({ vision_model: newModel });
      setConfig(prev => ({ ...prev, vision_model: updated.vision_model }));
    } catch (err) {
      console.error("Failed to update vision model", err);
    }
  };

  const handleStrategyChange = async (newStrategy) => {
    try {
      const updated = await api.updateConfig({ default_strategy: newStrategy });
      setConfig(prev => ({ ...prev, active_strategy: updated.active_strategy }));
    } catch (err) {
      console.error("Failed to update active strategy", err);
    }
  };

  const handleRevealCurtain = () => {
    if (mainContentRef.current) {
      mainContentRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleNavigateTab = (tab) => {
    setActiveTab(tab);
    if (mainContentRef.current) {
      mainContentRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#12161f] text-[#f8fafc] flex flex-col font-sans selection:bg-[#cc0000]/20">
      {/* 1. SPLASH SCREEN CURTAIN */}
      <SplashScreenCurtain onReveal={handleRevealCurtain} />

      {/* 2. REVEALED MAIN CONTENT SECTION */}
      <div id="main-content-section" ref={mainContentRef} className="min-h-screen flex flex-col bg-[#12161f]">
        <Navbar
          activeTab={activeTab}
          setActiveTab={(tab) => handleNavigateTab(tab)}
          config={config}
          onModelChange={handleModelChange}
          onStrategyChange={handleStrategyChange}
        />

        <main className="flex-1 w-full">
          <div className={activeTab === 'home' || activeTab === 'solutions' ? 'block' : 'hidden'}>
            <LandingHeroSection onNavigateTab={handleNavigateTab} />
          </div>

          <div className={activeTab === 'dashboard' ? 'block p-6 max-w-[1600px] mx-auto' : 'hidden'}>
            <PerceptionDashboard
              config={config}
              onStrategyChange={handleStrategyChange}
              onPipelineDataChange={(data) => setLatestPipelineData(data)}
            />
          </div>

          <div className={activeTab === 'benchmark' ? 'block p-6 max-w-[1600px] mx-auto' : 'hidden'}>
            <ExperimentBenchmark pipelineData={latestPipelineData} />
          </div>

          <div className={activeTab === 'dataset' ? 'block p-6 max-w-[1600px] mx-auto' : 'hidden'}>
            <DatasetTrainerPanel />
          </div>
        </main>

        {/* System Footer */}
        <footer className="border-t border-[#2d3748] bg-[#1e2430] py-6 px-6 text-center text-xs font-mono text-[#94a3b8] space-y-1">
          <p className="tracking-widest uppercase text-[#f8fafc] font-bold">MULTI-VISION • Autonomous Visual Intelligence System</p>
          <p className="text-[11px] text-[#94a3b8]">Conflict Resolution Strategies in Multi-Agent Vision Systems for Robotics</p>
        </footer>
      </div>
    </div>
  );
}
