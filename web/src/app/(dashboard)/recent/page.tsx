'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { apiService, MOCK_RECENT_DOCUMENTS } from '@/lib/api';
import { DocumentItem } from '@/types';
import { 
  FileText, 
  Search, 
  MessageSquare, 
  Sparkles, 
  Trash2, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  Loader2,
  Filter
} from 'lucide-react';

export default function RecentDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>(MOCK_RECENT_DOCUMENTS);
  const [filteredDocs, setFilteredDocs] = useState<DocumentItem[]>(MOCK_RECENT_DOCUMENTS);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'ready' | 'processing'>('all');
  const [loading, setLoading] = useState(true);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiService.getRecentDocuments();
      if (data && data.length > 0) {
        setDocuments(data);
      }
    } catch (err) {
      console.error('Failed to fetch recent documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    let result = documents;
    if (statusFilter !== 'all') {
      result = result.filter((d) => d.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter((d) => (d.file_name || d.title || '').toLowerCase().includes(q));
    }
    setFilteredDocs(result);
  }, [statusFilter, searchQuery, documents]);

  const handleDelete = async (docId: string, title: string) => {
    if (!confirm(`Bạn có chắc muốn xóa tài liệu "${title}" không?`)) return;
    try {
      await apiService.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => (d.document_id || d.id) !== docId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xóa tài liệu');
    }
  };

  const getBadge = (fileType?: string) => {
    switch (fileType) {
      case 'pdf':
        return { bg: 'bg-[#FFEBEE]', text: 'text-[#E53935]', label: 'PDF' };
      case 'docx':
        return { bg: 'bg-[#E3F2FD]', text: 'text-[#1E88E5]', label: 'DOCX' };
      default:
        return { bg: 'bg-[#EDE7F6]', text: 'text-[#5E35B1]', label: (fileType || 'FILE').toUpperCase() };
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Header */}
      <div>
        <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
          Tài liệu nghiên cứu gần đây
        </h2>
        <p className="text-xs text-[#8E9DAE] font-medium mt-1">
          Theo dõi toàn bộ file PDF, DOCX bạn đã tải lên và trạng thái xử lý của AI
        </p>
      </div>

      {/* Toolbar */}
      <div className="bg-white p-4 rounded-3xl border border-[#EAEFEA] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* Status Filters */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              statusFilter === 'all'
                ? 'bg-[#26A69A] text-white shadow-xs'
                : 'text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-[#F5F8F5]'
            }`}
          >
            Tất cả ({documents.length})
          </button>
          <button
            onClick={() => setStatusFilter('ready')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              statusFilter === 'ready'
                ? 'bg-[#26A69A] text-white shadow-xs'
                : 'text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-[#F5F8F5]'
            }`}
          >
            Sẵn sàng
          </button>
          <button
            onClick={() => setStatusFilter('processing')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              statusFilter === 'processing'
                ? 'bg-[#26A69A] text-white shadow-xs'
                : 'text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-[#F5F8F5]'
            }`}
          >
            Đang phân tích
          </button>
        </div>

        {/* Search */}
        <div className="relative flex items-center bg-[#F5F7F7] rounded-xl px-3.5 h-11 md:w-80">
          <Search className="w-4 h-4 text-[#8E9DAE] shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tên tài liệu..."
            className="w-full bg-transparent border-none outline-hidden px-3 text-xs text-[#2D3E50] placeholder-[#8E9DAE]"
          />
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-[#8E9DAE] gap-2">
          <Loader2 className="w-7 h-7 animate-spin text-[#26A69A]" />
          <span className="text-xs font-medium">Đang tải danh sách tài liệu...</span>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="bg-white rounded-3xl border border-[#EAEFEA] p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#F5F7F7] text-[#8E9DAE] flex items-center justify-center mx-auto mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h4 className="font-outfit font-bold text-base text-[#2D3E50]">Không tìm thấy tài liệu phù hợp</h4>
          <p className="text-xs text-[#8E9DAE] mt-1">
            Thử thay đổi từ khóa tìm kiếm hoặc tải lên tài liệu mới trong các sổ tay của bạn.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredDocs.map((doc) => {
            const docId = doc.document_id || doc.id || '';
            const badge = getBadge(doc.file_type);
            const isReady = doc.status === 'ready';
            const isProcessing = doc.status === 'processing' || doc.status === 'uploaded';

            return (
              <div
                key={docId}
                className="bg-white hover:bg-[#F9FCFA] border border-[#EAEFEA] hover:border-[#26A69A]/30 rounded-2xl p-4.5 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-2xs group"
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-outfit font-extrabold text-xs shrink-0 ${badge.bg} ${badge.text}`}>
                    {badge.label}
                  </div>
                  <div className="min-w-0">
                    <h4 className="font-inter font-bold text-sm text-[#2D3E50] truncate group-hover:text-[#26A69A] transition-colors">
                      {doc.file_name || doc.title}
                    </h4>
                    <div className="flex items-center gap-2 mt-1 text-xs text-[#8E9DAE]">
                      <span className="font-medium text-[#26A69A]">{doc.notebook_title || 'Tài liệu nghiên cứu'}</span>
                      <span>•</span>
                      <span>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString('vi-VN') : 'Gần đây'}</span>
                      {doc.page_count && (
                        <>
                          <span>•</span>
                          <span>{doc.page_count} trang</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end shrink-0">
                  {isReady ? (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E6F7F1] text-[#26A69A] text-xs font-semibold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Sẵn sàng</span>
                    </div>
                  ) : isProcessing ? (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFF8E1] text-[#F57F17] text-xs font-semibold animate-pulse">
                      <Clock className="w-3.5 h-3.5" />
                      <span>Đang phân tích</span>
                    </div>
                  ) : (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFEBEE] text-[#C62828] text-xs font-semibold">
                      <AlertCircle className="w-3.5 h-3.5" />
                      <span>Lỗi</span>
                    </div>
                  )}

                  <div className="flex items-center gap-1">
                    <Link
                      href={`/ai-chat?notebookId=${doc.notebook_id}&docId=${docId}`}
                      className="p-2 rounded-xl text-[#8E9DAE] hover:text-[#26A69A] hover:bg-[#E6F7F1] transition-colors"
                      title="Hỏi AI về tài liệu này"
                    >
                      <MessageSquare className="w-4 h-4" />
                    </Link>
                    <button
                      onClick={() => handleDelete(docId, doc.file_name || doc.title || '')}
                      className="p-2 rounded-xl text-gray-400 hover:text-[#E53935] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
                      title="Xóa file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
