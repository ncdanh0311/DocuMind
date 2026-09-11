'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { apiService, MOCK_NOTEBOOKS } from '@/lib/api';
import { Notebook, DocumentItem } from '@/types';
import { 
  ArrowLeft, 
  UploadCloud, 
  Trash2, 
  FileText, 
  Sparkles, 
  MessageSquare, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  Loader2,
  ChevronRight
} from 'lucide-react';

export default function NotebookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const notebookId = params.id as string;

  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load Notebook & Documents
  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [nbData, docsData] = await Promise.allSettled([
        apiService.getNotebook(notebookId),
        apiService.getDocuments(notebookId),
      ]);

      if (nbData.status === 'fulfilled') {
        setNotebook(nbData.value);
      } else {
        const fallback = MOCK_NOTEBOOKS.find((n) => n.id === notebookId || n.notebook_id === notebookId);
        if (fallback) setNotebook(fallback);
      }

      if (docsData.status === 'fulfilled') {
        setDocuments(docsData.value);
      }
    } catch (err) {
      console.error('Failed to load notebook detail:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadData(true);
  }, [notebookId]);

  // Polling logic matching mobile's _checkProcessingStatus: poll every 3 seconds if any doc is processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (doc) => doc.status === 'processing' || doc.status === 'uploaded'
    );
    if (!hasProcessing) return;

    const timer = setInterval(() => {
      loadData(false);
    }, 3000);

    return () => clearInterval(timer);
  }, [documents]);

  // Handle File Upload
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      await apiService.uploadDocument(notebookId, file, (percent) => {
        setUploadProgress(percent);
      });
      await loadData(false);
    } catch (err: any) {
      console.error('Upload failed:', err);
      setError(err.response?.data?.detail || 'Không thể tải lên tài liệu. Vui lòng kiểm tra lại định dạng file.');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Handle Delete Document
  const handleDeleteDocument = async (docId: string, fileName: string) => {
    if (!confirm(`Bạn có chắc muốn xóa tài liệu "${fileName}" không?`)) return;
    try {
      await apiService.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => (d.document_id || d.id) !== docId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xóa tài liệu');
    }
  };

  // Handle Delete Notebook
  const handleDeleteNotebook = async () => {
    if (!confirm(`Bạn có chắc muốn xóa toàn bộ vở bài tập này không?`)) return;
    try {
      await apiService.deleteNotebook(notebookId);
      router.push('/notebooks');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xóa vở bài tập');
    }
  };

  const getBadgeInfo = (fileType?: string) => {
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
      {/* Back and Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs font-semibold text-[#8E9DAE]">
        <Link href="/notebooks" className="hover:text-[#26A69A] flex items-center gap-1 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Danh sách vở bài tập</span>
        </Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-[#2D3E50]">{notebook?.title || 'Chi tiết sổ tay'}</span>
      </div>

      {/* Notebook Header Card */}
      <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 lg:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-xs">
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16 shrink-0">
            <Image
              src={notebook?.icon || '/assets/icons/categories/icon-category-study.png'}
              alt="Category Icon"
              fill
              className="object-contain"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-outfit text-2xl lg:text-3xl font-extrabold text-[#2D3E50]">
                {notebook?.title || 'Đang tải...'}
              </h2>
              <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-[#E6F7F1] text-[#26A69A]">
                {notebook?.category || 'Sổ tay'}
              </span>
            </div>
            <p className="text-xs text-[#8E9DAE] font-medium mt-1">
              {documents.length} tài liệu trong sổ tay này
            </p>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          <Link
            href={`/ai-chat?notebookId=${notebookId}`}
            className="flex-1 md:flex-none px-4 py-2.5 rounded-xl bg-[#E6F7F1] hover:bg-[#26A69A] text-[#26A69A] hover:text-white font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer shadow-2xs"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat với AI</span>
          </Link>
          <Link
            href={`/summary?notebookId=${notebookId}`}
            className="flex-1 md:flex-none px-4 py-2.5 rounded-xl bg-[#D6F0FF] hover:bg-[#0088CC] text-[#0088CC] hover:text-white font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-4 h-4" />
            <span>Tóm tắt</span>
          </Link>
          <button
            onClick={handleDeleteNotebook}
            className="p-2.5 rounded-xl text-gray-400 hover:text-[#E53935] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
            title="Xóa vở bài tập này"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Drag & Drop Upload Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        onDrop={(e) => {
          e.preventDefault();
          e.stopPropagation();
          handleFileUpload(e.dataTransfer.files);
        }}
        className={`border-2 border-dashed rounded-3xl p-8 text-center transition-all cursor-pointer ${
          uploading
            ? 'border-[#26A69A] bg-[#E6F7F1]/30 cursor-not-allowed'
            : 'border-[#D2EFE6] hover:border-[#26A69A] hover:bg-white bg-white/60 shadow-2xs'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFileUpload(e.target.files)}
          accept=".pdf,.docx,.txt"
          className="hidden"
          disabled={uploading}
        />

        <div className="flex flex-col items-center justify-center max-w-md mx-auto">
          <div className="w-14 h-14 rounded-2xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center mb-3">
            {uploading ? (
              <Loader2 className="w-6 h-6 animate-spin" />
            ) : (
              <UploadCloud className="w-7 h-7" />
            )}
          </div>

          <h3 className="font-outfit font-bold text-base text-[#2D3E50]">
            {uploading ? 'Đang tải lên và phân tích tài liệu...' : 'Kéo thả file vào đây hoặc bấm để chọn'}
          </h3>
          <p className="text-xs text-[#8E9DAE] mt-1">
            Hỗ trợ tài liệu định dạng PDF, DOCX, TXT. IBM Docling sẽ tự động OCR và trích xuất cấu trúc.
          </p>

          {uploading && (
            <div className="w-full max-w-xs mt-4">
              <div className="w-full h-2 bg-[#EAEFEA] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#26A69A] rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <span className="text-[11px] font-bold text-[#26A69A] mt-1 block">
                {uploadProgress}%
              </span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Documents List */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-outfit text-xl font-bold text-[#2D3E50]">
            Danh sách tài liệu ({documents.length})
          </h3>
        </div>

        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center text-[#8E9DAE] gap-2">
            <Loader2 className="w-7 h-7 animate-spin text-[#26A69A]" />
            <span className="text-xs font-medium">Đang tải tài liệu...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="bg-white rounded-3xl border border-[#EAEFEA] p-10 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#F5F7F7] text-[#8E9DAE] flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6" />
            </div>
            <h4 className="font-outfit font-bold text-sm text-[#2D3E50]">Chưa có tài liệu nào</h4>
            <p className="text-xs text-[#8E9DAE] mt-1">
              Hãy tải lên tài liệu đầu tiên ở khung bên trên để bắt đầu nghiên cứu cùng AI.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const docId = doc.document_id || doc.id || '';
              const badge = getBadgeInfo(doc.file_type);
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
                        <span>{doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString('vi-VN') : 'Mới'}</span>
                        {doc.file_size && (
                          <>
                            <span>•</span>
                            <span>{(doc.file_size / 1024 / 1024).toFixed(1)} MB</span>
                          </>
                        )}
                        {doc.page_count && (
                          <>
                            <span>•</span>
                            <span>{doc.page_count} trang</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Status & Actions */}
                  <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end shrink-0">
                    {isReady ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E6F7F1] text-[#26A69A] text-xs font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Sẵn sàng</span>
                      </div>
                    ) : isProcessing ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFF8E1] text-[#F57F17] text-xs font-semibold animate-pulse">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Đang phân tích Docling...</span>
                      </div>
                    ) : (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFEBEE] text-[#C62828] text-xs font-semibold">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>Lỗi xử lý</span>
                      </div>
                    )}

                    <div className="flex items-center gap-1">
                      <Link
                        href={`/ai-chat?notebookId=${notebookId}&docId=${docId}`}
                        className="p-2 rounded-xl text-[#8E9DAE] hover:text-[#26A69A] hover:bg-[#E6F7F1] transition-colors"
                        title="Chat với tài liệu này"
                      >
                        <MessageSquare className="w-4 h-4" />
                      </Link>
                      <button
                        onClick={() => handleDeleteDocument(docId, doc.file_name || doc.title || '')}
                        className="p-2 rounded-xl text-gray-400 hover:text-[#E53935] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
                        title="Xóa tài liệu"
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
    </div>
  );
}
