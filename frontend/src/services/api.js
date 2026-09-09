import axios from 'axios';

const API_BASE = '/api';

export const api = {
  getConfig: () => axios.get(`${API_BASE}/config`).then(res => res.data),
  updateConfig: (data) => axios.post(`${API_BASE}/config`, data).then(res => res.data),
  runAgents: (formData) => axios.post(`${API_BASE}/run_agents`, formData).then(res => res.data),
  uploadImage: (file, overlayMode = "YOLO Agent Active") => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('overlay_mode', overlayMode);
    return axios.post(`${API_BASE}/upload`, formData).then(res => res.data);
  },
  runConflictResolution: (payload) => axios.post(`${API_BASE}/run_conflict_resolution`, payload).then(res => res.data),
  evaluateImageStrategies: (payload) => axios.post(`${API_BASE}/evaluate_image_strategies`, payload).then(res => res.data),
  getMetrics: () => axios.get(`${API_BASE}/get_metrics`).then(res => res.data),
  getExperiments: () => axios.get(`${API_BASE}/experiments`).then(res => res.data),
  triggerBenchmark: (numFrames = 15) => axios.post(`${API_BASE}/experiments/run?num_frames=${numFrames}`).then(res => res.data),
  trainYolo: (epochs = 3) => axios.post(`${API_BASE}/train?epochs=${epochs}`).then(res => res.data),
  getHistory: () => axios.get(`${API_BASE}/history`).then(res => res.data),
  exportData: () => axios.get(`${API_BASE}/export`).then(res => res.data)
};
