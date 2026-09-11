'use client';

import React from 'react';
import Link from 'next/link';
import { DocumentItem } from '@/types';
import { FileText, ChevronRight, MessageSquare, Sparkles, CheckCircle2, Clock } from 'lucide-react';

interface RecentNotesListProps {
  documents: DocumentItem[];
}

export default function RecentNotesList({ documents }: RecentNotesListProps) {
  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('vi-VN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getFileBadge = (fileType?: string) => {
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
    <section>
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-outfit text-xl font-bold text-[#2D3E50]">
          Ghi chú & Tài liệu gần đây
        </h3>
        <Link
          href="/recent"
          className="text-sm font-bold text-[#26A69A] hover:text-[#1E877B] flex items-center gap-1 transition-colors"
        >
          <span>Xem tất cả</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Documents List */}
      <div className="space-y-3">
        {documents.map((doc) => {
          const docId = doc.document_id || doc.id || '';
          const badge = getFileBadge(doc.file_type);
          const isReady = doc.status === 'ready';

          return (
            <div
              key={docId}
              className="bg-white hover:bg-[#F9FCFA] border border-[#EAEFEA] hover:border-[#26A69A]/30 rounded-2xl p-4 transition-all duration-200 hover:shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 group"
            >
              {/* File Info */}
              <div className="flex items-center gap-3.5 min-w-0">
                {/* File Type Pill */}
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-outfit font-extrabold text-xs shrink-0 ${badge.bg} ${badge.text}`}>
                  {badge.label}
                </div>

                {/* Details */}
                <div className="min-w-0">
                  <h4 className="font-inter font-bold text-sm text-[#2D3E50] truncate group-hover:text-[#26A69A] transition-colors">
                    {doc.file_name || doc.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-1 text-xs text-[#8E9DAE]">
                    <span className="font-medium text-[#26A69A]/90">
                      {doc.notebook_title || 'Tài liệu nghiên cứu'}
                    </span>
                    <span>•</span>
                    <span>{formatTime(doc.uploaded_at)}</span>
                    {doc.page_count && (
                      <>
                        <span>•</span>
                        <span>{doc.page_count} trang</span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Status and Action Buttons */}
              <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end shrink-0">
                {/* Status Badge */}
                {isReady ? (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#E6F7F1] text-[#26A69A] text-xs font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Sẵn sàng</span>
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFF8E1] text-[#F57F17] text-xs font-semibold animate-pulse">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Đang phân tích</span>
                  </div>
                )}

                {/* Quick Actions */}
                <div className="flex items-center gap-1.5">
                  <Link
                    href={`/ai-chat?notebookId=${doc.notebook_id}&docId=${docId}`}
                    className="p-2 rounded-xl text-[#8E9DAE] hover:text-[#26A69A] hover:bg-[#E6F7F1] transition-colors"
                    title="Chat với tài liệu này"
                  >
                    <MessageSquare className="w-4 h-4" />
                  </Link>
                  <Link
                    href={`/summary?notebookId=${doc.notebook_id}`}
                    className="p-2 rounded-xl text-[#8E9DAE] hover:text-[#26A69A] hover:bg-[#E6F7F1] transition-colors"
                    title="Tóm tắt tài liệu"
                  >
                    <Sparkles className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
