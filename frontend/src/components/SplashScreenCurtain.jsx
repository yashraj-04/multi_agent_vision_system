import React, { useState, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

export default function SplashScreenCurtain() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Calculate scroll progress ratio (0 at top, 1 when scrolled 70% of viewport)
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800;
  const progress = Math.min(scrollY / (viewportHeight * 0.7), 1);

  // MULTI slides left on scroll (-X px), VISION slides right (+X px)
  const multiOffsetPx = -(progress * 220);
  const visionOffsetPx = progress * 220;
  const titleOpacity = Math.max(0, 1 - progress * 1.3);

  const handleIndicatorClick = () => {
    const mainContent = document.getElementById('main-content-section');
    if (mainContent) {
      mainContent.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section className="relative w-full h-screen bg-[#12161f] overflow-hidden flex flex-col justify-between items-center select-none z-40 border-b border-[#2d3748]">
      {/* Subtle Background Grid & Tesla Crimson Radial Ambient Glow */}
      <div className="absolute inset-0 bg-grid-pattern opacity-35 pointer-events-none" />
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[850px] h-[550px] bg-gradient-to-r from-red-600/15 via-red-900/10 to-transparent blur-[150px] rounded-full pointer-events-none transition-opacity duration-300"
        style={{ opacity: titleOpacity }}
      />

      {/* Top Margin Spacer */}
      <div className="pt-12" />

      {/* Centered Clean MULTI-VISION Title Section (Slate Obsidian Palette: #f8fafc off-white & #cc0000 crimson accent) */}
      <div className="z-10 text-center px-4 my-auto flex flex-col items-center justify-center space-y-4 w-full">
        {/* SPLIT TITLE CONTAINER */}
        <div 
          className="flex items-center justify-center gap-2 sm:gap-4 py-2 w-full max-w-7xl transition-opacity duration-300"
          style={{ opacity: titleOpacity }}
        >
          {/* MULTI: Slides from Left */}
          <div className="inline-block py-1">
            <span 
              className="animate-slide-left text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black font-sans tracking-wider uppercase gradient-text-multivision leading-none inline-block transition-transform duration-100 ease-out"
              style={{ 
                transform: `translateX(${multiOffsetPx}px)`
              }}
            >
              MULTI-
            </span>
          </div>

          {/* VISION: Slides from Right */}
          <div className="inline-block py-1">
            <span 
              className="animate-slide-right text-6xl sm:text-7xl md:text-8xl lg:text-9xl font-black font-sans tracking-wider uppercase gradient-text-multivision leading-none inline-block transition-transform duration-100 ease-out"
              style={{ 
                transform: `translateX(${visionOffsetPx}px)`
              }}
            >
              VISION
            </span>
          </div>
        </div>

        <p 
          className="text-[#94a3b8] font-mono text-xs sm:text-sm tracking-[0.2em] max-w-xl mx-auto uppercase transition-all duration-300 font-semibold"
          style={{ opacity: titleOpacity }}
        >
          Multi-Agent Conflict Resolution • VisionLLM Reasoning • Autonomous Perception
        </p>
      </div>

      {/* Minimalist Scroll Down Indicator (Tesla Crimson Highlight on Hover) */}
      <div 
        onClick={handleIndicatorClick}
        className="pb-10 z-10 flex flex-col items-center justify-center cursor-pointer group transition-opacity duration-300"
        style={{ opacity: titleOpacity }}
      >
        <div className="p-2.5 rounded-full text-[#94a3b8] group-hover:text-[#cc0000] transition-all animate-bounce">
          <ChevronDown className="w-6 h-6" />
        </div>
      </div>
    </section>
  );
}
