'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Notebook } from '@/types';
import { ChevronRight, Plus } from 'lucide-react';

interface NotebookGridProps {
  notebooks: Notebook[];
}

export default function NotebookGrid({ notebooks }: NotebookGridProps) {
  const getCategoryColor = (category?: string) => {
    switch (category) {
      case 'study':
        return 'bg-[#E6F7F1] text-[#26A69A]';
      case 'project':
        return 'bg-[#D6F0FF] text-[#0088CC]';
      case 'research':
        return 'bg-[#FFE1E6] text-[#E91E63]';
      case 'personal':
        return 'bg-[#FFE9B3] text-[#B78103]';
      default:
        return 'bg-[#E6F7F1] text-[#26A69A]';
    }
  };

  return (
    <section className="mb-8">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-outfit text-xl font-bold text-[#2D3E50]">
          Vở bài tập gần đây
        </h3>
        <Link
          href="/notebooks"
          className="text-sm font-bold text-[#26A69A] hover:text-[#1E877B] flex items-center gap-1 transition-colors"
        >
          <span>Xem tất cả</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Grid of Notebooks */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {notebooks.map((nb) => {
          const nbId = nb.notebook_id || nb.id || '';
          return (
            <Link
              key={nbId}
              href={`/notebooks/${nbId}`}
              className="group bg-white hover:bg-[#F9FCFA] border border-[#EAEFEA] hover:border-[#26A69A]/40 rounded-2xl p-4 transition-all duration-300 hover:shadow-md cursor-pointer flex items-center gap-3.5"
            >
              {/* 3D Category Icon */}
              <div className="relative w-12 h-12 shrink-0 transition-transform duration-300 group-hover:scale-105">
                <Image
                  src={nb.icon || '/assets/icons/categories/icon-category-study.png'}
                  alt={nb.title}
                  fill
                  className="object-contain"
                />
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <h4 className="font-outfit font-bold text-sm text-[#2D3E50] truncate group-hover:text-[#26A69A] transition-colors">
                  {nb.title}
                </h4>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-[#8E9DAE] font-medium">
                    {nb.count ?? 0} tài liệu
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${getCategoryColor(nb.category)}`}>
                    {nb.category || 'Môn học'}
                  </span>
                </div>
              </div>
            </Link>
          );
        })}

        {/* Create New Card */}
        <Link
          href="/notebooks"
          className="border-2 border-dashed border-[#D2EFE6] hover:border-[#26A69A] hover:bg-[#E6F7F1]/30 rounded-2xl p-4 transition-all duration-300 flex items-center justify-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center group-hover:scale-110 transition-transform">
            <Plus className="w-5 h-5" />
          </div>
          <div className="text-left">
            <div className="font-outfit font-bold text-sm text-[#2D3E50] group-hover:text-[#26A69A]">Thêm vở bài tập</div>
            <div className="text-xs text-[#8E9DAE]">Tạo chủ đề mới</div>
          </div>
        </Link>
      </div>
    </section>
  );
}
