import React, { useState, useEffect, useRef } from 'react';
import { Play, Upload, Camera, Sparkles, Layers, Video, RefreshCw, AlertCircle, Film, UploadCloud, Eye, Sliders, Info } from 'lucide-react';
import { api } from '../services/api';
import AgentStatusCards from './AgentStatusCards';
import ConflictViewer from './ConflictViewer';
import ResolutionEnginePanel from './ResolutionEnginePanel';
import VisionLLMModal from './VisionLLMModal';

const OVERLAY_OPTIONS = [
  "YOLO Agent Active",
  "Lane Detection Agent",
  "Risk Assessment Agent",
  "Traffic Rule Agent",
  "All Agents Combined"
];

export default function PerceptionDashboard({ config, onStrategyChange, onImageUploaded, onPipelineDataChange }) {
  const [loading, setLoading] = useState(false);
  const [pipelineData, setPipelineData] = useState(null);

  useEffect(() => {
    if (onPipelineDataChange) {
      onPipelineDataChange(pipelineData);
    }
  }, [pipelineData]);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isVisionLLMOpen, setIsVisionLLMOpen] = useState(false);
  const [webcamActive, setWebcamActive] = useState(false);
  const [selectedOverlay, setSelectedOverlay] = useState("YOLO Agent Active");
  
  // Media Preview States
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isVideo, setIsVideo] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState('');

  const videoRef = useRef(null);
  const uploadedVideoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (webcamActive && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(err => console.error("Video play error:", err));
    }
  }, [webcamActive]);

  const handleRunAgents = async (fileObj = null, currentOverlay = selectedOverlay) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      let res;
      const targetFile = fileObj || uploadedFile;
      if (targetFile && !isVideo) {
        res = await api.uploadImage(targetFile, currentOverlay);
      } else if (isVideo) {
        captureUploadedVideoFrame(currentOverlay);
        return;
      } else {
        const formData = new FormData();
        formData.append('overlay_mode', currentOverlay);
        res = await api.runAgents(formData);
      }
      setPipelineData(res);
      if (res.error) {
        setErrorMsg(res.error);
      }
    } catch (err) {
      console.error("Error running agents:", err);
      setErrorMsg("Failed to connect to perception server. Please check backend server.");
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayChange = (newOverlay) => {
    setSelectedOverlay(newOverlay);
    if (uploadedFile || webcamActive || pipelineData) {
      handleRunAgents(uploadedFile, newOverlay);
    }
  };

  const [isDragging, setIsDragging] = useState(false);

  const processSelectedFile = (file) => {
    if (!file) return;
    const localUrl = URL.createObjectURL(file);
    setPreviewUrl(localUrl);
    setUploadedFile(file);
    setUploadedFileName(file.name);
    setErrorMsg(null);
    setPipelineData(null);

    if (webcamActive) {
      stopWebcam();
    }

    const isVideoFile = file.type.startsWith('video/');
    setIsVideo(isVideoFile);

    // Notify parent to reset benchmark stats
    if (onImageUploaded) onImageUploaded();
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    processSelectedFile(file);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const captureUploadedVideoFrame = (currentOverlay = selectedOverlay) => {
    if (!uploadedVideoRef.current || !canvasRef.current) return;
    const v = uploadedVideoRef.current;
    const canvas = canvasRef.current;
    canvas.width = v.videoWidth || 640;
    canvas.height = v.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL('image/jpeg');

    setLoading(true);
    const formData = new FormData();
    formData.append('image_b64', b64);
    formData.append('sample_name', uploadedFileName || 'uploaded_video.mp4');
    formData.append('overlay_mode', currentOverlay);
    api.runAgents(formData).then(res => {
      setPipelineData(res);
      setLoading(false);
    }).catch(err => {
      setErrorMsg("Failed to analyze video frame.");
      setLoading(false);
    });
  };

  const handleStrategySelect = async (newStrategy) => {
    onStrategyChange(newStrategy);
    if (pipelineData && pipelineData.agent_outputs) {
      setLoading(true);
      try {
        const payload = {
          strategy: newStrategy,
          agent_outputs: pipelineData.agent_outputs,
          conflicts: pipelineData.conflicts || []
        };
        const res = await api.runConflictResolution(payload);
        setPipelineData(prev => ({ ...prev, resolution: res }));
      } catch (err) {
        console.error("Error switching resolution strategy:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setWebcamActive(false);
  };

  const toggleWebcam = async () => {
    if (webcamActive) {
      stopWebcam();
    } else {
      setPreviewUrl(null);
      setUploadedFile(null);
      setIsVideo(false);
      setUploadedFileName('Live Webcam Feed');
      setErrorMsg(null);
      
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        streamRef.current = stream;
        setWebcamActive(true);
      } catch (err) {
        console.error("Webcam access error:", err);
        setErrorMsg("Unable to access camera. Please check browser permissions.");
      }
    }
  };

  const captureWebcamFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const b64 = canvas.toDataURL('image/jpeg');
    
    setLoading(true);
    const formData = new FormData();
    formData.append('image_b64', b64);
    formData.append('overlay_mode', selectedOverlay);
    api.runAgents(formData).then(res => {
      setPipelineData(res);
      setLoading(false);
    }).catch(err => {
      setErrorMsg("Failed to analyze webcam frame.");
      setLoading(false);
    });
  };

  const sceneAgentOutput = pipelineData?.agent_outputs?.find(a => a.agent_name === "Scene Understanding Agent");
  const autoStrategy = pipelineData?.resolution?.auto_selected_strategy || pipelineData?.resolution?.strategy;
  const selectionReasoning = pipelineData?.resolution?.selection_reasoning || pipelineData?.resolution?.reasoning;

  return (
    <div className="space-y-6">
      {/* Studio Control Header */}
      <div className="p-4 rounded-2xl border border-cyber-border bg-cyber-panel/80 glass-panel flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-cyber-accent/20 text-cyber-accent border border-cyber-accent/40">
            <Camera className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">Autonomous Perception Feed Studio</h2>
            <p className="text-xs text-slate-400 font-mono">
              {uploadedFileName ? `Active Input: ${uploadedFileName}` : 'Select an image, video, or start Live Webcam to begin'}
            </p>
          </div>
        </div>

        {/* Input & Overlay Controls */}
        <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
          {/* Agent Visual Overlay Selector Dropdown */}
          <div className="flex items-center gap-2 bg-cyber-dark px-3 py-2 rounded-xl border border-cyber-border">
            <Eye className="w-4 h-4 text-cyber-accent" />
            <span className="text-slate-400">Overlay:</span>
            <select
              value={selectedOverlay}
              onChange={(e) => handleOverlayChange(e.target.value)}
              className="bg-transparent text-cyber-accent font-bold focus:outline-none cursor-pointer"
            >
              {OVERLAY_OPTIONS.map((mode) => (
                <option key={mode} value={mode} className="bg-cyber-dark text-slate-200">
                  {mode}
                </option>
              ))}
            </select>
          </div>

          {/* File Upload Button */}
          <label className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-cyber-dark border border-cyber-border text-slate-200 hover:text-white hover:border-cyber-accent/50 transition-all cursor-pointer shadow-md">
            <Upload className="w-4 h-4 text-cyber-accent" />
            Upload Image / Video
            <input type="file" accept="image/*,video/*" onChange={handleFileUpload} className="hidden" />
          </label>

          {/* Webcam Toggle Button */}
          <button
            onClick={toggleWebcam}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl border transition-all ${
              webcamActive
                ? 'bg-cyber-danger/20 border-cyber-danger text-cyber-danger font-bold'
                : 'bg-cyber-dark border-cyber-border text-slate-200 hover:text-white'
            }`}
          >
            <Video className="w-4 h-4" />
            {webcamActive ? 'Stop Live Cam' : 'Start Live Cam'}
          </button>

          {/* Trigger Perception Analysis Button */}
          <button
            onClick={() => {
              if (webcamActive) captureWebcamFrame();
              else if (isVideo) captureUploadedVideoFrame();
              else if (uploadedFile) handleRunAgents(uploadedFile);
              else handleRunAgents();
            }}
            disabled={loading || (!uploadedFile && !webcamActive && !previewUrl)}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-cyber-accent text-cyber-dark font-bold hover:bg-cyber-accent/80 transition-all shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Analyze Frame & Resolve
          </button>
        </div>
      </div>

      {/* Error Alert Message */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-cyber-danger/10 border border-cyber-danger/40 text-xs font-mono text-cyber-danger flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Active Conflict Resolution Strategy Info Bar */}
      {pipelineData && autoStrategy && (
        <div className="p-4 rounded-2xl border border-cyber-neon/40 bg-cyber-neon/10 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-white">
            <Sparkles className="w-4 h-4 text-cyber-neon animate-pulse" />
            <span>
              Active Strategy: <strong className="text-cyber-neon uppercase tracking-wider">{autoStrategy}</strong>
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <Info className="w-4 h-4 text-cyber-accent flex-shrink-0" />
            <span className="font-sans italic">{selectionReasoning}</span>
          </div>
        </div>
      )}

      {/* Primary Perception Viewer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Media Display & Agent Visual Overlay */}
        <div className="lg:col-span-7 space-y-4">
          <div
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative rounded-2xl border-2 transition-all duration-300 bg-cyber-dark overflow-hidden shadow-2xl min-h-[480px] lg:min-h-[520px] flex items-center justify-center ${
              isDragging
                ? 'border-cyber-accent bg-cyber-accent/10 scale-[1.01] shadow-cyber-accent/30 ring-4 ring-cyber-accent/20'
                : 'border-cyber-border/80 hover:border-cyber-accent/40'
            }`}
          >
            {/* Drag active overlay label */}
            {isDragging && (
              <div className="absolute inset-0 bg-cyber-dark/90 backdrop-blur-sm z-30 flex flex-col items-center justify-center gap-3 border-2 border-dashed border-cyber-accent text-cyber-accent">
                <UploadCloud className="w-16 h-16 animate-bounce" />
                <h3 className="text-lg font-bold tracking-wider">Drop Image or Video File Here</h3>
                <p className="text-xs text-slate-300 font-mono">Supports JPEG, PNG, MP4, WEBM</p>
              </div>
            )}

            {/* 1. Live Webcam Stream */}
            {webcamActive ? (
              <video
                ref={(node) => {
                  videoRef.current = node;
                  if (node && streamRef.current && node.srcObject !== streamRef.current) {
                    node.srcObject = streamRef.current;
                    node.play().catch(() => {});
                  }
                }}
                autoPlay
                playsInline
                muted
                className="w-full h-[520px] object-cover"
              />
            ) : isVideo && previewUrl ? (
              /* 2. Video Player Preview */
              <div className="relative w-full h-[520px] bg-black">
                <video
                  ref={uploadedVideoRef}
                  src={previewUrl}
                  controls
                  playsInline
                  className="w-full h-full object-contain"
                />
              </div>
            ) : pipelineData?.rendered_image || previewUrl ? (
              /* 3. Rendered Agent Visual Overlay / Uploaded Preview */
              <img
                src={pipelineData?.rendered_image || previewUrl}
                alt="Autonomous Perception Analysis Frame"
                className="w-full h-[520px] object-contain bg-black/40"
              />
            ) : (
              /* 4. Main Screen-Centered Interactive Dropzone Frame */
              <label className="w-full h-full min-h-[480px] lg:min-h-[520px] flex flex-col items-center justify-center p-8 text-center cursor-pointer group space-y-4">
                <div className="w-20 h-20 rounded-3xl bg-cyber-panel border border-cyber-border/80 flex items-center justify-center text-cyber-accent group-hover:scale-110 group-hover:border-cyber-accent/60 group-hover:shadow-lg transition-all duration-300">
                  <UploadCloud className="w-10 h-10 group-hover:text-white transition-colors" />
                </div>
                <div className="space-y-1 max-w-md">
                  <h3 className="text-base font-bold text-white tracking-wide group-hover:text-cyber-accent transition-colors">
                    Drag & Drop Autonomous Road Vision File Here
                  </h3>
                  <p className="text-xs text-slate-400 font-mono">
                    or <span className="text-cyber-accent underline underline-offset-4">click to browse</span> from local disk
                  </p>
                  <p className="text-[11px] text-slate-500 font-mono pt-2">
                    Supports high-resolution road scenes, dashcam videos (MP4), or live camera feed
                  </p>
                </div>
                <input type="file" accept="image/*,video/*" onChange={handleFileUpload} className="hidden" />
              </label>
            )}

            <canvas ref={canvasRef} className="hidden" />

            {/* Badges when media is loaded */}
            {(pipelineData || previewUrl || webcamActive) && (
              <div className="absolute top-3 left-3 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-white/10 text-xs font-mono z-10">
                <span className="w-2 h-2 rounded-full bg-cyber-success animate-ping" />
                <span className="text-slate-200">{webcamActive ? 'LIVE WEBCAM' : (pipelineData ? `OVERLAY: ${selectedOverlay.toUpperCase()}` : 'PREVIEW READY')}</span>
              </div>
            )}

            {/* Video Frame Capture Button */}
            {isVideo && previewUrl && (
              <button
                onClick={() => captureUploadedVideoFrame()}
                className="absolute top-3 right-3 flex items-center gap-1.5 bg-cyber-accent text-cyber-dark px-3 py-1.5 rounded-lg text-xs font-mono font-bold hover:bg-cyber-accent/80 transition-all z-10 shadow-lg"
              >
                <Film className="w-3.5 h-3.5" />
                Capture & Analyze Video Frame
              </button>
            )}

            {/* VisionLLM Rationale Inspector Button */}
            {pipelineData && (
              <button
                onClick={() => setIsVisionLLMOpen(true)}
                className="absolute bottom-3 right-3 flex items-center gap-2 bg-cyber-panel/90 border border-cyber-accent/40 px-3.5 py-2 rounded-xl text-xs font-mono text-cyber-accent hover:bg-cyber-accent hover:text-cyber-dark font-bold transition-all shadow-lg glow-accent z-10"
              >
                <Sparkles className="w-4 h-4" />
                Inspect VisionLLM Rationale
              </button>
            )}
          </div>

          {/* Conflict Detector Panel */}
          {pipelineData && <ConflictViewer conflicts={pipelineData?.conflicts || []} />}
        </div>

        {/* Right Column: Resolution Engine & Decision Authority */}
        <div className="lg:col-span-5 space-y-4">
          <ResolutionEnginePanel
            resolution={pipelineData?.resolution}
            activeStrategy={config.active_strategy}
            supportedStrategies={config.supported_strategies}
            onSelectStrategy={handleStrategySelect}
          />
        </div>
      </div>

      {/* Bottom Grid: 7 Perception & Meta Agents Status Cards */}
      {pipelineData?.agent_outputs && pipelineData.agent_outputs.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-cyber-border/60">
          <h3 className="text-xs font-bold font-mono text-slate-400 uppercase tracking-wider flex items-center gap-2">
            <Layers className="w-4 h-4 text-cyber-accent" />
            INDEPENDENT PERCEPTION & META AGENTS (7 ACTIVE MODULES)
          </h3>
          <AgentStatusCards agentOutputs={pipelineData.agent_outputs} />
        </div>
      )}

      {/* VisionLLM Modal */}
      <VisionLLMModal
        isOpen={isVisionLLMOpen}
        onClose={() => setIsVisionLLMOpen(false)}
        sceneAgentData={sceneAgentOutput}
        modelName={config.vision_model}
      />
    </div>
  );
}
