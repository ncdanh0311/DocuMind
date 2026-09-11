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
  icon_path?: string;
  icon?: string; // UI alias
  category?: NotebookCategory;
  color?: string;
  count?: number;
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
}

export interface ChatCitation {
  content: string;
  page_number?: number;
  score?: number;
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
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}
