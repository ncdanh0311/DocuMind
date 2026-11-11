'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { apiService, getErrorMessage } from '@/lib/api';
import type { Notebook } from '@/types';
import FlashcardDeck from '@/components/notebooks/FlashcardDeck';

function FlashcardsContent() {
  const params = useSearchParams();
  const initial = params.get('notebookId') || '';
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [selected, setSelected] = useState(initial);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    apiService.getNotebooks().then(items => { if (active) { setNotebooks(items); setSelected(previous => { const candidate = initial || previous; return items.some(item => item.notebook_id === candidate) ? candidate : items[0]?.notebook_id || ''; }); } }).catch(err => { if (active) setError(getErrorMessage(err)); });
    return () => { active = false; };
  }, [initial]);
  return <main className="max-w-5xl mx-auto space-y-6 pb-12">
    <h1 className="font-outfit text-3xl font-bold">Thẻ học và ôn tập</h1>
    <p>Tự tạo thẻ từ kiến thức của bạn. Thẻ và tiến độ được lưu chung trên web và điện thoại.</p>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <label className="block">Sổ tay<select value={selected} onChange={event => setSelected(event.target.value)} className="block border rounded-xl p-3 mt-2 max-w-full"><option value="">Chọn sổ tay</option>{notebooks.map(item => <option key={item.notebook_id} value={item.notebook_id}>{item.title}</option>)}</select></label>
    {!selected && <p>Hãy tạo hoặc chọn một sổ tay để bắt đầu học.</p>}
    {selected && <FlashcardDeck key={selected} notebookId={selected} />}
  </main>;
}

export default function FlashcardsPage() {
  return <Suspense fallback={<p role="status">Đang tải bộ thẻ…</p>}><FlashcardsContent /></Suspense>;
}
