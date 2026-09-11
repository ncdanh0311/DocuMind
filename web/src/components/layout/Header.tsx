'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Search, Bell, SlidersHorizontal, X } from 'lucide-react';

interface HeaderProps {
  onSearch?: (query: string) => void;
}

export default function Header({ onSearch }: HeaderProps) {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [hasNotifications, setHasNotifications] = useState(true);

  const displayName = user?.full_name?.trim().split(' ').pop() || 'Danh';

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (onSearch) onSearch(val);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    if (onSearch) onSearch('');
  };

  return (
    <header className="h-20 bg-white/80 backdrop-blur-md border-b border-[#EAEFEA] px-8 flex items-center justify-between sticky top-0 z-20 transition-all">
      {/* Greeting Title */}
      <div>
        <h2 className="font-outfit text-2xl font-bold text-[#2D3E50] tracking-tight">
          Xin chào, <span className="text-[#26A69A]">{displayName}!</span> 👋
        </h2>
        <p className="text-xs text-[#8E9DAE] font-medium mt-0.5">
          Hôm nay bạn muốn nghiên cứu tài liệu gì nào?
        </p>
      </div>

      {/* Center / Right: Search Bar & Actions */}
      <div className="flex items-center gap-5">
        {/* Pill Search Bar (exact mobile styling) */}
        <div className="relative w-80 lg:w-96 flex items-center bg-[#F5F7F7] border border-transparent hover:border-[#D2EFE6] focus-within:border-[#26A69A] focus-within:bg-white rounded-full px-4 h-12 transition-all shadow-2xs">
          <Search className="w-4 h-4 text-[#8E9DAE] shrink-0" />
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Tìm kiếm vở bài tập, tài liệu..."
            className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE] font-inter"
          />
          {searchQuery ? (
            <button
              onClick={handleClearSearch}
              className="p-1 hover:bg-gray-200 rounded-full transition-colors cursor-pointer text-[#8E9DAE]"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <SlidersHorizontal className="w-4 h-4 text-[#8E9DAE] shrink-0 opacity-70" />
          )}
        </div>

        {/* Notification Bell */}
        <button
          onClick={() => setHasNotifications(false)}
          className="relative w-11 h-11 rounded-full bg-[#F5F7F7] hover:bg-[#E6F7F1] text-[#2D3E50] hover:text-[#26A69A] flex items-center justify-center transition-all cursor-pointer"
          title="Thông báo"
        >
          <Bell className="w-5 h-5" />
          {hasNotifications && (
            <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-[#EF5350] border-2 border-white rounded-full" />
          )}
        </button>

        {/* User Profile Avatar Link */}
        <Link
          href="/profile"
          className="flex items-center gap-3 pl-2 border-l border-[#EAEFEA] hover:opacity-85 transition-opacity"
        >
          <div className="relative w-10 h-10 rounded-full overflow-hidden border-2 border-[#26A69A]/30 bg-[#E6F7F1]">
            <Image
              src="/assets/mascot/mascot-owl-avatar-circle.png"
              alt="User Avatar"
              width={40}
              height={40}
              className="object-cover"
            />
          </div>
          <div className="hidden xl:block text-left">
            <div className="text-xs font-bold text-[#2D3E50] leading-tight">
              {user?.full_name || 'Danh Nguyen'}
            </div>
            <div className="text-[11px] text-[#26A69A] font-semibold">
              Sinh viên nghiên cứu
            </div>
          </div>
        </Link>
      </div>
    </header>
  );
}
