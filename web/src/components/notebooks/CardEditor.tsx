'use client';
import { useEffect, useRef, useState } from 'react';
import { getErrorMessage } from '@/lib/api';
import { learningApi, type Flashcard, type SourceLink, type CardInput } from '@/lib/learning-api';
import type { DocumentItem } from '@/types';
import DocumentReader from './DocumentReader';

export default function CardEditor({ notebookId, card, initialSource, documents, onSaved, onClose }: {
  notebookId: string; card?: Flashcard; initialSource?: SourceLink; documents: DocumentItem[]; onSaved: () => void; onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null); const alive = useRef(true);
  const [question, setQuestion] = useState(card?.question || ''); const [answer, setAnswer] = useState(card?.answer || initialSource?.snippet || '');
  const [source, setSource] = useState<SourceLink | null>(card?.source || initialSource || null); const [sourceChanged, setSourceChanged] = useState(false);
  const [documentId, setDocumentId] = useState(''); const [reader, setReader] = useState<DocumentItem | null>(null);
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  useEffect(() => { alive.current = true; if (dialog.current && !dialog.current.open) dialog.current.showModal(); return () => { alive.current = false; }; }, []);
  return <>
    <dialog ref={dialog} aria-labelledby="card-editor-title" className="fixed inset-0 m-auto h-fit max-h-[90vh] overflow-y-auto w-[95vw] max-w-2xl rounded-2xl p-6 backdrop:bg-black/40" onCancel={event => { if (busy) event.preventDefault(); else onClose(); }}>
      <form className="space-y-4" onSubmit={async event => {
        event.preventDefault(); if (busy) return; setBusy(true); setError('');
        const input: CardInput = { question: question.trim(), answer: answer.trim() };
        if (!card || sourceChanged) input.source = source;
        try {
          if (card) await learningApi.editCard(card, input); else await learningApi.createCard(notebookId, input);
          if (alive.current) onSaved();
        } catch (err) { if (alive.current) setError(getErrorMessage(err)); }
        finally { if (alive.current) setBusy(false); }
      }}>
        <h2 id="card-editor-title" className="text-xl font-bold">{card ? 'Sửa thẻ học' : 'Tạo thẻ học'}</h2>
        {error && <p role="alert" className="text-red-700">{error}</p>}
        <label className="block">Câu hỏi<textarea autoFocus required maxLength={2000} value={question} disabled={busy} onChange={event => setQuestion(event.target.value)} className="block w-full border rounded-xl p-3 mt-1 min-h-24" /></label>
        <label className="block">Đáp án<textarea required maxLength={10000} value={answer} disabled={busy} onChange={event => setAnswer(event.target.value)} className="block w-full border rounded-xl p-3 mt-1 min-h-32" /></label>
        {source && <div className="bg-[#F0FAF6] rounded-xl p-3 space-y-2"><p>Nguồn: {source.source_title} · Phiên bản {source.version}</p><blockquote className="whitespace-pre-wrap text-sm max-h-36 overflow-auto">{source.snippet}</blockquote>
          <button type="button" disabled={busy} className="underline" onClick={() => { setSource(null); setSourceChanged(true); }}>Bỏ liên kết nguồn</button></div>}
        <div className="flex flex-wrap gap-2"><label>Tài liệu nguồn<select className="block border rounded-xl p-2 max-w-full" disabled={busy} value={documentId} onChange={event => setDocumentId(event.target.value)}>
          <option value="">Chọn tài liệu để lấy đoạn văn</option>{documents.map(document => <option key={document.document_id} value={document.document_id}>{document.file_name}</option>)}
        </select></label><button type="button" disabled={!documentId || busy} className="underline" onClick={() => setReader(documents.find(document => document.document_id === documentId) || null)}>Đọc và chọn nguồn</button></div>
        <p className="text-xs text-gray-600">Bạn tự nhập câu hỏi và đáp án. Tạo thẻ tự động bằng AI đang tạm hoãn.</p>
        <div className="flex gap-3"><button disabled={busy || !question.trim() || !answer.trim()} className="bg-[#26A69A] text-white rounded-xl px-5 py-3 disabled:opacity-50">{busy ? 'Đang lưu…' : 'Lưu thẻ'}</button>
          <button type="button" disabled={busy} className="border rounded-xl px-5 py-3" onClick={onClose}>Hủy</button></div>
      </form>
    </dialog>
    {reader && <DocumentReader id={reader.document_id} name={reader.file_name} onClose={() => setReader(null)} onSelectSource={value => { setSource(value); setSourceChanged(true); if (!answer.trim()) setAnswer(value.snippet || ''); setReader(null); }} />}
  </>;
}
