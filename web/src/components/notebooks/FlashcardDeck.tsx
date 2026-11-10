'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiService, getErrorMessage } from '@/lib/api';
import { learningApi, type Flashcard, type StudyStats, type SourceLink } from '@/lib/learning-api';
import type { DocumentItem } from '@/types';
import CardEditor from './CardEditor';
import DocumentReader from './DocumentReader';

export default function FlashcardDeck({ notebookId }: { notebookId: string }) {
  const [cards, setCards] = useState<Flashcard[]>([]); const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [stats, setStats] = useState<StudyStats | null>(null); const [cursor, setCursor] = useState<string | null>(null);
  const [query, setQuery] = useState(''); const [search, setSearch] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const [editor, setEditor] = useState<{ card?: Flashcard; source?: SourceLink } | null>(null);
  const [source, setSource] = useState<SourceLink | null>(null); const [reader, setReader] = useState<DocumentItem | null>(null);
  const [reviewing, setReviewing] = useState(false); const [queue, setQueue] = useState<Flashcard[]>([]); const [flipped, setFlipped] = useState(false);
  const [reviewBusy, setReviewBusy] = useState(false); const [pending, setPending] = useState<{ id: string; grade: 'again' | 'remembered'; card: string } | null>(null);
  const generation = useRef(0); const mounted = useRef(true);
  const load = useCallback(async (next?: string) => {
    const request = ++generation.current; setBusy(true); setError('');
    try {
      const [page, progress] = await Promise.all([learningApi.cards(notebookId, search, next), learningApi.stats(notebookId)]);
      if (request !== generation.current || !mounted.current) return;
      setCards(previous => next ? [...previous, ...page.items] : page.items); setCursor(page.next_cursor); setStats(progress);
    } catch (err) { if (mounted.current && request === generation.current) setError(getErrorMessage(err)); }
    finally { if (mounted.current && request === generation.current) setBusy(false); }
  }, [notebookId, search]);
  const invalidate = useCallback(() => { mounted.current = false; generation.current++; }, []);
  useEffect(() => { mounted.current = true; void load(); return invalidate; }, [load, invalidate]);
  useEffect(() => {
    let active = true;
    apiService.getDocuments(notebookId).then(value => { if (active) setDocuments(value); }).catch(() => {});
    return () => { active = false; };
  }, [notebookId]);
  const startReview = async () => {
    setReviewBusy(true); setError('');
    try { const page = await learningApi.due(notebookId); if (mounted.current) { setQueue(page.items); setFlipped(false); setPending(null); setReviewing(true); } }
    catch (err) { if (mounted.current) setError(getErrorMessage(err)); }
    finally { if (mounted.current) setReviewBusy(false); }
  };
  const grade = async (value: 'again' | 'remembered') => {
    const card = queue[0]; if (!card || reviewBusy) return;
    const request = pending?.card === card.card_id ? pending : { id: crypto.randomUUID(), grade: value, card: card.card_id };
    setPending(request); setReviewBusy(true); setError('');
    try {
      await learningApi.review(card, request.grade, request.id);
      if (!mounted.current) return;
      setQueue(previous => previous.slice(1)); setPending(null); setFlipped(false);
      try { const progress = await learningApi.stats(notebookId); if (mounted.current) setStats(progress); }
      catch { if (mounted.current) setError('Đã lưu lượt ôn. Chưa tải lại được thống kê; bạn có thể làm mới sau.'); }
    } catch (err) {
      if (!mounted.current) return;
      setError(getErrorMessage(err));
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 409) { setPending(null); await startReview(); await load(); if (mounted.current) setError(getErrorMessage(err)); }
    } finally { if (mounted.current) setReviewBusy(false); }
  };
  const current = queue[0];
  return <section className="space-y-5">
    {stats && <div className="grid grid-cols-2 lg:grid-cols-4 gap-3" aria-label="Tiến độ học">
      {[['Tổng thẻ', stats.total_cards], ['Đến hạn', stats.due_cards], ['Đã ôn hôm nay', stats.reviewed_today], ['Ngày liên tiếp', stats.streak_days]].map(([label, value]) => <div key={label} className="rounded-2xl bg-[#F0FAF6] border p-4"><p className="text-sm">{label}</p><strong className="text-2xl">{value}</strong></div>)}
    </div>}
    {error && <p role="alert" className="bg-red-50 text-red-800 rounded-xl p-3">{error}</p>}
    <div className="flex flex-wrap gap-3">
      <button disabled={reviewBusy || reviewing} className="bg-[#26A69A] text-white px-4 py-3 rounded-xl disabled:opacity-50" onClick={() => setEditor({})}>Tạo thẻ</button>
      <button disabled={reviewBusy} className="border px-4 py-3 rounded-xl" onClick={startReview}>Ôn thẻ đến hạn</button>
      <button disabled={reviewBusy || busy} className="border px-4 py-3 rounded-xl" onClick={() => load()}>Làm mới</button>
      <button className="underline" onClick={async () => { try { await learningApi.download(`/notebooks/${notebookId}/flashcards/export`, 'flashcards.csv'); } catch (err) { setError(getErrorMessage(err)); } }}>Xuất CSV</button>
    </div>
    {reviewing ? <div className="border rounded-2xl p-5 space-y-4" aria-label="Phiên ôn tập">
      {reviewBusy && <p role="status">Đang cập nhật lượt ôn…</p>}
      {current ? <>
        <p role="status" className="text-sm text-gray-500">Còn {queue.length} thẻ trong lượt này · Tối đa 20 thẻ/lượt</p>
        <h2 className="font-bold text-xl whitespace-pre-wrap">{current.question}</h2>
        {flipped ? <p className="whitespace-pre-wrap p-4 bg-[#F0FAF6] rounded-xl">{current.answer}</p> : <button className="border rounded-xl p-3" onClick={() => setFlipped(true)}>Xem đáp án</button>}
        {flipped && <div className="flex gap-3"><button disabled={reviewBusy || !!pending && pending.grade !== 'again'} onClick={() => grade('again')} className="bg-amber-100 rounded-xl p-3 disabled:opacity-50">Chưa nhớ</button><button disabled={reviewBusy || !!pending && pending.grade !== 'remembered'} onClick={() => grade('remembered')} className="bg-[#26A69A] text-white rounded-xl p-3 disabled:opacity-50">Đã nhớ</button></div>}
        {pending && !reviewBusy && <p>Chưa xác nhận đã lưu. <button className="underline" onClick={() => grade(pending.grade)}>Thử lưu lại lượt ôn</button></p>}
        {current.source && <div><p>Nguồn: {current.source.source_title}</p>{current.source.source_state === 'missing' ? <p>Nguồn không còn tồn tại.</p> : <button className="underline" onClick={() => setSource(current.source)}>Mở nguồn</button>}</div>}
      </> : <><p role="status">Không còn thẻ đến hạn trong lượt này.</p><button className="underline" disabled={reviewBusy} onClick={startReview}>Kiểm tra thẻ đến hạn tiếp theo</button></>}
      <button disabled={reviewBusy} className="border rounded-xl p-2" onClick={() => { setReviewing(false); setPending(null); void load(); }}>Về danh sách thẻ</button>
    </div> : <>
      <form className="flex gap-2" onSubmit={event => { event.preventDefault(); setSearch(query.trim()); }}><input aria-label="Tìm thẻ" placeholder="Tìm câu hỏi hoặc đáp án" className="border rounded-xl p-3 flex-1 min-w-0" value={query} onChange={event => setQuery(event.target.value)} maxLength={200} /><button className="border rounded-xl p-3">Tìm</button></form>
      {busy && <p role="status">Đang tải thẻ…</p>}
      {!busy && !cards.length && <p>Chưa có thẻ phù hợp. Hãy tạo thẻ hoặc chọn đoạn văn trong tài liệu.</p>}
      <ul className="space-y-3">{cards.map(card => <li key={card.card_id} className="border rounded-2xl p-4 space-y-3">
        <h2 className="font-bold whitespace-pre-wrap">{card.question}</h2><p className="whitespace-pre-wrap">{card.answer}</p>
        <p className="text-xs text-gray-600">Lần ôn tiếp theo: {new Date(card.review.due_at).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh' })}</p>
        {card.source && <div><blockquote className="text-sm whitespace-pre-wrap">{card.source.snippet}</blockquote><p className="text-xs">{card.source.source_title} · {card.source.source_state === 'missing' ? 'Nguồn không còn' : card.source.source_state === 'changed' ? 'Nguồn đã thay đổi' : 'Nguồn đã lưu'}</p>{card.source.source_state !== 'missing' && <button className="underline" onClick={() => setSource(card.source)}>Mở nguồn</button>}</div>}
        <div className="flex gap-4"><button className="underline" onClick={() => setEditor({ card })}>Sửa thẻ</button><button className="text-red-700 underline" onClick={async () => {
          if (!window.confirm('Xóa thẻ và lịch sử ôn của thẻ này?')) return;
          try { await learningApi.deleteCard(card.card_id); if (mounted.current) await load(); } catch (err) { if (mounted.current) setError(getErrorMessage(err)); }
        }}>Xóa thẻ</button></div>
      </li>)}</ul>
      {cursor && <button disabled={busy} className="border rounded-xl p-3" onClick={() => load(cursor)}>Xem thêm thẻ</button>}
      {documents.length > 0 && <div className="border rounded-2xl p-4"><h2 className="font-bold mb-2">Tạo thẻ từ tài liệu</h2><div className="flex flex-wrap gap-2">{documents.map(document => <button key={document.document_id} className="border rounded-xl p-2" onClick={() => setReader(document)}>{document.file_name}</button>)}</div></div>}
    </>}
    {editor && <CardEditor notebookId={notebookId} card={editor.card} initialSource={editor.source} documents={documents} onClose={() => setEditor(null)} onSaved={() => { setEditor(null); void load(); }} />}
    {reader && <DocumentReader id={reader.document_id} name={reader.file_name} onClose={() => setReader(null)} onSelectSource={value => { setReader(null); setEditor({ source: value }); }} />}
    {source && <DocumentReader id={source.document_id} name={source.source_title || 'Nguồn'} version={source.version} onClose={() => setSource(null)} />}
  </section>;
}
