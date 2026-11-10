'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Image from 'next/image';
import Link from 'next/link';
import { apiService, getErrorMessage } from '@/lib/api';
import { useNotebooks } from '@/contexts/NotebookContext';
import CreateNotebookModal from '@/components/notebooks/CreateNotebookModal';
import DocumentReader from '@/components/notebooks/DocumentReader';
import NotebookHistory from '@/components/notebooks/NotebookHistory';
import StorageUsageView from '@/components/notebooks/StorageUsageView';
import { useAppConfig } from '@/lib/useAppConfig';
import { CATEGORY_LABELS, selectDocuments, type SortOrder } from '@/lib/management';
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
  ChevronRight,
  PlusCircle,
  X
} from 'lucide-react';

export default function NotebookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const notebookId = params.id as string;
  const { refreshNotebooks } = useNotebooks();

  const [notebook, setNotebook] = useState<Notebook | null>(null);
  const [reading, setReading] = useState<DocumentItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { aiEnabled } = useAppConfig();
  const [editingNotebook, setEditingNotebook] = useState(false);
  const [renaming, setRenaming] = useState<DocumentItem | null>(null);
  const [renameTitle, setRenameTitle] = useState('');
  const [renameError, setRenameError] = useState<string | null>(null);
  const [renamingBusy, setRenamingBusy] = useState(false);
  const [query, setQuery] = useState('');
  const [extension, setExtension] = useState('all');
  const [status, setStatus] = useState('all');
  const [sort, setSort] = useState<SortOrder>('newest');
  const visibleDocuments = selectDocuments(documents, query, extension, status, sort);
  const context = useRef(notebookId);
  const loadVersion = useRef(0);
  const invalidate = useCallback(() => { context.current = ''; loadVersion.current++; }, []);

  // Text Note Modal State
  const [isTextModalOpen, setIsTextModalOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState('');
  const [noteContent, setNoteContent] = useState('');
  const [noteLoading, setNoteLoading] = useState(false);
  const [noteError, setNoteError] = useState<string | null>(null);

  // Load Notebook & Documents
  const loadData = useCallback(async (showLoading = true) => {
    if (context.current !== notebookId) return;
    const request = ++loadVersion.current;
    if (showLoading) setLoading(true);
    try {
      const [nbData, docsData] = await Promise.all([
        apiService.getNotebook(notebookId),
        apiService.getDocuments(notebookId),
      ]);
      if (context.current !== notebookId || loadVersion.current !== request) return;
      setError(null);
      setNotebook(nbData);
      setDocuments(docsData);
    } catch (err: unknown) {
      if (context.current === notebookId && loadVersion.current === request) setError(getErrorMessage(err));
    } finally {
      if (showLoading && context.current === notebookId && loadVersion.current === request) setLoading(false);
    }
  }, [notebookId]);

  useEffect(() => {
    context.current = notebookId;
    setNotebook(null); setDocuments([]); setQuery(''); setExtension('all'); setStatus('all');
    setRenaming(null); setRenamingBusy(false); setEditingNotebook(false); setUploading(false); setNoteLoading(false);
    loadData(true);
    return invalidate;
  }, [loadData, notebookId, invalidate]);

  // Polling logic matching mobile's _checkProcessingStatus: poll every 3 seconds if any doc is processing
  useEffect(() => {
    const hasProcessing = documents.some(
      (doc) => doc.status === 'processing' || doc.status === 'uploaded'
    );
    if (!aiEnabled || !hasProcessing) return;

    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => { await loadData(false); if (!stopped) timer = setTimeout(poll, 3000); };
    timer = setTimeout(poll, 3000);

    return () => { stopped = true; clearTimeout(timer); };
  }, [documents, loadData, aiEnabled]);

  // Handle File Upload
  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      await apiService.uploadDocument(notebookId, file, (percent) => {
        if (context.current === notebookId) setUploadProgress(percent);
      });
      if (context.current !== notebookId) return;
      await loadData(false);
      await refreshNotebooks();
    } catch (err: unknown) {
      if (context.current !== notebookId) return;
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Không thể tải lên tài liệu. Vui lòng kiểm tra lại định dạng file.');
    } finally {
      if (context.current === notebookId) setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // Handle Create Text Document
  const handleCreateTextDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteTitle.trim() || !noteContent.trim()) {
      setNoteError('Vui lòng nhập tiêu đề và nội dung ghi chú.');
      return;
    }

    setNoteLoading(true);
    setNoteError(null);
    try {
      await apiService.createDocumentFromText(notebookId, noteTitle.trim(), noteContent.trim());
      if (context.current !== notebookId) return;
      setNoteTitle('');
      setNoteContent('');
      setIsTextModalOpen(false);
      if (context.current !== notebookId) return;
      await loadData(false);
      await refreshNotebooks();
    } catch (err: unknown) {
      if (context.current !== notebookId) return;
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setNoteError(axiosErr.response?.data?.detail || 'Không thể tạo ghi chú văn bản.');
    } finally {
      if (context.current === notebookId) setNoteLoading(false);
    }
  };

  // Handle Delete Document
  const handleDeleteDocument = async (docId: string, fileName: string) => {
    if (!confirm(`Bạn có chắc muốn xóa tài liệu "${fileName}" không?`)) return;
    try {
      await apiService.deleteDocument(docId);
      if (context.current !== notebookId) return;
      setDocuments((prev) => prev.filter((d) => (d.document_id || d.id) !== docId));
      await refreshNotebooks();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      alert(axiosErr.response?.data?.detail || 'Không thể xóa tài liệu');
    }
  };

  // Handle Delete Notebook
  const handleDeleteNotebook = async () => {
    if (!confirm('Xóa sổ tay và toàn bộ tài liệu bên trong? Thao tác này không thể hoàn tác.')) return;
    try {
      await apiService.deleteNotebook(notebookId);
      await refreshNotebooks();
      if (context.current === notebookId) router.push('/notebooks');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      alert(axiosErr.response?.data?.detail || 'Không thể xóa vở bài tập');
    }
  };

  const getBadgeInfo = (fileType?: string) => {
    switch (fileType) {
      case 'pdf':
        return { bg: 'bg-[#FFEBEE]', text: 'text-[#E53935]', label: 'PDF' };
      case 'docx':
        return { bg: 'bg-[#E3F2FD]', text: 'text-[#1E88E5]', label: 'DOCX' };
      case 'txt':
        return { bg: 'bg-[#FFF8E1]', text: 'text-[#F57F17]', label: 'TXT' };
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
              <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#E6F7F1] text-[#26A69A] capitalize">
                {notebook ? CATEGORY_LABELS[notebook.category] : 'Chủ đề'}
              </span>
            </div>
            <p className="text-xs text-[#8E9DAE] font-medium mt-1">
              {documents.length} tài liệu • {aiEnabled ? 'Có thể xử lý bằng AI' : 'Đã lưu trên hệ thống'}
            </p>
          </div>
        </div>

        {notebook?.description && <p className="text-sm text-gray-600 whitespace-pre-wrap">{notebook.description}</p>}
        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          <button onClick={() => setEditingNotebook(true)} disabled={!notebook} className="px-4 py-2 rounded-xl border text-sm">Chỉnh sửa sổ tay</button>
          {aiEnabled ? <Link
            href={`/ai-chat?notebookId=${notebookId}`}
            className="flex-1 md:flex-none px-4 py-2.5 rounded-xl bg-[#E6F7F1] hover:bg-[#D2EFE6] text-[#26A69A] text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer shadow-2xs"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat với AI</span>
          </Link> : <button disabled className="px-4 py-2 rounded-xl border opacity-50">Chat với AI</button>}
          {aiEnabled ? <Link
            href={`/summary?notebookId=${notebookId}`}
            className="flex-1 md:flex-none px-4 py-2.5 rounded-xl bg-[#FFF8E1] hover:bg-[#FFE082] text-[#B78103] text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer shadow-2xs"
          >
            <Sparkles className="w-4 h-4" />
            <span>Tóm tắt</span>
          </Link> : <button disabled className="px-4 py-2 rounded-xl border opacity-50">Tóm tắt</button>}
          <button
            onClick={handleDeleteNotebook}
            className="p-2.5 rounded-xl border border-[#FFCDD2] text-[#EF5350] hover:bg-[#FFEBEE] transition-all cursor-pointer"
            title="Xóa vở bài tập này"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {!aiEnabled && <p role="status" className="text-sm text-gray-600">Tính năng AI đang tạm hoãn. Bạn vẫn có thể quản lý sổ tay và lưu tài liệu.</p>}
      <StorageUsageView refreshKey={documents.map(item => item.document_id).join(',')} />
      <Link href={`/flashcards?notebookId=${notebookId}`} className="inline-block border rounded-xl p-3">Thẻ học và ôn tập</Link>
      <NotebookHistory notebookId={notebookId} />
      {reading && <DocumentReader id={reading.document_id} name={reading.file_name} onClose={() => { setReading(null); void loadData(false); }} />}
      {error && (
        <div className="p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Zone & Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Upload File Zone */}
        <div
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-3xl p-6 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[160px] ${
            uploading
              ? 'border-[#26A69A] bg-[#E6F7F1]/30'
              : 'border-[#D2EFE6] hover:border-[#26A69A] hover:bg-[#F9FCFA] bg-white'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={(e) => handleFileUpload(e.target.files)}
            className="hidden"
          />
          {uploading ? (
            <div className="space-y-3 w-full max-w-xs">
              <Loader2 className="w-8 h-8 animate-spin text-[#26A69A] mx-auto" />
              <div className="text-xs font-bold text-[#2D3E50]">Đang tải lên ({uploadProgress}%)...</div>
              <div className="w-full h-2 bg-[#EAEFEA] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#26A69A] transition-all duration-300 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <div className="w-12 h-12 rounded-2xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center mb-3">
                <UploadCloud className="w-6 h-6" />
              </div>
              <h4 className="font-outfit font-bold text-sm text-[#2D3E50]">
                Tải lên tài liệu PDF, DOCX hoặc TXT
              </h4>
              <p className="text-xs text-[#8E9DAE] mt-1">
                Bấm vào đây để lưu file PDF, DOCX hoặc TXT (tối đa 25 MB)
              </p>
            </>
          )}
        </div>

        {/* Text Note Creation Zone */}
        <div
          onClick={() => setIsTextModalOpen(true)}
          className="border-2 border-dashed border-[#D2EFE6] hover:border-[#26A69A] hover:bg-[#F9FCFA] bg-white rounded-3xl p-6 text-center transition-all cursor-pointer flex flex-col items-center justify-center min-h-[160px]"
        >
          <div className="w-12 h-12 rounded-2xl bg-[#D6F0FF] text-[#0088CC] flex items-center justify-center mb-3">
            <PlusCircle className="w-6 h-6" />
          </div>
          <h4 className="font-outfit font-bold text-sm text-[#2D3E50]">
            Tạo ghi chú từ văn bản thuần
          </h4>
          <p className="text-xs text-[#8E9DAE] mt-1">
            Lưu trực tiếp nội dung bài học hoặc ghi chú của bạn
          </p>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 lg:p-8 shadow-xs">
        <h3 className="font-outfit font-bold text-lg text-[#2D3E50] mb-4">
          Danh sách tài liệu ({documents.length})
        </h3>

        <div className="flex flex-wrap gap-3 mb-5">
          <input aria-label="Tìm tài liệu" placeholder="Tìm theo tên tài liệu..." value={query} onChange={event => setQuery(event.target.value)} className="p-2 rounded-xl border" />
          <select aria-label="Định dạng" value={extension} onChange={event => setExtension(event.target.value)} className="p-2 rounded-xl border"><option value="all">Mọi định dạng</option><option value="pdf">PDF</option><option value="docx">DOCX</option><option value="txt">TXT</option></select>
          <select aria-label="Trạng thái" value={status} onChange={event => setStatus(event.target.value)} className="p-2 rounded-xl border"><option value="all">Mọi trạng thái</option><option value="uploaded">Đã lưu</option><option value="processing">Đang xử lý</option><option value="ready">Sẵn sàng</option><option value="error">Lỗi</option></select>
          <select aria-label="Sắp xếp tài liệu" value={sort} onChange={event => setSort(event.target.value as SortOrder)} className="p-2 rounded-xl border"><option value="newest">Mới nhất</option><option value="oldest">Cũ nhất</option><option value="name">Tên A–Z</option></select>
        </div>
        {loading ? (
          <div className="py-12 text-center text-[#8E9DAE] flex flex-col items-center justify-center gap-2">
            <Loader2 className="w-6 h-6 animate-spin text-[#26A69A]" />
            <span className="text-xs font-medium">Đang tải danh sách tài liệu...</span>
          </div>
        ) : visibleDocuments.length === 0 ? (
          <div className="py-12 text-center text-[#8E9DAE]">
            <FileText className="w-10 h-10 mx-auto mb-2 text-[#B0BEC5]" />
            <p className="text-sm font-semibold text-[#2D3E50]">{documents.length ? 'Không có tài liệu phù hợp bộ lọc' : 'Chưa có tài liệu nào trong sổ tay này'}</p>
            <p className="text-xs text-[#8E9DAE] mt-1">
              Hãy tải lên tài liệu PDF hoặc tạo ghi chú văn bản ở trên để bắt đầu nghiên cứu.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-[#F5F8F5]">
            {visibleDocuments.map((doc) => {
              const docId = doc.document_id || doc.id || '';
              const badge = getBadgeInfo(doc.file_type);
              const isReady = doc.status === 'ready';

              return (
                <div
                  key={docId}
                  className="py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-outfit font-extrabold text-xs shrink-0 ${badge.bg} ${badge.text}`}>
                      {badge.label}
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-inter font-bold text-sm text-[#2D3E50] truncate group-hover:text-[#26A69A] transition-colors">
                        {doc.file_name || doc.title}
                      </h4>
                      <div className="flex items-center gap-2 mt-1 text-xs text-[#8E9DAE]">
                        <span>
                          {doc.uploaded_at
                            ? new Date(doc.uploaded_at).toLocaleDateString('vi-VN')
                            : 'Mới đây'}
                        </span>
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
                    <button className="text-sm p-2 border rounded-lg" onClick={() => setReading(doc)}>Đọc tài liệu</button>
                    {doc.status === 'error' && aiEnabled ? <button className="text-xs text-red-600 p-2" onClick={async () => {
                      try { await apiService.reprocessDocument(docId); await loadData(); }
                      catch { setError('Không thể xử lý lại tài liệu.'); }
                    }}>Xử lý lại</button> : isReady ? (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E6F7F1] text-[#26A69A] text-xs font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Sẵn sàng</span>
                      </div>
                    ) : !aiEnabled || doc.status === 'uploaded' ? <span className="text-xs text-gray-600">{doc.status === 'error' ? 'Lỗi' : doc.status === 'processing' ? 'Xử lý đang tạm hoãn' : 'Đã lưu'}</span> : (
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFF8E1] text-[#F57F17] text-xs font-semibold">
                        <Clock className="w-3.5 h-3.5 animate-spin" />
                        <span>Đang xử lý</span>
                      </div>
                    )}

                    <button aria-label={`Đổi tên ${doc.file_name}`} className="text-sm p-2 border rounded-lg" onClick={() => { setRenaming(doc); setRenameError(null); setRenameTitle(doc.file_name.replace(/\.[^.]+$/, '')); }}>Đổi tên</button>
                    <button
                      onClick={() => handleDeleteDocument(docId, doc.file_name || doc.title || 'tài liệu')}
                      className="p-2 rounded-xl text-[#B0BEC5] hover:text-[#EF5350] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
                      title="Xóa tài liệu"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CreateNotebookModal isOpen={editingNotebook} notebook={notebook} onClose={() => setEditingNotebook(false)} onCreated={() => { loadData(false); refreshNotebooks(); }} />
      {renaming && <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-6"><form aria-label="Đổi tên tài liệu" className="bg-white rounded-2xl p-6 space-y-4 max-w-lg w-full" onSubmit={async event => {
        event.preventDefault(); if (renamingBusy) return; setRenamingBusy(true);
        try { await apiService.renameDocument(renaming.document_id, renameTitle.trim()); if (context.current !== notebookId) return; setRenaming(null); await loadData(false); }
        catch (err) { if (context.current === notebookId) setRenameError(getErrorMessage(err)); }
        finally { if (context.current === notebookId) setRenamingBusy(false); }
      }}><h3 className="font-bold">Đổi tên tài liệu</h3>{renameError && <p role="alert" className="text-red-700">{renameError}</p>}<label>Tên mới<input aria-label="Tên tài liệu mới" required maxLength={200} value={renameTitle} onChange={event => setRenameTitle(event.target.value)} className="border rounded-xl p-3 w-full" /></label><p className="text-xs text-gray-500">Giữ nguyên định dạng .{renaming.file_name.split('.').pop()}</p><div className="flex gap-4"><button type="submit" disabled={renamingBusy} className="p-2 bg-[#26A69A] text-white rounded-xl">Lưu tên</button><button type="button" disabled={renamingBusy} onClick={() => setRenaming(null)}>Hủy</button></div></form></div>}
      {/* Modal: Thêm Ghi Chú Văn Bản Thuần */}
      {isTextModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg bg-white rounded-3xl shadow-2xl border border-[#EAEFEA] overflow-hidden">
            <div className="px-6 py-5 border-b border-[#F5F8F5] flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-[#D6F0FF] text-[#0088CC] flex items-center justify-center">
                  <PlusCircle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">Tạo ghi chú văn bản</h3>
                  <p className="text-xs text-[#8E9DAE]">Nội dung sẽ được trích xuất và xử lý bằng AI</p>
                </div>
              </div>
              <button
                onClick={() => setIsTextModalOpen(false)}
                className="p-1.5 rounded-full hover:bg-gray-100 text-[#8E9DAE] hover:text-[#2D3E50] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTextDoc} className="p-6 space-y-4">
              {noteError && (
                <div className="p-3 rounded-xl bg-[#FFEBEE] text-[#C62828] text-xs font-medium">
                  {noteError}
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
                  Tiêu đề ghi chú
                </label>
                <input
                  type="text"
                  required
                  value={noteTitle}
                  onChange={(e) => setNoteTitle(e.target.value)}
                  placeholder="VD: Khái niệm Attention, Tóm tắt bài giảng..."
                  className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE] outline-hidden transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
                  Nội dung ghi chú
                </label>
                <textarea
                  required
                  rows={6}
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Nhập nội dung kiến thức, câu hỏi hoặc văn bản cần nghiên cứu..."
                  className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl p-4 text-sm text-[#2D3E50] placeholder-[#8E9DAE] outline-hidden transition-all resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsTextModalOpen(false)}
                  className="px-4 py-2.5 rounded-xl border border-[#EAEFEA] text-xs font-bold text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-gray-50 transition-all cursor-pointer"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={noteLoading}
                  className="px-5 py-2.5 rounded-xl bg-[#26A69A] hover:bg-[#1E877B] text-white text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-60"
                >
                  {noteLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : (
                    <span>Lưu ghi chú</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
