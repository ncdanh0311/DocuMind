export type NotebookCategory = 'study' | 'project' | 'research' | 'personal';

export interface User {
  user_id: string;
  id?: string;
  email: string;
  full_name?: string;
  avatar_id?: string;
  created_at?: string;
}

export interface Notebook {
  notebook_id: string;
  id?: string; // helper alias
  user_id?: string;
  title: string;
  is_private?: boolean;
  show_on_home?: boolean;
  icon_path?: string | null;
  icon?: string; // UI alias
  category: NotebookCategory;
  description: string;
  color?: string;
  count?: number;
  document_count?: number;
  created_at?: string;
  updated_at?: string;
}

export type DocumentStatus = 'uploaded' | 'processing' | 'ready' | 'error';

export interface DocumentItem {
  document_id: string;
  id?: string; // helper alias
  notebook_id: string;
  notebook_title?: string;
  file_name: string;
  title?: string; // helper alias
  file_type?: string;
  file_size?: number;
  status: DocumentStatus;
  uploaded_at: string;
  page_count?: number;
  summary?: string;
  current_version?: number;
  error_code?: string | null;
  job_id?: string | null;
  file_size_bytes?: number | null;
  text_status?: 'not_started' | 'ready' | 'error';
  text_error_code?: string | null;
}

export type QAModel = 'phobert_qa' | 'xlmroberta_qa';
export type SummaryModel = 'vit5' | 'bartpho';

export interface TokenResponse {
  user_id: string;
  access_token: string;
  refresh_token: string;
  token_type: 'bearer';
  full_name?: string | null;
  avatar_id?: string | null;
}

export interface ResetTokenResponse { reset_token: string; }
export interface MessageResponse { message: string; }
export interface ChatCitation {
  id: number;
  source_title: string;
  page_number: number | null;
  snippet: string;
  document_id: string;
  version: number;
  start_offset: number;
  end_offset: number;
  page_end?: number | null;
  section_path?: string | null;
}
export interface ChatResponse {
  status: 'answered' | 'no_answer';
  model_version: string | null;
  answer: string;
  sources: string[];
  citations: ChatCitation[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  citations?: ChatCitation[];
  model?: string;
}

export interface QuickActionItem {
  id: string;
  key: string;
  title: string;
  subtitle: string;
  icon: string;
  href: string;
  badge?: string;
}

export interface NotificationItem {
  notification_id: string;
  id?: string;
  type?: string;
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export interface ModelCapability {
  id: QAModel | SummaryModel | 'embedding' | 'reranker';
  task: string;
  ready: boolean;
  version: string | null;
  error_code?: string | null;
}
export interface SummaryRecord {
  summary_id: string;
  job_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  summary: string | null;
  model: SummaryModel;
  model_version: string;
  coverage: number;
  processed_units: number;
  total_units: number;
  error_code: string | null;
  stale: boolean;
}
export interface JobRecord {
  job_id: string;
  kind: 'ingest' | 'summarize';
  status: string;
  progress: number;
  attempt: number;
  error_code: string | null;
}
export interface SourceRecord {
  document_id: string;
  version: number;
  start_offset: number;
  end_offset: number;
  text: string;
  sections: Array<{ start: number; end: number; section_path: string }>;
}
