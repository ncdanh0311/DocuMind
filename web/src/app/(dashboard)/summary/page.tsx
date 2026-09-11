'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { apiService, MOCK_NOTEBOOKS } from '@/lib/api';
import { Notebook } from '@/types';
import ReactMarkdown from 'react-markdown';
import { 
  Sparkles, 
  BookOpen, 
  Loader2, 
  Copy, 
  Check, 
  FileText, 
  RefreshCw,
  Layers,
  ArrowRight
} from 'lucide-react';

function SummaryContent() {
  const searchParams = useSearchParams();
  const initialNotebookId = searchParams.get('notebookId') || '';

  const [notebooks, setNotebooks] = useState<Notebook[]>(MOCK_NOTEBOOKS);
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>(initialNotebookId);
  const [selectedModel, setSelectedModel] = useState<'vit5' | 'bartpho'>('vit5');
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadNotebooks() {
      try {
        const data = await apiService.getNotebooks();
        if (data && data.length > 0) {
          setNotebooks(data);
          if (!selectedNotebookId) {
            setSelectedNotebookId(data[0].notebook_id || data[0].id || '');
          }
        }
      } catch (err) {
        console.error('Failed to load notebooks:', err);
      }
    }
    loadNotebooks();
  }, []);

  const handleSummarize = async () => {
    if (!selectedNotebookId || loading) return;

    setLoading(true);
    setError(null);
    try {
      const res = await apiService.summarizeNotebook(selectedNotebookId, selectedModel);
      setSummary(res.summary || 'Không tìm thấy nội dung tóm tắt.');
    } catch (err: any) {
      console.error('Summary error:', err);
      setError(
        err.response?.data?.detail ||
          'Không thể thực hiện tóm tắt. Vui lòng đảm bảo bạn đã tải lên tài liệu trong vở bài tập này và dịch vụ AI đang hoạt động.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const selectedNotebook = notebooks.find(
    (n) => n.notebook_id === selectedNotebookId || n.id === selectedNotebookId
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
            Tóm tắt tài liệu tự động
          </h2>
          <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#E6F7F1] text-[#26A69A]">
            Deep Learning
          </span>
        </div>
        <p className="text-xs text-[#8E9DAE] font-medium mt-1">
          Rút trích các ý chính và luận điểm quan trọng từ toàn bộ tài liệu bằng mô hình ViT5 và BARTpho
        </p>
      </div>

      {/* Control Panel: Sổ tay & Model */}
      <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 shadow-xs grid grid-cols-1 md:grid-cols-12 gap-6 items-end">
        {/* Notebook Selector */}
        <div className="md:col-span-6">
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Chọn vở bài tập nguồn
          </label>
          <select
            value={selectedNotebookId}
            onChange={(e) => setSelectedNotebookId(e.target.value)}
            className="w-full bg-[#F5F7F7] hover:bg-[#EAEFEA] text-sm font-semibold text-[#2D3E50] py-3 px-4 rounded-2xl appearance-none outline-hidden border border-transparent focus:border-[#26A69A] transition-all cursor-pointer"
          >
            {notebooks.map((nb) => {
              const id = nb.notebook_id || nb.id || '';
              return (
                <option key={id} value={id}>
                  {nb.title} ({nb.count ?? 0} tài liệu)
                </option>
              );
            })}
          </select>
        </div>

        {/* Model Selector */}
        <div className="md:col-span-3">
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Mô hình tóm tắt
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value as 'vit5' | 'bartpho')}
            className="w-full bg-[#F5F7F7] hover:bg-[#EAEFEA] text-sm font-semibold text-[#2D3E50] py-3 px-4 rounded-2xl appearance-none outline-hidden border border-transparent focus:border-[#26A69A] transition-all cursor-pointer"
          >
            <option value="vit5">ViT5 (Khuyên dùng - VietAI)</option>
            <option value="bartpho">BARTpho (VinAI)</option>
          </select>
        </div>

        {/* Action Button */}
        <div className="md:col-span-3">
          <button
            onClick={handleSummarize}
            disabled={loading || !selectedNotebookId}
            className="w-full bg-[#26A69A] hover:bg-[#1E877B] text-white font-bold h-12 rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-xs cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Đang tóm tắt...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span>Bắt đầu tóm tắt</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-xs font-medium">
          {error}
        </div>
      )}

      {/* Summary Output Area */}
      {summary ? (
        <div className="bg-white border border-[#EAEFEA] rounded-3xl p-8 shadow-xs animate-in fade-in duration-300">
          <div className="flex items-center justify-between pb-4 mb-6 border-b border-[#F5F8F5]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">
                  Bản tóm tắt: {selectedNotebook?.title}
                </h3>
                <span className="text-xs text-[#8E9DAE]">
                  Tạo bởi mô hình {selectedModel.toUpperCase()}
                </span>
              </div>
            </div>

            <button
              onClick={handleCopy}
              className="px-4 py-2 rounded-xl bg-[#F5F7F7] hover:bg-[#E6F7F1] text-xs font-bold text-[#2D3E50] hover:text-[#26A69A] flex items-center gap-2 transition-all cursor-pointer"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-[#26A69A]" />
                  <span className="text-[#26A69A]">Đã sao chép</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4" />
                  <span>Sao chép tóm tắt</span>
                </>
              )}
            </button>
          </div>

          <div className="prose max-w-none prose-p:my-2 prose-headings:text-[#2D3E50] prose-p:text-[#2D3E50] prose-li:text-[#2D3E50] leading-relaxed">
            <ReactMarkdown>{summary}</ReactMarkdown>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-[#EAEFEA] p-12 text-center">
          <div className="relative w-32 h-32 mx-auto mb-4 opacity-90">
            <Image
              src="/assets/mascot/mascot-owl-reading-on-books.png"
              alt="Mascot On Books"
              fill
              className="object-contain"
            />
          </div>
          <h4 className="font-outfit font-bold text-lg text-[#2D3E50]">
            Sẵn sàng tóm tắt kiến thức
          </h4>
          <p className="text-xs text-[#8E9DAE] max-w-md mx-auto mt-1">
            Chọn vở bài tập và bấm nút "Bắt đầu tóm tắt" để nhận bản tóm tắt súc tích, cô đọng nhất từ các tài liệu của bạn.
          </p>
        </div>
      )}
    </div>
  );
}

export default function SummaryPage() {
  return (
    <Suspense fallback={
      <div className="p-16 flex items-center justify-center bg-white rounded-3xl border border-[#EAEFEA]">
        <Loader2 className="w-8 h-8 animate-spin text-[#26A69A]" />
      </div>
    }>
      <SummaryContent />
    </Suspense>
  );
}
