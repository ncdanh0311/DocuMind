import axios from 'axios';
import { Notebook, DocumentItem, User, NotificationItem } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,
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
            // eslint-disable-next-line @next/next/no-location-assign-relative-destination
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

interface RawNotebook {
  notebook_id: string;
  title: string;
  icon_path?: string;
  document_count?: number;
  count?: number;
  is_private?: boolean;
  show_on_home?: boolean;
  created_at?: string;
}

interface RawDocument {
  document_id: string;
  notebook_id: string;
  notebook_title?: string;
  file_name: string;
  status: 'processing' | 'ready' | 'error' | 'uploaded';
  file_size?: number;
  page_count?: number;
  uploaded_at: string;
}

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
    } catch {
      // Ignore network errors on logout
    }
    tokenManager.clearAuth();
  },

  async forgotPassword(email: string) {
    const res = await apiClient.post('/auth/forgot-password', { email });
    return res.data;
  },

  async verifyOtp(email: string, otp_code: string) {
    const res = await apiClient.post('/auth/verify-otp', { email, otp_code });
    return res.data;
  },

  async resetPassword(token: string, new_password: string) {
    const res = await apiClient.post('/auth/reset-password', { token, new_password });
    if (res.data?.access_token) {
      tokenManager.setTokens(res.data.access_token, res.data.refresh_token, res.data.full_name);
    }
    return res.data;
  },

  async getProfile(): Promise<User> {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },

  async updateProfile(data: { full_name?: string; avatar_id?: string }) {
    const res = await apiClient.put('/auth/me', data);
    if (data.full_name) {
      localStorage.setItem('full_name', data.full_name);
    }
    return res.data;
  },

  async updateSecurity(data: { old_password?: string; new_password?: string }) {
    const res = await apiClient.put('/auth/security', data);
    return res.data;
  },

  // 2. NOTEBOOKS
  async getNotebooks(): Promise<Notebook[]> {
    const res = await apiClient.get('/notebooks/');
    const list: RawNotebook[] = Array.isArray(res.data) ? res.data : [];
    return list.map((item) => ({
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
      count: res.data.document_count || res.data.count || 0,
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

  async updateNotebook(notebookId: string, data: { title?: string; is_private?: boolean; show_on_home?: boolean; icon_path?: string }) {
    const res = await apiClient.put(`/notebooks/${notebookId}`, data);
    return res.data;
  },

  async deleteNotebook(notebookId: string) {
    const res = await apiClient.delete(`/notebooks/${notebookId}`);
    return res.data;
  },

  // 3. DOCUMENTS
  async getDocuments(notebookId: string): Promise<DocumentItem[]> {
    const res = await apiClient.get(`/notebooks/${notebookId}/documents`);
    const list: RawDocument[] = Array.isArray(res.data) ? res.data : [];
    return list.map((item) => ({
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

  async createDocumentFromText(notebookId: string, title: string, content: string): Promise<DocumentItem> {
    const res = await apiClient.post(`/notebooks/${notebookId}/documents/text`, {
      title,
      content,
    });
    return {
      ...res.data,
      id: res.data.document_id,
      title: res.data.file_name,
      file_type: 'txt',
    };
  },

  async deleteDocument(documentId: string) {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  async getRecentDocuments(): Promise<DocumentItem[]> {
    const res = await apiClient.get('/documents/recent');
    const list: RawDocument[] = Array.isArray(res.data) ? res.data : [];
    return list.map((item) => ({
      ...item,
      id: item.document_id,
      title: item.file_name,
      file_type: item.file_name?.split('.').pop()?.toLowerCase() || 'pdf',
    }));
  },

  async getDocumentChunks(documentId: string) {
    const res = await apiClient.get(`/documents/${documentId}/chunks`);
    return res.data;
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

  async markNotificationAsRead(notificationId: string) {
    const res = await apiClient.post(`/notifications/${notificationId}/read`);
    return res.data;
  },
};

const ERROR_TRANSLATIONS: Record<string, string> = {
  ERR_EMAIL_TAKEN: 'Email này đã được sử dụng. Vui lòng chọn email khác hoặc đăng nhập.',
  ERR_INVALID_CREDENTIALS: 'Email hoặc mật khẩu không chính xác.',
  ERR_EMAIL_NOT_FOUND: 'Email này chưa được đăng ký trong hệ thống.',
  ERR_OTP_INVALID: 'Mã xác thực OTP không chính xác.',
  ERR_OTP_EXPIRED: 'Mã xác thực OTP đã hết hạn. Vui lòng yêu cầu mã mới.',
  ERR_TOKEN_INVALID: 'Token không hợp lệ.',
  ERR_TOKEN_EXPIRED: 'Phiên làm việc đã hết hạn. Vui lòng thử lại.',
  ERR_USER_NOT_FOUND: 'Không tìm thấy người dùng.',
  ERR_NOTEBOOK_NOT_FOUND: 'Không tìm thấy sổ tay hoặc bạn không có quyền truy cập.',
  ERR_DOC_NOT_FOUND: 'Không tìm thấy tài liệu.',
  ERR_DOC_FORBIDDEN: 'Bạn không có quyền thao tác với tài liệu này.',
  ERR_UNAUTHORIZED: 'Phiên đăng nhập đã hết hạn hoặc không hợp lệ.',
  ERR_SESSION_EXPIRED: 'Phiên đăng nhập của bạn đã hết hạn. Vui lòng đăng nhập lại.',
  ERR_OLD_PASSWORD_INCORRECT: 'Mật khẩu hiện tại không chính xác.',
  ERR_NO_DOCUMENTS: 'Sổ tay này chưa có tài liệu nào được phân tích thành công.',
  ERR_ANSWER_NOT_FOUND: 'Không tìm thấy câu trả lời trong tài liệu.',
  ERR_INVALID_INPUT: 'Dữ liệu đầu vào không hợp lệ.',
  ERR_AI_SERVICE_UNAVAILABLE: 'Dịch vụ AI hiện đang bận hoặc đang khởi động. Vui lòng thử lại sau!',
  ERR_CONNECTION_FAILED: 'Kết nối thất bại. Vui lòng kiểm tra lại kết nối mạng!',
};

export function getErrorMessage(err: unknown, defaultMessage = 'Đã có lỗi xảy ra. Vui lòng thử lại.'): string {
  if (axios.isAxiosError(err)) {
    if (!err.response) {
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        return `Máy chủ phản hồi quá lâu (có thể đang khởi động từ chế độ ngủ trên Render). Vui lòng đợi 30 giây rồi thử lại!`;
      }
      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        return `Không thể kết nối tới máy chủ backend (${API_BASE_URL}). Vui lòng đảm bảo backend đang chạy.`;
      }
      return `Lỗi kết nối máy chủ: ${err.message || 'Không thể liên lạc với máy chủ'}`;
    }

    const data = err.response.data;
    if (data) {
      if (typeof data.detail === 'string') {
        return ERROR_TRANSLATIONS[data.detail] || data.detail;
      }
      if (Array.isArray(data.detail)) {
        const messages = data.detail.map((item: unknown) => {
          if (typeof item === 'string') return item;
          if (typeof item === 'object' && item !== null) {
            const errObj = item as { loc?: unknown[]; msg?: string };
            const field = Array.isArray(errObj.loc) ? errObj.loc[errObj.loc.length - 1] : '';
            const msg = errObj.msg || 'Không hợp lệ';
            if (field === 'email') return 'Địa chỉ email không đúng định dạng';
            if (field === 'password') return 'Mật khẩu không hợp lệ';
            return field ? `${String(field)}: ${msg}` : msg;
          }
          return 'Dữ liệu không hợp lệ';
        });
        return messages.join('. ');
      }
      if (typeof data.message === 'string') {
        return ERROR_TRANSLATIONS[data.message] || data.message;
      }
    }

    if (err.response.status === 404) return 'Không tìm thấy dịch vụ yêu cầu (404).';
    if (err.response.status === 500) return 'Lỗi máy chủ nội bộ (500). Vui lòng thử lại sau.';
    if (err.response.status === 403) return 'Bạn không có quyền thực hiện hành động này (403).';
  }

  if (err instanceof Error) {
    return err.message;
  }

  return defaultMessage;
}

