import axios from 'axios';
import {
  User,
  Report,
  Issue,
  WorkOrder,
  Notification,
  DuplicateMatch,
} from '@/types';

const rawBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').trim().replace(/\/+$/, '');
const API_BASE = rawBase.endsWith('/api/v1') ? rawBase : `${rawBase}/api/v1`;

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('civicfix_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('civicfix_token');
      localStorage.removeItem('civicfix_user');
    }
    return Promise.reject(error);
  }
);

// --- Auth APIs ---
export const authApi = {
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/auth/login', { email, password });
    return res.data;
  },
  register: async (data: { email: string; password: string; full_name: string; phone?: string; phone_number?: string; role?: string }) => {
    const payload = {
      ...data,
      phone: data.phone || data.phone_number,
      phone_number: data.phone_number || data.phone,
    };
    const res = await apiClient.post('/auth/register', payload);
    return res.data;
  },
  me: async (): Promise<User> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// --- Report APIs ---
export const reportApi = {
  create: async (data: {
    title: string;
    description: string;
    category?: string;
    priority?: string;
    latitude: number;
    longitude: number;
    address?: string;
    image?: File | null;
    image_url?: string;
  }) => {
    if (data.image) {
      const formData = new FormData();
      formData.append('title', data.title);
      formData.append('description', data.description);
      if (data.category) formData.append('category', data.category);
      if (data.priority) formData.append('priority', data.priority);
      formData.append('latitude', data.latitude.toString());
      formData.append('longitude', data.longitude.toString());
      if (data.address) formData.append('address', data.address);
      formData.append('image', data.image);

      const res = await apiClient.post('/reports/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    }

    const res = await apiClient.post('/reports/', data);
    return res.data;
  },
  list: async (params?: { status?: string; category?: string; user_id?: number; priority?: string }): Promise<Report[]> => {
    const res = await apiClient.get('/reports/', { params });
    return res.data;
  },
  getById: async (id: string | number): Promise<Report> => {
    const res = await apiClient.get(`/reports/${id}`);
    return res.data;
  },
  getNearby: async (lat: number, lng: number, radiusKm: number = 2.0): Promise<Report[]> => {
    const res = await apiClient.get('/reports/nearby', {
      params: { latitude: lat, longitude: lng, radius_km: radiusKm },
    });
    return res.data;
  },
  upvote: async (id: string | number) => {
    const res = await apiClient.post(`/reports/${id}/upvote`);
    return res.data;
  },
  updateStatus: async (id: string | number, status: string, issueId?: number) => {
    const res = await apiClient.patch(`/reports/${id}/status`, null, {
      params: { status, issue_id: issueId },
    });
    return res.data;
  },
};

// --- Issue APIs ---
export const issueApi = {
  list: async (params?: { category?: string; status?: string; priority?: string; department_id?: number }): Promise<Issue[]> => {
    const res = await apiClient.get('/issues/', { params });
    return res.data;
  },
  getById: async (id: string | number): Promise<Issue> => {
    const res = await apiClient.get(`/issues/${id}`);
    return res.data;
  },
  create: async (data: any, initialReportId?: number) => {
    const res = await apiClient.post('/issues/', data, {
      params: initialReportId ? { initial_report_id: initialReportId } : undefined,
    });
    return res.data;
  },
  update: async (id: string | number, data: any) => {
    const res = await apiClient.patch(`/issues/${id}`, data);
    return res.data;
  },
  updateStatus: async (id: string | number, status: string) => {
    const res = await apiClient.patch(`/issues/${id}/status`, null, {
      params: { status },
    });
    return res.data;
  },
  mergeReport: async (issueId: string | number, reportId: string | number) => {
    const res = await apiClient.post(`/issues/${issueId}/merge-report/${reportId}`);
    return res.data;
  },
};

// --- Work Order APIs ---
export const workOrderApi = {
  list: async (params?: { status?: string; assigned_to_id?: number; department_id?: number }): Promise<WorkOrder[]> => {
    const res = await apiClient.get('/work-orders/', { params });
    return res.data;
  },
  getById: async (id: string | number): Promise<WorkOrder> => {
    const res = await apiClient.get(`/work-orders/${id}`);
    return res.data;
  },
  create: async (data: {
    issue_id: number;
    title: string;
    description?: string;
    priority?: string;
    assigned_to_id?: number;
    department_id?: number;
    estimated_hours?: number;
    due_date?: string;
  }) => {
    const res = await apiClient.post('/work-orders/', data);
    return res.data;
  },
  update: async (id: string | number, data: any) => {
    const res = await apiClient.patch(`/work-orders/${id}`, data);
    return res.data;
  },
  updateStatus: async (id: string | number, status: string) => {
    const res = await apiClient.patch(`/work-orders/${id}/status`, null, {
      params: { status },
    });
    return res.data;
  },
  uploadBeforePhoto: async (id: string | number, file: File) => {
    const formData = new FormData();
    formData.append('image', file);
    const res = await apiClient.post(`/work-orders/${id}/before-photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  uploadAfterPhoto: async (id: string | number, file: File) => {
    const formData = new FormData();
    formData.append('image', file);
    const res = await apiClient.post(`/work-orders/${id}/after-photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
  reportBlocked: async (id: string | number, reason: string, notes?: string, file?: File) => {
    const formData = new FormData();
    formData.append('reason', reason);
    if (notes) formData.append('notes', notes);
    if (file) formData.append('image', file);
    const res = await apiClient.post(`/work-orders/${id}/report-blocked`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

// --- Analytics APIs ---
export const analyticsApi = {
  getDashboard: async () => {
    const res = await apiClient.get('/analytics/dashboard');
    return res.data;
  },
  getResolutionTimes: async () => {
    const res = await apiClient.get('/analytics/resolution-times');
    return res.data;
  },
  getHeatmap: async () => {
    const res = await apiClient.get('/analytics/heatmap');
    return res.data;
  },
};

// --- AI Assistant API ---
export const assistantApi = {
  chat: async (prompt: string, contextReportId?: number) => {
    const res = await apiClient.post('/ai-assistant/chat', {
      prompt,
      context_report_id: contextReportId,
    });
    return res.data;
  },
  triage: async (data: {
    title: string;
    description: string;
    latitude: number;
    longitude: number;
  }) => {
    const res = await apiClient.post('/ai-assistant/triage', data);
    return res.data;
  },
  triageImage: async (file: File, notes?: string) => {
    const formData = new FormData();
    formData.append('image', file);
    if (notes) formData.append('notes', notes);
    const res = await apiClient.post('/ai-assistant/triage-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

// --- Notifications API ---
export const notificationApi = {
  list: async (unreadOnly: boolean = false): Promise<Notification[]> => {
    const res = await apiClient.get('/notifications/', {
      params: { unread_only: unreadOnly },
    });
    return res.data;
  },
  markRead: async (id: string | number) => {
    const res = await apiClient.patch(`/notifications/${id}/read`);
    return res.data;
  },
  markAllRead: async () => {
    const res = await apiClient.post('/notifications/read-all');
    return res.data;
  },
};

// --- Service Request APIs ---
export const serviceRequestApi = {
  list: async () => {
    const res = await apiClient.get('/service-requests/');
    return res.data;
  },
  createFromIssue: async (issueId: number, reportedById?: number) => {
    const res = await apiClient.post('/service-requests/', {
      issue_id: issueId,
      reported_by_id: reportedById ?? null,
    });
    return res.data;
  },
  updateStatus: async (srId: number, status: string, notes?: string) => {
    const res = await apiClient.post(`/service-requests/${srId}/status`, { status, notes });
    return res.data;
  },
};
