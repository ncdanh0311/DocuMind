'use client';
import React, { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { isAxiosError } from 'axios';
import { Loader2, Sparkles, Copy } from 'lucide-react';
import { apiService, getErrorMessage } from '@/lib/api';
import { useNotebooks } from '@/contexts/NotebookContext';
import type { ModelCapability, SummaryModel, SummaryRecord } from '@/types';

const active = (record: SummaryRecord | null) => !!record && !record.stale && ['queued', 'running'].includes(record.status);

function SummaryContent() {
  const params = useSearchParams();
  const { notebooks } = useNotebooks();
  const [notebookId, setNotebookId] = useState(params.get('notebookId') || '');
  const [model, setModel] = useState<SummaryModel>('vit5');
  const [models, setModels] = useState<ModelCapability[]>([]);
  const [record, setRecord] = useState<SummaryRecord | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const aiPaused = models.length === 0 || models.some(entry => entry.error_code === 'ERR_AI_DISABLED');
  const generation = useRef(0);
  const invalidate = useCallback(() => { generation.current++; }, []);
  const key = `documind:summary:${notebookId}:${model}`;

  useEffect(() => {
    apiService.getCapabilities().then(setModels).catch((err) => setError(getErrorMessage(err)));
  }, []);
  useEffect(() => { if (!notebookId && notebooks.length) setNotebookId(notebooks[0].notebook_id); }, [notebooks, notebookId]);
  useEffect(() => {
    const version = ++generation.current;
    setRecord(null); setError(null); setStarting(false);
    const saved = localStorage.getItem(key);
    if (saved) apiService.getSummary(saved).then((value) => {
      if (generation.current === version) setRecord(value);
    }).catch((err) => {
      if (generation.current !== version) return;
      if (isAxiosError(err) && err.response?.status === 404) localStorage.removeItem(key);
      else setError(getErrorMessage(err));
    });
    return invalidate;
  }, [key, invalidate]);
  const summaryId = record?.summary_id;
  const status = record?.status;
  const stale = record?.stale;
  useEffect(() => {
    if (aiPaused || !summaryId || stale || !['queued', 'running'].includes(status || '')) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const value = await apiService.getSummary(summaryId);
        if (cancelled) return;
        setRecord(value); setError(null);
        if (active(value)) timer = setTimeout(poll, 3000);
      } catch (err) {
        if (!cancelled) {
          setError(getErrorMessage(err));
          if (isAxiosError(err) && [401, 403, 404].includes(err.response?.status || 0)) setRecord(null);
          else timer = setTimeout(poll, 3000);
        }
      }
    };
    timer = setTimeout(poll, 3000);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [summaryId, status, stale, key, aiPaused]);

  const start = async () => {
    const version = generation.current;
    setStarting(true); setError(null);
    try {
      const value = await apiService.summarizeNotebook(notebookId, model);
      if (generation.current !== version) return;
      localStorage.setItem(key, value.summary_id);
      setRecord(value);
    } catch (err) { if (generation.current === version) setError(getErrorMessage(err)); }
    finally { if (generation.current === version) setStarting(false); }
  };
  const ready = models.find((entry) => entry.id === model)?.ready === true;
  const waiting = !aiPaused && active(record);
  return <div className="space-y-6 pb-12">
    <div><h2 className="font-outfit text-3xl font-bold text-[#2D3E50]">Tóm tắt tài liệu</h2>
      <p className="text-sm text-[#8E9DAE] mt-2">Đọc từng phần rồi tổng hợp toàn bộ tài liệu trong sổ tay.</p></div>
    <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 grid md:grid-cols-3 gap-4">
      <label className="text-sm font-semibold">Sổ tay
        <select aria-label="Sổ tay" value={notebookId} disabled={starting} onChange={(event) => setNotebookId(event.target.value)} className="block w-full bg-[#F5F7F7] rounded-xl p-3 mt-2">
          <option value="">Chọn sổ tay</option>{notebooks.map((item) => <option key={item.notebook_id} value={item.notebook_id}>{item.title}</option>)}
        </select></label>
      <label className="text-sm font-semibold">Mô hình
        <select aria-label="Mô hình" value={model} disabled={starting} onChange={(event) => setModel(event.target.value as SummaryModel)} className="block w-full bg-[#F5F7F7] rounded-xl p-3 mt-2">
          {(['vit5', 'bartpho'] as const).map((id) => <option key={id} value={id} disabled={!models.find((entry) => entry.id === id)?.ready}>{id === 'vit5' ? 'ViT5' : 'BARTpho'}{models.find((entry) => entry.id === id)?.ready ? '' : ' — Chưa sẵn sàng'}</option>)}
        </select></label>
      <button onClick={start} disabled={!notebookId || !ready || starting || waiting} className="mt-6 p-3 rounded-xl bg-[#26A69A] text-white font-bold disabled:opacity-40 flex items-center justify-center gap-2">
        {starting || waiting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
        {starting ? 'Đang tạo yêu cầu...' : waiting ? 'Đang xử lý...' : 'Tạo bản tóm tắt'}
      </button>
    </div>
    {aiPaused && <p role="status" className="text-sm text-gray-600">Tính năng AI đang tạm hoãn.</p>}
    {!ready && !aiPaused && <p className="text-sm text-[#8E9DAE]">Mô hình đã chọn chưa sẵn sàng. Bạn có thể chọn mô hình khác khi dịch vụ được cập nhật.</p>}
    {error && <p role="alert" className="rounded-2xl p-4 bg-red-50 text-red-700">{error}</p>}
    {record?.stale && <p role="alert" className="p-4 bg-amber-50 rounded-xl">Tài liệu đã thay đổi. Hãy tạo lại bản tóm tắt.</p>}
    {record && ['failed', 'cancelled'].includes(record.status) && !record.stale && <p role="alert" className="p-4 bg-red-50 rounded-xl">Không thể hoàn tất bản tóm tắt. Bạn có thể thử tạo lại.</p>}
    {waiting && <div role="status" className="bg-white rounded-3xl p-8 border border-[#EAEFEA]">
      <p>{record?.status === 'queued' ? 'Đang chờ xử lý' : 'Đang đọc và tổng hợp tài liệu'}</p>
      <p className="mt-2 text-sm text-[#8E9DAE]">Đã đọc {record?.processed_units || 0}/{record?.total_units || 0} phần. Bạn có thể rời trang và quay lại sau.</p>
      <progress aria-label="Phần tài liệu đã đọc" className="w-full mt-4" max={record?.total_units || 1} value={record?.processed_units || 0} />
    </div>}
    {record?.status === 'succeeded' && !record.stale && record.summary && <article className="bg-white rounded-3xl p-8 border border-[#EAEFEA]">
      <div className="flex justify-between mb-5"><h3 className="font-bold text-lg">Bản tóm tắt</h3><button aria-label="Sao chép tóm tắt" onClick={() => navigator.clipboard.writeText(record.summary || '')}><Copy className="w-4 h-4" /></button></div>
      <ReactMarkdown>{record.summary}</ReactMarkdown>
      <p className="mt-6 text-xs text-[#8E9DAE]">Đã xử lý {record.processed_units}/{record.total_units} phần đầu vào. Hãy đối chiếu thông tin quan trọng với tài liệu nguồn.</p>
    </article>}
  </div>;
}
export default function SummaryPage() { return <Suspense fallback={<p>Đang tải...</p>}><SummaryContent /></Suspense>; }
