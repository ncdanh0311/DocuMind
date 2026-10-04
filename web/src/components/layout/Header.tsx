'use client';

import React, { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/lib/api';
import { Search, Bell, SlidersHorizontal, X, User as UserIcon, Lock, LogOut, ChevronDown } from 'lucide-react';
import NotificationDrawer from '@/components/notifications/NotificationDrawer';

interface HeaderProps {
  onSearch?: (query: string) => void;
}

export default function Header({ onSearch }: HeaderProps) {
  const { user, logout } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [unreadCount, setUnreadCount] = useState(0);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Greeting display name: strictly based on real user, fallback to "bạn"
  const displayName = user?.full_name?.trim() || user?.email?.split('@')[0] || 'bạn';

  // Load notifications unread count
  const loadNotificationsCount = async () => {
    try {
      const notifs = await apiService.getNotifications();
      const unread = notifs.filter((n) => !n.is_read).length;
      setUnreadCount(unread);
    } catch {
      // Ignore background notification fetch errors
    }
  };

  useEffect(() => {
    loadNotificationsCount();
    const interval = setInterval(loadNotificationsCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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
    <>
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
          {/* Pill Search Bar */}
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
            onClick={() => setIsNotifOpen(true)}
            className="relative w-11 h-11 rounded-full bg-[#F5F7F7] hover:bg-[#E6F7F1] text-[#2D3E50] hover:text-[#26A69A] flex items-center justify-center transition-all cursor-pointer"
            title="Thông báo"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-2 right-2 min-w-4 h-4 px-1 bg-[#EF5350] border-2 border-white rounded-full text-[10px] font-bold text-white flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* User Profile Avatar Link & Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-3 pl-2 border-l border-[#EAEFEA] hover:opacity-85 transition-opacity cursor-pointer"
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
                <div className="text-xs font-bold text-[#2D3E50] leading-tight flex items-center gap-1">
                  <span>{user?.full_name || user?.email || 'Tài khoản'}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-[#8E9DAE]" />
                </div>
                <div className="text-[11px] text-[#26A69A] font-semibold">
                  {user?.email || 'Người học'}
                </div>
              </div>
            </button>

            {/* Dropdown Menu */}
            {isDropdownOpen && (
              <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-xl border border-[#EAEFEA] py-2 z-30 animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="px-4 py-2 border-b border-[#F5F8F5]">
                  <p className="text-xs font-bold text-[#2D3E50] truncate">{user?.full_name || 'Người dùng'}</p>
                  <p className="text-[11px] text-[#8E9DAE] truncate">{user?.email}</p>
                </div>
                <Link
                  href="/profile"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-xs font-medium text-[#2D3E50] hover:bg-[#F5F8F5] hover:text-[#26A69A] transition-colors"
                >
                  <UserIcon className="w-4 h-4 text-[#8E9DAE]" />
                  <span>Hồ sơ cá nhân</span>
                </Link>
                <Link
                  href="/profile"
                  onClick={() => setIsDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2.5 text-xs font-medium text-[#2D3E50] hover:bg-[#F5F8F5] hover:text-[#26A69A] transition-colors"
                >
                  <Lock className="w-4 h-4 text-[#8E9DAE]" />
                  <span>Đổi mật khẩu</span>
                </Link>
                <div className="border-t border-[#F5F8F5] my-1" />
                <button
                  onClick={() => {
                    setIsDropdownOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2.5 px-4 py-2.5 text-xs font-bold text-[#EF5350] hover:bg-[#FFEBEE] transition-colors text-left cursor-pointer"
                >
                  <LogOut className="w-4 h-4 text-[#EF5350]" />
                  <span>Đăng xuất</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Notification Drawer */}
      <NotificationDrawer
        isOpen={isNotifOpen}
        onClose={() => setIsNotifOpen(false)}
        onNotificationsRead={() => setUnreadCount(0)}
      />
    </>
  );
}
