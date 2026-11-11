'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getErrorMessage } from '@/lib/api';
import { learningApi, type HistoryItem, type HistoryDetail, type SourceLink } from '@/lib/learning-api';
import DocumentReader from './DocumentReader';

export default function NotebookHistory({ notebookId }: { notebookId: string }) {
  const [items, setItems] = useState<HistoryItem[]>([]); const [cursor, setCursor] = useState<string | null>(null);
  const [detail, setDetail] = useState<HistoryDetail | null>(null); const [source, setSource] = useState<SourceLink | null>(null);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const generation = useRef(0); const detailRequest = useRef(0);
  const load = useCallback(async (next?: string) => {
    const request = ++generation.current; setBusy(true); setError('');
    try {
      const page = await learningApi.history(notebookId, next);
      if (request === generation.current) { setItems(previous => next ? [...previous, ...page.items] : page.items); setCursor(page.next_cursor); }
    } catch (err) { if (request === generation.current) setError(getErrorMessage(err)); }
    finally { if (request === generation.current) setBusy(false); }
  }, [notebookId]);
  const invalidate = useCallback(() => { generation.current++; detailRequest.current++; }, []);
  useEffect(() => { setItems([]); setDetail(null); void load(); return invalidate; }, [load, invalidate]);
  return <section className="rounded-2xl border p-5 space-y-3">
    <div className="flex justify-between"><h2 className="font-bold text-lg">Lịch sử đã lưu</h2><button disabled={busy} onClick={() => load()} className="underline">Làm mới</button></div>
    <p className="text-sm text-gray-600">Có thể xem kết quả cũ khi AI đang tạm hoãn.</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {busy && <p role="status">Đang tải lịch sử…</p>}
    {!busy && !items.length && <p>Chưa có hỏi đáp hoặc tóm tắt được lưu.</p>}
    <ul className="space-y-2">{items.map(item => <li key={item.id}><button className="text-left w-full border rounded-xl p-3" onClick={async () => {
      const request = ++detailRequest.current; setError('');
      try { const value = await learningApi.historyDetail(item); if (request === detailRequest.current) setDetail(value); }
      catch (err) { if (request === detailRequest.current) setError(getErrorMessage(err)); }
    }}><span className="font-medium">{item.kind === 'qa' ? item.title : 'Bản tóm tắt'}</span><span className="block text-xs text-gray-500">{item.model} · {new Date(item.created_at).toLocaleString('vi-VN')}</span></button></li>)}</ul>
    {cursor && <button disabled={busy} onClick={() => load(cursor)} className="border rounded-xl p-2">Xem thêm lịch sử</button>}
    {detail && <article className="bg-[#F0FAF6] rounded-xl p-4 space-y-3" aria-label="Chi tiết lịch sử">
      <div className="flex justify-between gap-3"><h3 className="font-bold">{detail.question || 'Bản tóm tắt đã lưu'}</h3><button onClick={() => { detailRequest.current++; setDetail(null); }}>Đóng chi tiết</button></div>
      <p className="text-xs">{detail.model} · {detail.model_version || 'Phiên bản cũ'} · {new Date(detail.created_at).toLocaleString('vi-VN')}</p>
      <p className="whitespace-pre-wrap">{detail.answer || detail.content || 'Chưa có nội dung hoàn tất.'}</p>
      {(detail.citations || detail.sources || []).map((item, index) => <div key={index} className="border-t pt-2">
        <p>{item.source_title || 'Tài liệu nguồn'} {item.source_state !== 'available' && <span className="text-amber-800">— {item.source_state === 'missing' ? 'Nguồn không còn tồn tại' : 'Nguồn đã thay đổi'}</span>}</p>
        {item.snippet && <blockquote className="whitespace-pre-wrap text-sm">{item.snippet}</blockquote>}
        {item.source_state !== 'missing' && item.version > 0 && <button className="underline" onClick={() => setSource(item)}>Mở nguồn đã lưu</button>}
      </div>)}
      <button className="underline" onClick={async () => {
        try { await learningApi.download(`/history/${detail.question ? 'qa' : 'summary'}/${detail.id}/export`, 'lich-su.md'); }
        catch (err) { setError(getErrorMessage(err)); }
      }}>Xuất Markdown</button>
    </article>}
    {source && <DocumentReader id={source.document_id} name={source.source_title || 'Nguồn'} version={source.version} onClose={() => setSource(null)} />}
  </section>;
}
