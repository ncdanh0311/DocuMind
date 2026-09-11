'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { apiService, MOCK_NOTEBOOKS } from '@/lib/api';
import { Notebook, NotebookCategory } from '@/types';
import CreateNotebookModal from '@/components/notebooks/CreateNotebookModal';
import { Plus, Search, Trash2, BookOpen, Layers, ArrowRight, Loader2 } from 'lucide-react';

export default function NotebooksPage() {
  const [notebooks, setNotebooks] = useState<Notebook[]>(MOCK_NOTEBOOKS);
  const [filteredNotebooks, setFilteredNotebooks] = useState<Notebook[]>(MOCK_NOTEBOOKS);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchNotebooks = async () => {
    setLoading(true);
    try {
      const data = await apiService.getNotebooks();
      if (data && data.length > 0) {
        setNotebooks(data);
      }
    } catch (err) {
      console.error('Failed to fetch notebooks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotebooks();
  }, []);

  useEffect(() => {
    let result = notebooks;
    if (selectedCategory !== 'all') {
      result = result.filter((nb) => nb.category === selectedCategory);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter((nb) => nb.title.toLowerCase().includes(q));
    }
    setFilteredNotebooks(result);
  }, [selectedCategory, searchQuery, notebooks]);

  const handleDelete = async (e: React.MouseEvent, id: string, title: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm(`Bạn có chắc chắn muốn xóa vở bài tập "${title}" không?`)) return;

    try {
      await apiService.deleteNotebook(id);
      setNotebooks((prev) => prev.filter((nb) => (nb.notebook_id || nb.id) !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Không thể xóa vở bài tập');
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
          onClick={() => setIsCreateOpen(true)}
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
                  : 'text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-[#F5F8F5]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative flex items-center bg-[#F5F7F7] rounded-xl px-3 h-10 md:w-72">
          <Search className="w-4 h-4 text-[#8E9DAE] shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm vở bài tập..."
            className="w-full bg-transparent border-none outline-hidden px-2.5 text-xs text-[#2D3E50] placeholder-[#8E9DAE]"
          />
        </div>
      </div>

      {/* Grid of Notebooks */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-[#8E9DAE] gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-[#26A69A]" />
          <p className="text-sm font-medium">Đang tải danh sách vở bài tập...</p>
        </div>
      ) : filteredNotebooks.length === 0 ? (
        <div className="py-20 flex flex-col items-center justify-center text-center bg-white rounded-3xl border border-[#EAEFEA] p-8">
          <div className="w-16 h-16 rounded-2xl bg-[#E6F7F1] flex items-center justify-center text-[#26A69A] mb-3">
            <BookOpen className="w-8 h-8" />
          </div>
          <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">Chưa có vở bài tập nào</h3>
          <p className="text-xs text-[#8E9DAE] max-w-sm mt-1 mb-5">
            Bắt đầu tổ chức tài liệu học tập của bạn bằng cách tạo vở bài tập đầu tiên
          </p>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="bg-[#26A69A] hover:bg-[#1E877B] text-white text-xs font-bold py-2.5 px-5 rounded-xl transition-all cursor-pointer"
          >
            Tạo vở bài tập ngay
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredNotebooks.map((nb) => {
            const nbId = nb.notebook_id || nb.id || '';
            return (
              <Link
                key={nbId}
                href={`/notebooks/${nbId}`}
                className="group bg-white hover:bg-[#F9FCFA] border border-[#EAEFEA] hover:border-[#26A69A]/40 rounded-3xl p-5 transition-all duration-300 hover:shadow-md cursor-pointer flex flex-col justify-between min-h-[170px]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3.5">
                    <div className="relative w-14 h-14 shrink-0 transition-transform group-hover:scale-105">
                      <Image
                        src={nb.icon || '/assets/icons/categories/icon-category-study.png'}
                        alt={nb.title}
                        fill
                        className="object-contain"
                      />
                    </div>
                    <div>
                      <h4 className="font-outfit font-bold text-base text-[#2D3E50] group-hover:text-[#26A69A] transition-colors line-clamp-1">
                        {nb.title}
                      </h4>
                      <span className="text-xs text-[#8E9DAE] font-medium mt-0.5 block">
                        {nb.count ?? 0} tài liệu
                      </span>
                    </div>
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={(e) => handleDelete(e, nbId, nb.title)}
                    className="p-2 rounded-xl text-gray-400 hover:text-[#E53935] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
                    title="Xóa vở bài tập"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="pt-4 border-t border-[#F5F8F5] flex items-center justify-between mt-4">
                  <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-[#E6F7F1] text-[#26A69A]">
                    {nb.category || 'Môn học'}
                  </span>
                  <div className="text-xs font-bold text-[#26A69A] flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                    <span>Mở sổ tay</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Modal */}
      <CreateNotebookModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onCreated={fetchNotebooks}
      />
    </div>
  );
}
