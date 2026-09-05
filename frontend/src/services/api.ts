import axios from 'axios';
import type {
  TokenResponse, User, Dataset, Ticket, AnalyticsResponse,
  AnalyticsFilters, FilterOptions, AIInsight, CommonIssue, Analysis,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  register: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/register', { email, password }).then(r => r.data),
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }).then(r => r.data),
  me: () => api.get<User>('/auth/me').then(r => r.data),
};

export const datasetsAPI = {
  list: () => api.get<{ datasets: Dataset[]; total: number }>('/datasets').then(r => r.data),
  get: (id: number) => api.get<Dataset>(`/datasets/${id}`).then(r => r.data),
  delete: (id: number) => api.delete(`/datasets/${id}`),
  upload: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ dataset: Dataset; message: string; rows_processed: number; warnings: string[] }>(
      '/datasets/upload', formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    ).then(r => r.data);
  },
  loadSample: () => api.post<{ dataset: Dataset; message: string; rows_processed: number }>('/datasets/sample').then(r => r.data),
};

export const analyticsAPI = {
  get: (datasetId: number, filters?: AnalyticsFilters) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([k, v]) => {
        if (v) params.append(k, v);
      });
    }
    return api.get<AnalyticsResponse>(`/datasets/${datasetId}/analytics`, { params }).then(r => r.data);
  },
  getFilters: (datasetId: number) =>
    api.get<FilterOptions>(`/datasets/${datasetId}/analytics/filters`).then(r => r.data),
};

export const ticketsAPI = {
  list: (datasetId: number, params: Record<string, string | number> = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') searchParams.append(k, String(v));
    });
    return api.get<{ tickets: Ticket[]; total: number; page: number; page_size: number }>(
      `/datasets/${datasetId}/tickets`, { params: searchParams }
    ).then(r => r.data);
  },
  get: (ticketId: number) => api.get<Ticket>(`/tickets/${ticketId}`).then(r => r.data),
};

export const aiAPI = {
  summarizeTicket: (ticketId: number) =>
    api.post<{ summary: string; available: boolean; message?: string }>(
      `/tickets/${ticketId}/summarize`
    ).then(r => r.data),
  getInsights: (datasetId: number) =>
    api.post<{ insights: AIInsight[]; summary: string; available: boolean; message?: string }>(
      `/datasets/${datasetId}/ai/insights`
    ).then(r => r.data),
  getCommonIssues: (datasetId: number) =>
    api.post<{ issues: CommonIssue[]; available: boolean }>(
      `/datasets/${datasetId}/ai/common-issues`
    ).then(r => r.data),
  askQuestion: (datasetId: number, question: string) =>
    api.post<{ question: string; answer: string; calculated_facts: Record<string, unknown>; available: boolean; message?: string }>(
      `/datasets/${datasetId}/ai/ask`, { question }
    ).then(r => r.data),
};

export const historyAPI = {
  list: () => api.get<{ analyses: Analysis[]; total: number }>('/analyses').then(r => r.data),
  create: (datasetId: number, name: string) =>
    api.post<Analysis>('/analyses', { dataset_id: datasetId, analysis_name: name }).then(r => r.data),
  get: (id: number) => api.get<Analysis>(`/analyses/${id}`).then(r => r.data),
  delete: (id: number) => api.delete(`/analyses/${id}`),
};

export default api;
