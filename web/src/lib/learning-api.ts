import { apiClient } from './api';
import type { SourceRecord } from '@/types';

export interface Page<T> { items: T[]; next_cursor: string | null; }
export interface SourceLink {
  document_id: string; version: number; start_offset: number; end_offset: number;
  snippet?: string; source_title?: string; page_number?: number | null; section_path?: string | null;
  source_state?: 'available' | 'changed' | 'missing';
}
export interface HistoryItem { id: string; kind: 'qa' | 'summary'; title: string; model: string; created_at: string; }
export interface HistoryDetail {
  id: string; model: string; model_version: string | null; created_at: string;
  question?: string; answer?: string; content?: string | null; status?: string;
  citations?: SourceLink[]; sources?: SourceLink[];
}
export interface StorageUsage { used_bytes: number; limit_bytes: number; max_file_bytes: number; }

export const learningApi = {
  async extract(id: string) { return (await apiClient.post(`/documents/${id}/extract-text`)).data; },
  async source(id: string, version?: number): Promise<SourceRecord> {
    return (await apiClient.get(`/documents/${id}/source`, { params: { version } })).data;
  },
  async usage(): Promise<StorageUsage> { return (await apiClient.get('/storage/usage')).data; },
  async history(id: string, cursor?: string): Promise<Page<HistoryItem>> {
    return (await apiClient.get(`/notebooks/${id}/history`, { params: { cursor } })).data;
  },
  async historyDetail(item: HistoryItem): Promise<HistoryDetail> {
    return (await apiClient.get(`/${item.kind === 'qa' ? 'qa-history' : 'summary-history'}/${item.id}`)).data;
  },
  async download(path: string, name: string) {
    const response = await apiClient.get(path, { responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = name;
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  },
};

export function selectedSource(text: string, startUtf16: number, endUtf16: number, base = 0) {
  return { start_offset: base + Array.from(text.slice(0, startUtf16)).length,
           end_offset: base + Array.from(text.slice(0, endUtf16)).length,
           snippet: text.slice(startUtf16, endUtf16) };
}
