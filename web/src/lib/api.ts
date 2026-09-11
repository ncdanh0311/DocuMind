import axios from 'axios';
import { Notebook, DocumentItem, User, NotificationItem } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Helper for Token Management (matching mobile's secure storage)
export const tokenManager = {
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  },
  setTokens(accessToken: string, refreshToken?: string, fullName?: string) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
    if (fullName) localStorage.setItem('full_name', fullName);
  },
  clearAuth() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('full_name');
  },
};

// Request Interceptor: Attach Bearer Token
apiClient.interceptors.request.use((config) => {
  const token = tokenManager.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Auto-refresh token on 401 (matching mobile _sendWithAuthRetry)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = tokenManager.getRefreshToken();
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_BASE_URL}/auth/refresh-token`, {
            refresh_token: refreshToken,
          });
          if (res.data?.access_token) {
            tokenManager.setTokens(res.data.access_token, res.data.refresh_token);
            originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`;
            return apiClient(originalRequest);
          }
        } catch {
          tokenManager.clearAuth();
          if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
            window.location.href = '/login';
          }
        }
      }
    }
    return Promise.reject(error);
  }
);

// Fallback category icon resolver matching mobile's _getCategoryIcon
export function getCategoryIcon(title: string, iconPath?: string): string {
  if (iconPath && iconPath.startsWith('/assets')) return iconPath;
  const t = title.toLowerCase();
  if (t.includes('toán') || t.includes('học') || t.includes('study') || t.includes('giải tích')) {
    return '/assets/icons/categories/icon-category-study.png';
  }
  if (t.includes('dự án') || t.includes('project') || t.includes('app') || t.includes('web')) {
    return '/assets/icons/categories/icon-category-project.png';
  }
  if (t.includes('nghiên cứu') || t.includes('research') || t.includes('deep learning') || t.includes('ai')) {
    return '/assets/icons/categories/icon-category-research.png';
  }
  return '/assets/icons/categories/icon-category-personal.png';
}

// Fallback category type
export function getCategoryType(title: string): 'study' | 'project' | 'research' | 'personal' {
  const t = title.toLowerCase();
  if (t.includes('toán') || t.includes('học') || t.includes('study')) return 'study';
  if (t.includes('dự án') || t.includes('project')) return 'project';
  if (t.includes('nghiên cứu') || t.includes('deep learning') || t.includes('ai')) return 'research';
  return 'personal';
}

// Fallback Mock Data for smooth rendering and offline preview
export const MOCK_NOTEBOOKS: Notebook[] = [
  {
    notebook_id: 'nb-1',
    id: 'nb-1',
    title: 'Toán Cao Cấp & Giải Tích',
    category: 'study',
    color: '#E6F7F1',
    icon: '/assets/icons/categories/icon-category-study.png',
    count: 6,
    show_on_home: true,
    created_at: '2026-09-08T09:00:00Z',
  },
  {
    notebook_id: 'nb-2',
    id: 'nb-2',
    title: 'Học Máy & Deep Learning',
    category: 'research',
    color: '#FFE1E6',
    icon: '/assets/icons/categories/icon-category-research.png',
    count: 12,
    show_on_home: true,
    created_at: '2026-09-07T14:30:00Z',
  },
  {
    notebook_id: 'nb-3',
    id: 'nb-3',
    title: 'Dự án DocuMind AI',
    category: 'project',
    color: '#D6F0FF',
    icon: '/assets/icons/categories/icon-category-project.png',
    count: 8,
    show_on_home: true,
    created_at: '2026-09-06T11:20:00Z',
  },
  {
    notebook_id: 'nb-4',
    id: 'nb-4',
    title: 'Ghi chú nghiên cứu cá nhân',
    category: 'personal',
    color: '#FFE9B3',
    icon: '/assets/icons/categories/icon-category-personal.png',
    count: 4,
    show_on_home: true,
    created_at: '2026-09-05T16:00:00Z',
  },
];

export const MOCK_RECENT_DOCUMENTS: DocumentItem[] = [
  {
    document_id: 'doc-1',
    id: 'doc-1',
    notebook_id: 'nb-2',
    notebook_title: 'Học Máy & Deep Learning',
    file_name: 'Kien_truc_Transformer_va_Attention.pdf',
    title: 'Kien_truc_Transformer_va_Attention.pdf',
    file_type: 'pdf',
    file_size: 4200000,
    status: 'ready',
    uploaded_at: '2026-09-10T08:30:00Z',
    page_count: 24,
  },
  {
    document_id: 'doc-2',
    id: 'doc-2',
    notebook_id: 'nb-1',
    notebook_title: 'Toán Cao Cấp & Giải Tích',
    file_name: 'Giao_trinh_Giai_tich_Ham_Nhieu_Bien.pdf',
    title: 'Giao_trinh_Giai_tich_Ham_Nhieu_Bien.pdf',
    file_type: 'pdf',
    file_size: 6100000,
    status: 'ready',
    uploaded_at: '2026-09-09T15:45:00Z',
    page_count: 58,
  },
  {
    document_id: 'doc-3',
    id: 'doc-3',
    notebook_id: 'nb-3',
    notebook_title: 'Dự án DocuMind AI',
    file_name: 'Tai_lieu_Thiet_ke_He_thong_DocuMind.docx',
    title: 'Tai_lieu_Thiet_ke_He_thong_DocuMind.docx',
    file_type: 'docx',
    file_size: 2800000,
    status: 'processing',
    uploaded_at: '2026-09-10T12:15:00Z',
    page_count: 14,
  },
];

// --- API SERVICES (Matching mobile ApiService 1:1) ---
export const apiService = {
  // 1. AUTH
  async login(email: string, password: string) {
    const res = await apiClient.post('/auth/login', { email, password });
    if (res.data?.access_token) {
      tokenManager.setTokens(res.data.access_token, res.data.refresh_token, res.data.full_name);
    }
    return res.data;
  },

  async register(email: string, password: string, full_name?: string) {
    const res = await apiClient.post('/auth/register', { email, password, full_name });
    if (res.data?.access_token) {
      tokenManager.setTokens(res.data.access_token, res.data.refresh_token, res.data.full_name);
    }
    return res.data;
  },

  async logout() {
    try {
      await apiClient.post('/auth/logout');
    } catch {}
    tokenManager.clearAuth();
  },

  async getProfile(): Promise<User> {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  async updateProfile(data: { full_name?: string; avatar_id?: string }) {
    const res = await apiClient.put('/auth/me', data);
    return res.data;
  },

  async updateSecurity(data: { old_password?: string; new_password?: string }) {
    const res = await apiClient.put('/auth/security', data);
    return res.data;
  },

  // 2. NOTEBOOKS
  async getNotebooks(): Promise<Notebook[]> {
    const res = await apiClient.get('/notebooks/');
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map((item: any) => ({
      ...item,
      id: item.notebook_id,
      category: getCategoryType(item.title),
      icon: item.icon_path || getCategoryIcon(item.title, item.icon_path),
      count: item.document_count || item.count || 0,
    }));
  },

  async getNotebook(notebookId: string): Promise<Notebook> {
    const res = await apiClient.get(`/notebooks/${notebookId}`);
    return {
      ...res.data,
      id: res.data.notebook_id,
      category: getCategoryType(res.data.title),
      icon: res.data.icon_path || getCategoryIcon(res.data.title, res.data.icon_path),
    };
  },

  async createNotebook(title: string, options: { is_private?: boolean; show_on_home?: boolean; icon_path?: string } = {}) {
    const res = await apiClient.post('/notebooks/', {
      title,
      is_private: options.is_private ?? true,
      show_on_home: options.show_on_home ?? true,
      icon_path: options.icon_path,
    });
    return res.data;
  },

  async deleteNotebook(notebookId: string) {
    const res = await apiClient.delete(`/notebooks/${notebookId}`);
    return res.data;
  },

  // 3. DOCUMENTS
  async getDocuments(notebookId: string): Promise<DocumentItem[]> {
    const res = await apiClient.get(`/notebooks/${notebookId}/documents`);
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map((item: any) => ({
      ...item,
      id: item.document_id,
      title: item.file_name,
      file_type: item.file_name?.split('.').pop()?.toLowerCase() || 'pdf',
    }));
  },

  async uploadDocument(notebookId: string, file: File, onUploadProgress?: (percent: number) => void) {
    const formData = new FormData();
    formData.append('file', file);

    const res = await apiClient.post(`/notebooks/${notebookId}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    });
    return res.data;
  },

  async deleteDocument(documentId: string) {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  async getRecentDocuments(): Promise<DocumentItem[]> {
    const res = await apiClient.get('/documents/recent');
    const list = Array.isArray(res.data) ? res.data : [];
    return list.map((item: any) => ({
      ...item,
      id: item.document_id,
      title: item.file_name,
      file_type: item.file_name?.split('.').pop()?.toLowerCase() || 'pdf',
    }));
  },

  // 4. AI SERVICE (RAG Chat & Summarization)
  async askAI(notebookId: string, question: string, model = 'phobert_qa') {
    const res = await apiClient.post(`/notebooks/${notebookId}/chat`, {
      question,
      model,
    });
    return res.data; // { answer, citations: [...] }
  },

  async summarizeNotebook(notebookId: string, model = 'vit5') {
    const res = await apiClient.post(`/notebooks/${notebookId}/summarize`, {
      model,
    });
    return res.data; // { summary: string }
  },

  // 5. NOTIFICATIONS
  async getNotifications(): Promise<NotificationItem[]> {
    const res = await apiClient.get('/notifications/');
    return Array.isArray(res.data) ? res.data : [];
  },

  async markAllNotificationsAsRead() {
    const res = await apiClient.post('/notifications/read');
    return res.data;
  },
};
