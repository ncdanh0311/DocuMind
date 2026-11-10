import { apiClient, tokenManager } from './api';
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
export interface ReviewState { card_id: string; stage: number; revision: number; due_at: string; last_review_at: string | null; }
export interface Flashcard {
  card_id: string; notebook_id: string; question: string; answer: string; source: SourceLink | null;
  revision: number; created_at: string; updated_at: string; review: ReviewState;
}
export interface StudyStats { total_cards: number; due_cards: number; reviewed_today: number; streak_days: number; timezone: string; server_now: string; }
export interface CardInput { question: string; answer: string; source?: SourceLink | null; }
export interface TextSearchResult { document_id: string; file_name: string; version: number; snippet: string; }

export const learningApi = {
  async search(id: string, q: string, cursor?: string): Promise<Page<TextSearchResult>> {
    return (await apiClient.get(`/notebooks/${id}/search`, { params: { q, cursor } })).data;
  },
  async cards(id: string, q = '', cursor?: string): Promise<Page<Flashcard>> {
    return (await apiClient.get(`/notebooks/${id}/flashcards`, { params: { q, cursor } })).data;
  },
  async createCard(id: string, input: CardInput): Promise<Flashcard> {
    return (await apiClient.post(`/notebooks/${id}/flashcards`, input)).data;
  },
  async editCard(card: Flashcard, input: CardInput): Promise<Flashcard> {
    return (await apiClient.patch(`/flashcards/${card.card_id}`, { ...input, expected_revision: card.revision })).data;
  },
  async deleteCard(id: string) { await apiClient.delete(`/flashcards/${id}`); },
  async due(id: string): Promise<Page<Flashcard>> { return (await apiClient.get('/flashcards/due', { params: { notebook_id: id } })).data; },
  async review(card: Flashcard, grade: 'again' | 'remembered', requestId: string): Promise<ReviewState> {
    return (await apiClient.post(`/flashcards/${card.card_id}/reviews`, { request_id: requestId, grade,
      expected_revision: card.review.revision, card_revision: card.revision })).data;
  },
  async stats(id: string): Promise<StudyStats> { return (await apiClient.get('/study/stats', { params: { notebook_id: id } })).data; },
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

const readingRequests = new Map<string, Promise<SourceRecord>>();
export function readDocumentOnce(id: string, api = learningApi): Promise<SourceRecord> {
  const key = `${tokenManager.getAccessToken() || 'anonymous'}:${id}`;
  const existing = readingRequests.get(key);
  if (existing) return existing;
  const pending = (async () => { await api.extract(id); return api.source(id); })().finally(() => {
    if (readingRequests.get(key) === pending) readingRequests.delete(key);
  });
  readingRequests.set(key, pending);
  return pending;
}
