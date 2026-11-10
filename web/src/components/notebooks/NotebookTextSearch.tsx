'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { learningApi, type TextSearchResult, type SourceLink } from '@/lib/learning-api';
import { getErrorMessage } from '@/lib/api';
import DocumentReader from './DocumentReader';

export default function NotebookTextSearch({ notebookId, onSelectSource }: { notebookId: string; onSelectSource: (value: SourceLink) => void }) {
  const [query, setQuery] = useState(''); const [searched, setSearched] = useState('');
  const [items, setItems] = useState<TextSearchResult[]>([]); const [cursor, setCursor] = useState<string | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [reader, setReader] = useState<TextSearchResult | null>(null);
  const generation = useRef(0); const invalidate = useCallback(() => { generation.current++; }, []);
  useEffect(() => invalidate, [invalidate]);
  const search = async (next?: string) => {
    const term = next ? searched : query.trim(); if (!term) return;
    const request = ++generation.current; setBusy(true); setError('');
    try {
      const page = await learningApi.search(notebookId, term, next);
      if (request === generation.current) { setItems(previous => next ? [...previous, ...page.items] : page.items); setCursor(page.next_cursor); setSearched(term); }
    } catch (err) { if (request === generation.current) setError(getErrorMessage(err)); }
    finally { if (request === generation.current) setBusy(false); }
  };
  return <section className="border rounded-2xl p-4 space-y-3">
    <h2 className="font-bold">Tìm trong nội dung tài liệu</h2><p className="text-sm text-gray-600">Tìm chữ đã đọc từ tài liệu, không dùng AI. Tài liệu chưa có văn bản sẽ chưa xuất hiện.</p>
    <form className="flex gap-2" onSubmit={event => { event.preventDefault(); void search(); }}><input aria-label="Tìm nội dung tài liệu" className="border rounded-xl p-2 flex-1 min-w-0" value={query} maxLength={200} onChange={event => setQuery(event.target.value)} /><button disabled={busy || !query.trim()} className="border rounded-xl p-2">Tìm nội dung</button></form>
    {busy && <p role="status">Đang tìm nội dung…</p>}{error && <p role="alert" className="text-red-700">{error}</p>}
    {searched && !busy && !items.length && <p>Không tìm thấy nội dung phù hợp.</p>}
    {items.map(item => <button key={item.document_id} className="block w-full text-left border rounded-xl p-3" onClick={() => setReader(item)}><strong>{item.file_name}</strong><p className="text-sm whitespace-pre-wrap">{item.snippet}</p></button>)}
    {cursor && <button disabled={busy} className="underline" onClick={() => search(cursor)}>Xem thêm kết quả</button>}
    {reader && <DocumentReader id={reader.document_id} name={reader.file_name} version={reader.version} onClose={() => setReader(null)} onSelectSource={value => { setReader(null); onSelectSource(value); }} />}
  </section>;
}
