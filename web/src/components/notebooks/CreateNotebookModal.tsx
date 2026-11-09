'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import { apiService, getErrorMessage } from '@/lib/api';
import { X, Plus, Loader2, Check } from 'lucide-react';
import { Notebook, NotebookCategory } from '@/types';

interface CreateNotebookModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
  notebook?: Notebook | null;
}

interface CategoryOption {
  key: NotebookCategory;
  name: string;
  icon: string;
  bg: string;
  color: string;
}

const CATEGORIES: CategoryOption[] = [
  {
    key: 'study',
    name: 'Học tập',
    icon: '/assets/icons/categories/icon-category-study.png',
    bg: '#E6F7F1',
    color: '#26A69A',
  },
  {
    key: 'project',
    name: 'Dự án',
    icon: '/assets/icons/categories/icon-category-project.png',
    bg: '#D6F0FF',
    color: '#0088CC',
  },
  {
    key: 'research',
    name: 'Nghiên cứu',
    icon: '/assets/icons/categories/icon-category-research.png',
    bg: '#FFE1E6',
    color: '#E91E63',
  },
  {
    key: 'personal',
    name: 'Cá nhân',
    icon: '/assets/icons/categories/icon-category-personal.png',
    bg: '#FFE9B3',
    color: '#B78103',
  },
];

export default function CreateNotebookModal({ isOpen, onClose, onCreated, notebook }: CreateNotebookModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isPrivate, setPrivate] = useState(true);
  const generation = useRef(0);
  const invalidate = useCallback(() => { generation.current++; }, []);
  const [selectedCategory, setSelectedCategory] = useState<CategoryOption>(CATEGORIES[0]);
  const [showOnHome, setShowOnHome] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    generation.current++;
    setTitle(notebook?.title || ''); setDescription(notebook?.description || '');
    setPrivate(notebook?.is_private ?? true); setShowOnHome(notebook?.show_on_home ?? true);
    setSelectedCategory(CATEGORIES.find(item => item.key === notebook?.category) || CATEGORIES[3]);
    setError(null); setLoading(false);
    return invalidate;
  }, [isOpen, notebook, invalidate]);
  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Vui lòng nhập tên vở bài tập.');
      return;
    }

    const request = generation.current;
    setLoading(true);
    setError(null);
    try {
      const values = { title: title.trim(), description: description.trim(), category: selectedCategory.key,
        is_private: isPrivate, show_on_home: showOnHome,
        icon_path: notebook?.category === selectedCategory.key ? notebook.icon_path || selectedCategory.icon : selectedCategory.icon };
      if (notebook) await apiService.updateNotebook(notebook.notebook_id, values);
      else await apiService.createNotebook(values.title, values);
      if (generation.current !== request) return;
      setTitle('');
      onCreated();
      onClose();
    } catch (err: unknown) {
      if (generation.current === request) setError(getErrorMessage(err));
    } finally {
      if (generation.current === request) setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-[#EAEFEA]">
        {/* Header */}
        <div className="px-6 py-5 border-b border-[#F5F8F5] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">{notebook ? 'Chỉnh sửa sổ tay' : 'Tạo vở bài tập mới'}</h3>
              <p className="text-xs text-[#8E9DAE]">Tổ chức và quản lý tài liệu học tập của bạn</p>
            </div>
          </div>
          <button
            disabled={loading}
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-gray-100 text-[#8E9DAE] hover:text-[#2D3E50] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="p-3 rounded-xl bg-[#FFEBEE] text-[#C62828] text-xs font-medium">
              {error}
            </div>
          )}

          {/* Title Input */}
          <div>
            <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
              Tên vở bài tập
            </label>
            <input
              type="text"
              required
              maxLength={200}
              aria-label="Tên sổ tay"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="VD: Toán Cao Cấp, Deep Learning, v.v."
              className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE] outline-hidden transition-all"
            />
          </div>

          <label className="block text-sm">Mô tả
            <textarea aria-label="Mô tả" maxLength={1000} value={description} onChange={event => setDescription(event.target.value)} className="mt-2 w-full bg-[#F5F7F7] rounded-xl p-3" />
          </label>
          <label className="flex gap-2 text-sm"><input type="checkbox" checked={isPrivate} onChange={event => setPrivate(event.target.checked)} />Đánh dấu riêng tư</label>
          {/* Category Selection */}
          <div>
            <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
              Chủ đề & Icon
            </label>
            <div className="grid grid-cols-2 gap-3">
              {CATEGORIES.map((cat) => {
                const isSelected = selectedCategory.key === cat.key;
                return (
                  <button type="button" aria-pressed={selectedCategory.key === cat.key}
                    key={cat.key}
                    onClick={() => setSelectedCategory(cat)}
                    className={`p-3 rounded-2xl border-2 transition-all cursor-pointer flex items-center gap-3 ${
                      isSelected
                        ? 'border-[#26A69A] bg-[#E6F7F1]/40 shadow-xs'
                        : 'border-[#EAEFEA] hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="relative w-10 h-10 shrink-0">
                      <Image
                        src={cat.icon}
                        alt={cat.name}
                        fill
                        className="object-contain"
                      />
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <div className="text-xs font-bold text-[#2D3E50]">{cat.name}</div>
                      <div className="text-[10px] text-[#8E9DAE]">Mặc định</div>
                    </div>
                    {isSelected && (
                      <div className="w-5 h-5 rounded-full bg-[#26A69A] text-white flex items-center justify-center shrink-0">
                        <Check className="w-3 h-3" />
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Toggle Show on Home */}
          <div className="flex items-center justify-between p-3.5 rounded-2xl bg-[#F7FAF7] border border-[#EAEFEA]">
            <div>
              <div className="text-xs font-bold text-[#2D3E50]">Hiển thị ở trang chủ</div>
              <div className="text-[11px] text-[#8E9DAE]">Ghim sổ tay này lên đầu trang tổng quan</div>
            </div>
            <input
              type="checkbox"
              checked={showOnHome}
              onChange={(e) => setShowOnHome(e.target.checked)}
              className="w-5 h-5 text-[#26A69A] rounded-md accent-[#26A69A] cursor-pointer"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              disabled={loading}
            onClick={onClose}
              className="px-4 py-2.5 rounded-xl border border-[#EAEFEA] text-xs font-bold text-[#8E9DAE] hover:text-[#2D3E50] hover:bg-gray-50 transition-all cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-[#26A69A] hover:bg-[#1E877B] text-white text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Đang tạo...</span>
                </>
              ) : (
                <span>{notebook ? 'Lưu thay đổi' : 'Tạo sổ tay'}</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
