import React, { useState, useEffect } from 'react';
import { BarChart2, Shield, Zap, TrendingUp, RefreshCw, FileText, CheckCircle2, AlertTriangle, Image as ImageIcon, Cpu, Award } from 'lucide-react';
import { api } from '../services/api';

export default function ExperimentBenchmark({ pipelineData }) {
  const [evalData, setEvalData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (pipelineData && pipelineData.agent_outputs) {
      runImageEvaluation(pipelineData);
    } else {
      setEvalData(null);
    }
  }, [pipelineData]);

  const runImageEvaluation = async (pData) => {
    setLoading(true);
    try {
      const res = await api.evaluateImageStrategies({
        agent_outputs: pData.agent_outputs || [],
        conflicts: pData.conflicts || []
      });
      setEvalData(res);
    } catch (err) {
      console.error("Failed to evaluate image strategies", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = () => {
    if (!pipelineData) return;
    const filename = pipelineData.filename || 'Uploaded Image';
    const strategyResults = evalData?.strategy_results || [];
    const agentOutputs = pipelineData.agent_outputs || [];

    // Build base64 image src — support both raw base64 and full data URIs
    const rawImg = pipelineData.rendered_image || pipelineData.image_b64 || pipelineData.image || '';
    let imgSrc = '';
    if (rawImg) {
      imgSrc = rawImg.startsWith('data:') ? rawImg : `data:image/jpeg;base64,${rawImg}`;
    }

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Multi-Vision Benchmark Report — ${filename}</title>
          <style>
            @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Helvetica Neue', Arial, sans-serif; padding: 32px; color: #1e293b; background: #ffffff; font-size: 12px; }
            .report-header { display: flex; align-items: flex-start; justify-content: space-between; border-bottom: 3px solid #cc0000; padding-bottom: 14px; margin-bottom: 20px; }
            .report-title h1 { color: #cc0000; font-size: 22px; font-weight: 900; letter-spacing: 1px; margin-bottom: 4px; }
            .report-title p { color: #64748b; font-size: 11px; }
            .logo-badge { background: #1e2430; color: #ffffff; padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 11px; letter-spacing: 2px; }
            .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; align-items: start; }
            .image-section { border: 1px solid #cbd5e1; border-radius: 10px; overflow: hidden; background: #0f172a; }
            .image-section .img-label { background: #1e2430; color: #94a3b8; font-size: 9px; font-weight: bold; letter-spacing: 2px; padding: 6px 12px; text-transform: uppercase; }
            .image-section img { width: 100%; height: auto; display: block; max-height: 280px; object-fit: cover; }
            .image-section .no-image { padding: 40px; text-align: center; color: #94a3b8; font-size: 11px; }
            .meta-section { display: flex; flex-direction: column; gap: 10px; }
            .meta-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; }
            .meta-card label { display: block; font-size: 9px; color: #94a3b8; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }
            .meta-card .val { font-size: 13px; font-weight: 800; color: #1e293b; }
            .meta-card .val.red { color: #cc0000; }
            .meta-card .val.green { color: #16a34a; }
            h3 { font-size: 13px; font-weight: 800; color: #1e293b; letter-spacing: 0.5px; margin-bottom: 10px; border-left: 3px solid #cc0000; padding-left: 8px; }
            table { width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 20px; }
            th, td { border: 1px solid #e2e8f0; padding: 7px 10px; text-align: left; }
            th { background: #1e2430; color: #ffffff; font-weight: 700; font-size: 10px; letter-spacing: 0.5px; }
            tr:nth-child(even) td { background: #f8fafc; }
            .badge-go { background: #dcfce7; color: #166534; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 10px; }
            .badge-slow { background: #fef9c3; color: #854d0e; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 10px; }
            .badge-stop { background: #fee2e2; color: #cc0000; padding: 2px 7px; border-radius: 4px; font-weight: bold; font-size: 10px; }
            .agent-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 20px; }
            .agent-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; }
            .agent-card .agent-name { font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
            .agent-card .decision { font-size: 11px; font-weight: 800; color: #cc0000; }
            .agent-card .conf { font-size: 10px; color: #64748b; margin-top: 2px; }
            .conf-bar-bg { background: #e2e8f0; border-radius: 4px; height: 5px; margin-top: 6px; overflow: hidden; }
            .conf-bar { height: 5px; border-radius: 4px; background: #cc0000; }
            .footer { margin-top: 24px; font-size: 9px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 12px; }
          </style>
        </head>
        <body>
          <div class="report-header">
            <div class="report-title">
              <h1>MULTI-VISION BENCHMARK REPORT</h1>
              <p>Multi-Agent Conflict Arbitration — Autonomous Perception Analysis</p>
            </div>
            <div class="logo-badge">MULTI-VISION v1.0</div>
          </div>

          <div class="two-col">
            <!-- LEFT: Analysed Frame Image -->
            <div class="image-section">
              <div class="img-label">📷 Analysed Perception Frame</div>
              ${imgSrc
                ? `<img src="${imgSrc}" alt="Analysed Frame: ${filename}" />`
                : `<div class="no-image">No rendered frame available</div>`
              }
            </div>

            <!-- RIGHT: Meta Info Cards -->
            <div class="meta-section">
              <div class="meta-card">
                <label>Frame / File Name</label>
                <div class="val">${filename}</div>
              </div>
              <div class="meta-card">
                <label>Consensus Action</label>
                <div class="val red">${evalData?.top_action || pipelineData?.resolution?.final_decision || 'N/A'}</div>
              </div>
              <div class="meta-card">
                <label>Consensus Strength</label>
                <div class="val">${evalData?.consensus_pct || 0}%</div>
              </div>
              <div class="meta-card">
                <label>Active Agents</label>
                <div class="val">${agentOutputs.length} Perception Models</div>
              </div>
              <div class="meta-card">
                <label>Report Generated</label>
                <div class="val" style="font-size:11px">${new Date().toLocaleString()}</div>
              </div>
            </div>
          </div>

          <!-- Agent Decisions Grid -->
          ${agentOutputs.length > 0 ? `
          <h3>Agent Perception Outputs</h3>
          <div class="agent-grid">
            ${agentOutputs.map(a => `
              <div class="agent-card">
                <div class="agent-name">${a.agent_name}</div>
                <div class="decision">${a.decision}</div>
                <div class="conf">${((a.confidence || 0) * 100).toFixed(0)}% confidence &nbsp;|&nbsp; ${a.latency_ms || 0} ms</div>
                <div class="conf-bar-bg"><div class="conf-bar" style="width:${Math.round((a.confidence || 0) * 100)}%"></div></div>
              </div>
            `).join('')}
          </div>` : ''}

          <!-- 10-Strategy Table -->
          <h3>10-Strategy Comparative Benchmark Results</h3>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Strategy Name</th>
                <th>Final Decision</th>
                <th>Confidence</th>
                <th>Winning Agent</th>
                <th>Latency (ms)</th>
              </tr>
            </thead>
            <tbody>
              ${strategyResults.map((st, i) => `
                <tr>
                  <td>${i + 1}</td>
                  <td><strong>${st.strategy}</strong></td>
                  <td><span class="${st.final_decision === 'GO' ? 'badge-go' : st.final_decision === 'SLOW DOWN' ? 'badge-slow' : 'badge-stop'}">${st.final_decision}</span></td>
                  <td>${((st.confidence || 0) * 100).toFixed(1)}%</td>
                  <td>${st.winning_agent || 'Ensemble'}</td>
                  <td>${st.resolution_time_ms} ms</td>
                </tr>
              `).join('')}
            </tbody>
          </table>

          <div class="footer">
            MULTI-VISION Autonomous Vision Multi-Agent System &nbsp;|&nbsp; Research Platform v1.0 &nbsp;|&nbsp; Conflict Resolution Strategies in Multi-Agent Vision Systems
          </div>

          <script>window.onload = function() { window.print(); }<\/script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // If no image uploaded yet
  if (!pipelineData || !pipelineData.agent_outputs) {
    return (
      <div className="space-y-6">
        <div className="p-8 rounded-2xl border border-[#2d3748] bg-[#1e2430] text-center space-y-4 max-w-2xl mx-auto my-12 shadow-xl">
          <div className="w-14 h-14 rounded-2xl bg-[#cc0000]/10 border border-[#cc0000]/30 flex items-center justify-center mx-auto text-[#cc0000]">
            <ImageIcon className="w-7 h-7" />
          </div>
          <h2 className="text-lg font-bold text-[#f8fafc] font-mono">
            No Image Uploaded for Benchmark Analysis
          </h2>
          <p className="text-xs text-[#94a3b8] font-mono leading-relaxed">
            Upload or select an image on the <strong className="text-[#cc0000]">Perception Dashboard</strong> tab first. Once an image is uploaded, this page will automatically display its complete multi-agent perception graphs, confidence metrics, and 10-strategy comparative evaluation benchmarks.
          </p>
        </div>
      </div>
    );
  }

  const agentOutputs = pipelineData.agent_outputs || [];
  const conflicts = pipelineData.conflicts || [];
  const strategyResults = evalData?.strategy_results || [];
  const actionCounts = evalData?.action_counts || {};

  const getActionColor = (act) => {
    if (act === "GO" || act === "PROCEED") return "text-[#00e676] bg-[#00e676]/10 border-[#00e676]/40";
    if (act === "SLOW DOWN") return "text-[#ffb300] bg-[#ffb300]/10 border-[#ffb300]/40";
    return "text-[#cc0000] bg-[#cc0000]/10 border-[#cc0000]/40";
  };

  const getActionBarColor = (act) => {
    if (act === "GO" || act === "PROCEED") return "bg-[#00e676]";
    if (act === "SLOW DOWN") return "bg-[#ffb300]";
    return "bg-[#cc0000]";
  };

  return (
    <div className="space-y-6">
      {/* Header Banner for Uploaded Image */}
      <div className="p-5 rounded-2xl border border-[#2d3748] bg-[#1e2430] flex flex-wrap items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-4">
          {pipelineData.rendered_image && (
            <img
              src={pipelineData.rendered_image}
              alt="Uploaded Frame"
              className="w-16 h-16 rounded-xl object-cover border border-[#2d3748] shadow-md"
            />
          )}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold bg-[#cc0000]/20 text-[#cc0000] px-2 py-0.5 rounded-md border border-[#cc0000]/30 uppercase">
                MOST RECENT UPLOAD
              </span>
              <span className="text-xs font-mono text-[#94a3b8] truncate max-w-xs">{pipelineData.filename || 'Uploaded Frame'}</span>
            </div>
            <h2 className="text-base font-bold text-[#f8fafc] font-mono mt-1 flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-[#cc0000]" />
              Uploaded Image Strategy Benchmark & Analytics
            </h2>
            <p className="text-xs text-[#94a3b8] font-mono">
              6 Perception Agents • {conflicts.length} Conflict(s) Identified • {evalData?.consensus_pct || 0}% Strategy Consensus on <strong className="text-[#f8fafc]">{evalData?.top_action || 'GO'}</strong>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => runImageEvaluation(pipelineData)}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#cc0000] text-white font-bold text-xs hover:brightness-110 transition-all shadow-md disabled:opacity-50 font-mono"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Re-evaluate Image
          </button>

          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#161b26] border border-[#2d3748] text-[#f8fafc] hover:border-[#cc0000] font-bold text-xs transition-all font-mono"
          >
            <FileText className="w-4 h-4 text-[#00e676]" />
            Export Image Report PDF
          </button>
        </div>
      </div>

      {/* Overview Cards for this Image */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-[#1e2430] border border-[#2d3748] space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#94a3b8] uppercase font-bold tracking-widest">Consensus Action</span>
          <p className={`text-xl font-black font-mono px-2.5 py-0.5 rounded-lg border w-fit ${getActionColor(evalData?.top_action)}`}>
            {evalData?.top_action || "PROCEED"}
          </p>
          <span className="text-[11px] text-[#94a3b8] font-mono">{evalData?.consensus_pct || 0}% Algorithm Agreement</span>
        </div>
        <div className="p-4 rounded-xl bg-[#1e2430] border border-[#2d3748] space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#94a3b8] uppercase font-bold tracking-widest">Perception Agents</span>
          <p className="text-xl font-black text-[#f8fafc] font-mono">{agentOutputs.length} Agents</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Object, Lane, Traffic Rule, Scene, Risk</span>
        </div>
        <div className="p-4 rounded-xl bg-[#1e2430] border border-[#2d3748] space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#94a3b8] uppercase font-bold tracking-widest">Conflicts Identified</span>
          <p className="text-xl font-black text-[#cc0000] font-mono">{conflicts.length} Conflicts</p>
          <span className="text-[11px] text-[#94a3b8] font-mono">{conflicts.length === 0 ? "Unanimous Perception" : "Arbitrated by Rules"}</span>
        </div>
        <div className="p-4 rounded-xl bg-[#1e2430] border border-[#2d3748] space-y-1 shadow-lg">
          <span className="text-[10px] font-mono text-[#94a3b8] uppercase font-bold tracking-widest">Fastest Resolution</span>
          <p className="text-xl font-black text-[#00e676] font-mono">
            {strategyResults.slice().sort((a,b) => (a.resolution_time_ms||0) - (b.resolution_time_ms||0))[0]?.resolution_time_ms || 0.1} ms
          </p>
          <span className="text-[11px] text-[#94a3b8] font-mono">Sub-millisecond inference</span>
        </div>
      </div>

      {/* Visual Graphs Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* GRAPH 1: 10-Strategy Decision & Confidence Comparison */}
        <div className="p-5 rounded-2xl border border-[#2d3748] bg-[#1e2430] space-y-4 shadow-xl">
          <h3 className="text-xs font-bold text-[#f8fafc] tracking-wider font-mono flex items-center gap-2 uppercase">
            <Cpu className="w-4 h-4 text-[#cc0000]" />
            10-STRATEGY CONFIDENCE & DECISION COMPARISON (THIS IMAGE)
          </h3>

          <div className="space-y-3 pt-2">
            {strategyResults.map((st, idx) => {
              const confPct = Math.round((st.confidence || 0) * 100);
              const barColor = getActionBarColor(st.final_decision);
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="text-[#f8fafc] font-bold truncate max-w-[200px]">{st.strategy}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${getActionColor(st.final_decision)}`}>
                        {st.final_decision}
                      </span>
                      <span className="text-[#cc0000] font-bold">{confPct}%</span>
                    </div>
                  </div>
                  <div className="w-full bg-[#161b26] rounded-full h-2.5 overflow-hidden border border-[#2d3748]">
                    <div
                      className={`h-2.5 rounded-full ${barColor} transition-all duration-500`}
                      style={{ width: `${confPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* GRAPH 2: 6 Perception Agents Confidence & Latency */}
        <div className="p-5 rounded-2xl border border-[#2d3748] bg-[#1e2430] space-y-4 shadow-xl">
          <h3 className="text-xs font-bold text-[#f8fafc] tracking-wider font-mono flex items-center gap-2 uppercase">
            <Zap className="w-4 h-4 text-[#ffb300]" />
            PERCEPTION AGENT CONFIDENCE & LATENCY (THIS IMAGE)
          </h3>

          <div className="space-y-4 pt-2">
            {agentOutputs.map((agent, idx) => {
              const confPct = Math.round((agent.confidence || 0) * 100);
              return (
                <div key={idx} className="bg-[#161b26] p-3 rounded-xl border border-[#2d3748] space-y-2">
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="font-bold text-[#f8fafc] truncate">{agent.agent_name}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-[#94a3b8] text-[11px]">{agent.latency_ms} ms</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${getActionColor(agent.proposed_action)}`}>
                        {agent.proposed_action}
                      </span>
                      <span className="text-[#00e676] font-bold">{confPct}%</span>
                    </div>
                  </div>
                  <div className="w-full bg-[#1e2430] rounded-full h-2 overflow-hidden border border-[#2d3748]">
                    <div
                      className="h-2 rounded-full bg-[#00e676] transition-all duration-500"
                      style={{ width: `${confPct}%` }}
                    />
                  </div>
                  {agent.reasoning && (
                    <p className="text-[10px] font-mono text-[#94a3b8] truncate">{agent.reasoning}</p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* GRAPH 3: Consensus Voting Breakdown & Strategy Table */}
      <div className="p-5 rounded-2xl border border-[#2d3748] bg-[#1e2430] space-y-4 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h3 className="text-sm font-bold text-[#f8fafc] tracking-wider font-mono flex items-center gap-2 uppercase">
            <Award className="w-4 h-4 text-[#cc0000]" />
            10-STRATEGY COMPARATIVE MATRIX FOR UPLOADED IMAGE
          </h3>
          <div className="flex items-center gap-2">
            {Object.entries(actionCounts).map(([act, count]) => (
              <span key={act} className={`text-xs font-mono px-2.5 py-1 rounded-lg border font-bold ${getActionColor(act)}`}>
                {act}: {count} strategy votes
              </span>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono border-collapse">
            <thead>
              <tr className="border-b border-[#2d3748] text-[#94a3b8] bg-[#161b26]">
                <th className="p-3">Strategy Name</th>
                <th className="p-3">Final Decision</th>
                <th className="p-3">Confidence</th>
                <th className="p-3">Winning Agent</th>
                <th className="p-3">Latency</th>
                <th className="p-3">Mathematical Reasoning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2d3748] text-[#94a3b8]">
              {strategyResults.map((st, idx) => (
                <tr key={idx} className="hover:bg-[#161b26] transition-all">
                  <td className="p-3 font-bold text-[#cc0000]">{st.strategy}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getActionColor(st.final_decision)}`}>
                      {st.final_decision}
                    </span>
                  </td>
                  <td className="p-3 font-bold text-[#f8fafc]">{((st.confidence || 0) * 100).toFixed(1)}%</td>
                  <td className="p-3 text-[#94a3b8]">{st.winning_agent || 'N/A'}</td>
                  <td className="p-3 text-[#ffb300] font-bold">{st.resolution_time_ms} ms</td>
                  <td className="p-3 text-[#94a3b8] text-[11px] max-w-xs truncate">{st.reasoning || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

