'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { getErrorMessage } from '@/lib/api';
import { learningApi, selectedSource, type SourceLink } from '@/lib/learning-api';
import type { SourceRecord } from '@/types';

export default function DocumentReader({ id, name, version, onClose, onSelectSource }: {
  id: string; name: string; version?: number; onClose: () => void; onSelectSource?: (source: SourceLink) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [source, setSource] = useState<SourceRecord | null>(null);
  const [error, setError] = useState(''); const [busy, setBusy] = useState(true);
  const [section, setSection] = useState(0); const [selection, setSelection] = useState<SourceLink | null>(null);
  const generation = useRef(0);
  const load = useCallback(async () => {
    const request = ++generation.current; setBusy(true); setError(''); setSelection(null); setSource(null);
    try {
      if (!version) await learningApi.extract(id);
      const result = await learningApi.source(id, version);
      if (generation.current === request) { setSource(result); setSection(0); }
    } catch (err) { if (generation.current === request) setError(getErrorMessage(err)); }
    finally { if (generation.current === request) setBusy(false); }
  }, [id, version]);
  const invalidate = useCallback(() => { generation.current++; }, []);
  useEffect(() => { if (dialog.current && !dialog.current.open) dialog.current.showModal(); void load(); return invalidate; }, [load, invalidate]);
  const current = source?.sections[section];
  const visibleText = source && current ? Array.from(source.text).slice(current.start, current.end).join('') : source?.text || '';
  return <dialog ref={dialog} onCancel={onClose} aria-labelledby="reader-title" className="w-[95vw] max-w-4xl rounded-2xl p-5 backdrop:bg-black/40">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="reader-title" className="font-bold text-xl">{name}</h2>
      <button onClick={onClose} className="rounded-lg border px-3 py-2">Đóng</button></div>
    <p className="text-sm text-gray-600 my-2">Văn bản trích từ tài liệu. Không dùng AI hoặc OCR.</p>
    {busy && <p role="status">Đang đọc văn bản…</p>}
    {error && <div role="alert" className="text-red-700 my-3">{error} <button onClick={load} className="underline">Thử lại</button></div>}
    {!busy && source && <>
      <label className="block my-3">Trang hoặc mục
        <select className="border rounded-lg p-2 ml-3 max-w-full" value={section} onChange={event => { setSection(Number(event.target.value)); setSelection(null); }}>
          {source.sections.map((item, index) => <option key={index} value={index}>{item.section_path || `Mục ${index + 1}`}</option>)}
        </select></label>
      <textarea aria-label="Nội dung tài liệu" readOnly value={visibleText} className="w-full h-[50vh] border rounded-xl p-4 leading-7" onSelect={event => {
        const input = event.currentTarget;
        const range = selectedSource(input.value, input.selectionStart, input.selectionEnd, current?.start || 0);
        setSelection(range.snippet.trim() ? { document_id: id, version: source.version, source_title: name, ...range } : null);
      }} />
      {onSelectSource && <button disabled={!selection} onClick={() => selection && onSelectSource(selection)} className="my-3 bg-[#26A69A] text-white rounded-xl p-3 disabled:opacity-50">Tạo thẻ từ đoạn đã chọn</button>}
    </>}
    <button className="underline text-sm mt-3" onClick={async () => {
      try { await learningApi.download(`/documents/${id}/download`, name); } catch (err) { setError(getErrorMessage(err)); }
    }}>Tải file gốc</button>
  </dialog>;
}
