'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { apiService } from '@/lib/api';
import { useNotebooks } from '@/contexts/NotebookContext';
import { Plus, Search, Trash2, BookOpen, Layers, ArrowRight } from 'lucide-react';

export default function NotebooksPage() {
  const { notebooks, loading, refreshNotebooks, openCreateModal } = useNotebooks();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredNotebooks = useMemo(() => {
    let result = notebooks;
    if (selectedCategory !== 'all') {
      result = result.filter((nb) => nb.category === selectedCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter((nb) => nb.title.toLowerCase().includes(q));
    }
    return result;
  }, [notebooks, selectedCategory, searchQuery]);

  const handleDelete = async (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm(`Bạn có chắc chắn muốn xóa vở bài tập "${title}" không?`)) return;

    try {
      await apiService.deleteNotebook(id);
      await refreshNotebooks();
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      alert(axiosErr.response?.data?.detail || 'Không thể xóa vở bài tập');
    }
  };

  const categories = [
    { key: 'all', label: 'Tất cả' },
    { key: 'study', label: 'Học tập' },
    { key: 'project', label: 'Dự án' },
    { key: 'research', label: 'Nghiên cứu' },
    { key: 'personal', label: 'Cá nhân' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-300 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
            Vở bài tập của bạn
          </h2>
          <p className="text-xs text-[#8E9DAE] font-medium mt-1">
            Quản lý các môn học, tài liệu nghiên cứu và dự án học tập
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="bg-[#26A69A] hover:bg-[#1E877B] text-white font-bold py-2.5 px-4 rounded-2xl shadow-sm hover:shadow-md transition-all flex items-center gap-2 text-xs cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo vở bài tập mới</span>
        </button>
      </div>

      {/* Filter and Search Toolbar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-white p-3 rounded-2xl border border-[#EAEFEA]">
        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
          {categories.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setSelectedCategory(cat.key)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
                selectedCategory === cat.key
                  ? 'bg-[#26A69A] text-white shadow-xs'
                  : 'bg-[#F7FAF7] text-[#8E9DAE] hover:text-[#2D3E50]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative flex items-center bg-[#F7FAF7] rounded-xl px-3 h-10 w-full md:w-72 border border-transparent focus-within:border-[#26A69A] focus-within:bg-white transition-all">
          <Search className="w-4 h-4 text-[#8E9DAE] shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm vở bài tập..."
            className="w-full bg-transparent border-none outline-hidden px-2 text-xs text-[#2D3E50] placeholder-[#8E9DAE]"
          />
        </div>
      </div>

      {/* Notebook Cards Grid */}
      {loading ? (
        <div className="py-20 text-center text-[#8E9DAE]">
          <BookOpen className="w-8 h-8 animate-bounce mx-auto mb-2 text-[#26A69A]" />
          <p className="text-sm font-medium">Đang tải danh sách vở bài tập...</p>
        </div>
      ) : filteredNotebooks.length === 0 ? (
        <div className="py-16 bg-white border border-[#EAEFEA] rounded-3xl text-center p-8">
          <div className="w-16 h-16 rounded-full bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center mx-auto mb-4">
            <BookOpen className="w-8 h-8" />
          </div>
          <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">
            Không tìm thấy vở bài tập nào
          </h3>
          <p className="text-xs text-[#8E9DAE] mt-1.5 max-w-sm mx-auto">
            {searchQuery
              ? `Không có kết quả nào phù hợp với từ khóa "${searchQuery}". Hãy thử tìm kiếm khác.`
              : 'Hãy bắt đầu tạo vở bài tập mới để tải lên tài liệu và sử dụng AI nghiên cứu.'}
          </p>
          <button
            onClick={openCreateModal}
            className="mt-5 inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#26A69A] text-white text-xs font-bold shadow-md hover:bg-[#1E877B] transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Tạo vở bài tập ngay</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredNotebooks.map((nb) => {
            const nbId = nb.notebook_id || nb.id || '';
            return (
              <Link
                key={nbId}
                href={`/notebooks/${nbId}`}
                className="group relative bg-white border border-[#EAEFEA] hover:border-[#26A69A]/40 rounded-3xl p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="relative w-14 h-14 shrink-0 p-2 rounded-2xl bg-[#F7FAF7] border border-[#EAEFEA]">
                      <Image
                        src={nb.icon || '/assets/icons/categories/icon-category-study.png'}
                        alt={nb.title}
                        fill
                        className="object-contain p-2"
                      />
                    </div>

                    <button
                      onClick={(e) => handleDelete(e, nbId, nb.title)}
                      className="p-2 rounded-xl text-[#B0BEC5] hover:text-[#EF5350] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
                      title="Xóa vở bài tập"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <h3 className="font-outfit font-bold text-lg text-[#2D3E50] group-hover:text-[#26A69A] transition-colors mb-2 line-clamp-1">
                    {nb.title}
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-[#8E9DAE]">
                    <span className="flex items-center gap-1">
                      <Layers className="w-3.5 h-3.5" />
                      <span>{nb.count ?? 0} tài liệu</span>
                    </span>
                    <span>•</span>
                    <span className="capitalize">{nb.category || 'Học tập'}</span>
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-[#F5F8F5] flex items-center justify-between text-xs font-bold text-[#26A69A]">
                  <span>Mở không gian học tập</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
