import axios from 'axios';
import type { Notebook, DocumentItem, User, NotificationItem, TokenResponse, ResetTokenResponse, MessageResponse, QAModel, SummaryModel, ChatResponse, SummaryRecord, ModelCapability, SourceRecord, JobRecord } from '../types';

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
  setTokens(accessToken: string, refreshToken?: string, fullName?: string | null) {
    if (typeof window === 'undefined') return;
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken);
    if (fullName !== undefined) {
      if (fullName) localStorage.setItem('full_name', fullName);
      else localStorage.removeItem('full_name');
    }
    window.dispatchEvent(new Event('auth-changed'));
  },
  clearAuth() {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('full_name');
    window.dispatchEvent(new Event('auth-changed'));
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

// Share one refresh operation across concurrent requests; retry stale requests with
// the already-rotated token instead of rotating a second time.
let refreshPromise: Promise<string> | null = null;
const publicAuthPaths = ['/auth/login', '/auth/register', '/auth/refresh-token', '/auth/forgot-password', '/auth/verify-otp', '/auth/reset-password'];
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (!original || error.response?.status !== 401 || original._retry ||
        publicAuthPaths.some((path) => original.url?.split('?')[0] === path)) {
      return Promise.reject(error);
    }
    original._retry = true;
    const current = tokenManager.getAccessToken();
    const refresh = tokenManager.getRefreshToken();
    if (!current || !refresh) return Promise.reject(error);
    try {
      if (original.headers.Authorization !== `Bearer ${current}`) {
        original.headers.Authorization = `Bearer ${current}`;
        return apiClient(original);
      }
      if (!refreshPromise) {
        refreshPromise = axios.post<TokenResponse>(`${API_BASE_URL}/auth/refresh-token`,
          { refresh_token: refresh }, { timeout: 15000 }).then((res) => {
          // A logout or a new login must not be overwritten by a late refresh.
          if (tokenManager.getRefreshToken() !== refresh) throw new Error('Session changed');
          if (!res.data.access_token || !res.data.refresh_token) throw new Error('Invalid token response');
          tokenManager.setTokens(res.data.access_token, res.data.refresh_token);
          return res.data.access_token;
        }).finally(() => { refreshPromise = null; });
      }
      const token = await refreshPromise;
      original.headers.Authorization = `Bearer ${token}`;
      return apiClient(original);
    } catch (refreshError) {
      // A network outage is not proof that the stored session is invalid.
      if (axios.isAxiosError(refreshError) && [401, 403].includes(refreshError.response?.status ?? 0)
          && tokenManager.getRefreshToken() === refresh) tokenManager.clearAuth();
      return Promise.reject(refreshError);
    }
  }
);

// Category is persisted by the API; titles never determine classification.
export function getCategoryIcon(category: string = 'personal', iconPath?: string | null): string {
  if (iconPath?.startsWith('/assets/')) return iconPath;
  if (iconPath?.startsWith('assets/')) return '/' + iconPath;
  return `/assets/icons/categories/icon-category-${category}.png`;
}

interface RawNotebook {
  notebook_id: string;
  title: string;
  category: Notebook['category'];
  description: string;
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
    const res = await apiClient.post<TokenResponse>('/auth/login', { email, password });
    if (res.data?.access_token) {
      tokenManager.setTokens(res.data.access_token, res.data.refresh_token, res.data.full_name);
    }
    return res.data;
  },

  async register(email: string, password: string, full_name?: string) {
    const res = await apiClient.post<TokenResponse>('/auth/register', { email, password, full_name });
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
    const res = await apiClient.post<MessageResponse>('/auth/forgot-password', { email });
    return res.data;
  },

  async verifyOtp(email: string, otp_code: string) {
    const res = await apiClient.post<ResetTokenResponse>('/auth/verify-otp', { email, otp_code });
    return res.data;
  },

  async resetPassword(token: string, new_password: string) {
    const res = await apiClient.post<TokenResponse & MessageResponse>('/auth/reset-password', { token, new_password });
    if (res.data?.access_token) {
      tokenManager.setTokens(res.data.access_token, res.data.refresh_token, res.data.full_name);
    }
    return res.data;
  },

  async getProfile(): Promise<User> {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  async updateProfile(data: { full_name?: string; avatar_id?: string }) {
    const res = await apiClient.put('/auth/me', data);
    if (data.full_name) {
      localStorage.setItem('full_name', data.full_name);
    }
    return res.data;
  },

  async updateSecurity(data: { old_password: string; new_password: string }) {
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
      category: item.category ?? 'personal',
      icon: getCategoryIcon(item.category, item.icon_path),
      count: item.document_count || item.count || 0,
    }));
  },

  async getNotebook(notebookId: string): Promise<Notebook> {
    const res = await apiClient.get<Notebook>(`/notebooks/${notebookId}`);
    return {
      ...res.data,
      id: res.data.notebook_id,
      category: res.data.category ?? 'personal',
      icon: getCategoryIcon(res.data.category, res.data.icon_path),
      count: res.data.document_count || res.data.count || 0,
    };
  },

  async createNotebook(title: string, options: { category?: Notebook['category']; description?: string; is_private?: boolean; show_on_home?: boolean; icon_path?: string } = {}) {
    const res = await apiClient.post('/notebooks/', {
      title,
      category: options.category ?? 'personal',
      description: options.description ?? '',
      is_private: options.is_private ?? true,
      show_on_home: options.show_on_home ?? true,
      icon_path: options.icon_path,
    });
    return res.data;
  },

  async updateNotebook(notebookId: string, data: { title?: string; category?: Notebook['category']; description?: string; is_private?: boolean; show_on_home?: boolean; icon_path?: string }) {
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

  async renameDocument(documentId: string, title: string): Promise<DocumentItem> {
    return (await apiClient.patch<DocumentItem>(`/documents/${documentId}`, { title })).data;
  },
  async getAppConfig(): Promise<{ ai_enabled: boolean }> {
    return (await apiClient.get('/app-config')).data;
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
  async askAI(notebookId: string, question: string, model: QAModel = 'phobert_qa') {
    const res = await apiClient.post<ChatResponse>(`/notebooks/${notebookId}/chat`, {
      question,
      model,
    });
    return res.data; // { answer, citations: [...] }
  },

  async summarizeNotebook(notebookId: string, model: SummaryModel = 'vit5') {
    const res = await apiClient.post<SummaryRecord>(`/notebooks/${notebookId}/summarize`, {
      model,
    });
    return res.data; // { summary: string }
  },

  async getSummary(summaryId: string) {
    return (await apiClient.get<SummaryRecord>(`/summaries/${summaryId}`)).data;
  },
  async getJob(jobId: string) {
    return (await apiClient.get<JobRecord>(`/jobs/${jobId}`)).data;
  },
  async getCapabilities() {
    return (await apiClient.get<{ models: ModelCapability[] }>('/capabilities')).data.models;
  },
  async getSource(citation: { document_id: string; version: number; start_offset: number; end_offset: number }) {
    return (await apiClient.get<SourceRecord>(`/documents/${citation.document_id}/source`, {
      params: { version: citation.version, start: citation.start_offset, end: citation.end_offset },
    })).data;
  },
  async reprocessDocument(documentId: string) {
    return (await apiClient.post(`/documents/${documentId}/reprocess`)).data;
  },

  // 5. NOTIFICATIONS
  async getNotifications(): Promise<NotificationItem[]> {
    const res = await apiClient.get<NotificationItem[]>('/notifications/');
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
  ERR_USER_STORAGE_QUOTA: 'Dung lượng tài khoản đã đầy. Hãy xóa bớt tài liệu rồi thử lại.',
  ERR_TOTAL_STORAGE_QUOTA: 'Kho lưu trữ đã đầy. Vui lòng thử lại sau khi dọn dung lượng.',
  ERR_FILE_TOO_LARGE: 'File vượt quá dung lượng cho phép.',
  ERR_STORAGE_RECONCILE_REQUIRED: 'Tài liệu cũ cần được kiểm kê dung lượng trước khi tải thêm file.',
  ERR_STORAGE_UNAVAILABLE: 'Kho file chưa kết nối được. Vui lòng thử lại.',
  ERR_SOURCE_MISSING: 'Không còn file nguồn để mở hoặc tải xuống.',
  ERR_SOURCE_NOT_READY: 'Tài liệu chưa có văn bản để đọc.',
  ERR_DOCUMENT_NEEDS_OCR: 'PDF chưa có lớp chữ. Bạn vẫn có thể tải file gốc; OCR chưa được bật.',
  ERR_DOCUMENT_PASSWORD: 'PDF đang được khóa bằng mật khẩu.',
  ERR_FILE_FORMAT: 'Không đọc được định dạng hoặc cấu trúc file.',
  ERR_TEXT_ENCODING: 'File TXT cần dùng bảng mã UTF-8.',
  ERR_TOO_MANY_PAGES: 'Tài liệu vượt giới hạn số trang được đọc.',
  ERR_TEXT_TOO_LARGE: 'Nội dung vượt giới hạn đọc văn bản của bản beta.',
  ERR_DOCUMENT_TOO_COMPLEX: 'Tài liệu có cấu trúc quá lớn để xử lý trong bản beta.',
  ERR_EXTRACTION_BUSY: 'Đang đọc một tài liệu khác. Vui lòng thử lại sau.',
  ERR_EXTRACTION_TIMEOUT: 'Đọc tài liệu quá thời gian cho phép. Bạn vẫn có thể tải file gốc.',
  ERR_DOCUMENT_BUSY: 'Tài liệu đang có tác vụ xử lý. Vui lòng thử lại sau.',
  ERR_JOB_QUOTA: 'Bạn đã có đủ số tác vụ đang chờ. Hãy đợi tác vụ hiện tại hoàn tất.',
  ERR_REVIEW_CONFLICT: 'Thẻ đã được ôn trên thiết bị khác. Hãy tải lại trạng thái mới.',
  ERR_CARD_CONFLICT: 'Thẻ đã được sửa ở nơi khác. Hãy tải lại trước khi lưu.',
  ERR_CARD_NOT_FOUND: 'Không tìm thấy thẻ hoặc bạn không có quyền truy cập.',
  ERR_CARD_NOT_DUE: 'Thẻ này chưa đến hạn ôn. Hãy làm mới danh sách.',
  ERR_REQUEST_ID_REUSED: 'Mã lượt ôn đã được dùng cho thao tác khác. Hãy tải lại thẻ.',
  ERR_INVALID_SOURCE_RANGE: 'Đoạn nguồn chưa khớp tài liệu. Hãy mở nguồn và chọn lại.',
  ERR_HISTORY_NOT_READY: 'Bản lưu chưa có nội dung hoàn tất để xuất.',
  ERR_HISTORY_NOT_FOUND: 'Không tìm thấy lịch sử đã lưu.',
  ERR_SUMMARY_NOT_FOUND: 'Không tìm thấy bản tóm tắt đã lưu.',
  ERR_INVALID_CURSOR: 'Danh sách đã thay đổi. Hãy tải lại từ đầu.',
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
  ERR_SOURCE_CHANGED: 'Tài liệu đã thay đổi. Vui lòng tạo lại bản tóm tắt.',
  ERR_DOCUMENTS_NOT_READY: 'Vui lòng đợi mọi tài liệu xử lý xong hoặc xử lý lại tài liệu gặp lỗi.',
  ERR_JOB_FAILED: 'Xử lý tài liệu gặp lỗi. Bạn có thể thử lại.',
  ERR_REPROCESS_REQUIRED: 'Tài liệu cần được xử lý lại để cập nhật vị trí nguồn.',
  ERR_MODEL_NOT_CALIBRATED: 'Mô hình chưa hoàn tất đánh giá chất lượng.',
  ERR_AI_SERVICE_ERROR: 'Dịch vụ AI gặp lỗi. Vui lòng thử lại sau.',
  ERR_AI_DISABLED: 'Tính năng AI đang tạm hoãn.',
  ERR_MODEL_UNAVAILABLE: 'Mô hình đã chọn chưa sẵn sàng. Vui lòng chọn mô hình khác hoặc thử lại sau.',
  ERR_INTERNAL_SERVER: 'Máy chủ gặp lỗi. Vui lòng thử lại sau.',
  ERR_FILE_WRITE_FAILED: 'Không thể lưu tài liệu. Vui lòng thử lại sau.',
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

