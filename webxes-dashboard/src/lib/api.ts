import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT to all requests
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('webxes_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-redirect on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('webxes_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const login = (password: string) =>
  api.post('/api/auth/login', { password });

export const checkAuth = () => api.get('/api/auth/me');

// Dashboard
export const getDashboardStats = () => api.get('/api/dashboard/stats');

// Inbox
export const getInbox = (params?: Record<string, string | number>) =>
  api.get('/api/inbox', { params });

export const getInboxItem = (id: string) => api.get(`/api/inbox/${id}`);

// Approvals
export const getApprovals = (params?: Record<string, string | number>) =>
  api.get('/api/approvals', { params });

export const getApproval = (id: string) => api.get(`/api/approvals/${id}`);

export const updateApprovalContent = (id: string, content: string) =>
  api.put(`/api/approvals/${id}/content`, { content });

export const approveItem = (id: string, note?: string) =>
  api.post(`/api/approvals/${id}/approve`, { note: note || '' });

export const rejectItem = (id: string, note?: string) =>
  api.post(`/api/approvals/${id}/reject`, { note: note || '' });

// Audit
export const getAuditEvents = (params?: Record<string, string | number>) =>
  api.get('/api/audit', { params });

export const getAuditSummary = (params?: Record<string, string>) =>
  api.get('/api/audit/summary', { params });

// Settings
export const getSettings = () => api.get('/api/settings');

export const toggleDryRun = (enabled: boolean) =>
  api.put('/api/settings/dry-run', { enabled });

export default api;
