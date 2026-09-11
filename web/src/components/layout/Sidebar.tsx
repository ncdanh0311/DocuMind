'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  BookOpen, 
  Sparkles, 
  Clock, 
  User, 
  Plus, 
  FolderPlus,
  Compass
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
}

export default function Sidebar() {
  const pathname = usePathname();

  const navItems: NavItem[] = [
    {
      label: 'Trang chủ',
      href: '/',
      icon: <Home className="w-5 h-5" />,
    },
    {
      label: 'Vở bài tập',
      href: '/notebooks',
      icon: <BookOpen className="w-5 h-5" />,
    },
    {
      label: 'AI Chat & Tóm tắt',
      href: '/ai-chat',
      icon: <Sparkles className="w-5 h-5 text-[#26A69A]" />,
      badge: 'Pro',
    },
    {
      label: 'Tài liệu gần đây',
      href: '/recent',
      icon: <Clock className="w-5 h-5" />,
    },
    {
      label: 'Cá nhân & Cài đặt',
      href: '/profile',
      icon: <User className="w-5 h-5" />,
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#EAEFEA] flex flex-col h-screen sticky top-0 z-30 select-none shadow-[2px_0_12px_rgba(38,166,154,0.03)]">
      {/* Brand Header */}
      <div className="p-6 pb-5 flex items-center gap-3 border-b border-[#F5F8F5]">
        <div className="relative w-11 h-11 rounded-2xl overflow-hidden shadow-sm bg-[#E6F7F1] flex items-center justify-center p-1 border border-[#D2EFE6]">
          <Image
            src="/assets/mascot/mascot-owl-avatar-circle.png"
            alt="DocuMind Mascot"
            width={40}
            height={40}
            className="object-contain"
            priority
          />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="font-outfit font-extrabold text-xl text-[#2D3E50] tracking-tight">
              Docu<span className="text-[#26A69A]">Mind</span>
            </h1>
          </div>
          <p className="text-xs text-[#8E9DAE] font-medium">Trợ lý học tập AI</p>
        </div>
      </div>

      {/* Action Button: Create Notebook */}
      <div className="px-5 pt-5 pb-2">
        <button
          onClick={() => alert('Chức năng tạo sổ tay mới')}
          className="w-full bg-[#26A69A] hover:bg-[#1E877B] active:scale-[0.98] text-white font-medium py-3 px-4 rounded-2xl shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2 text-sm group cursor-pointer"
        >
          <div className="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center group-hover:rotate-90 transition-transform duration-300">
            <Plus className="w-4 h-4 text-white" />
          </div>
          <span>Tạo sổ tay mới</span>
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold text-[#8E9DAE] uppercase tracking-wider">
          Điều hướng chính
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-[#E6F7F1] text-[#26A69A] font-semibold shadow-xs'
                  : 'text-[#2D3E50] hover:bg-[#F5F8F5] hover:text-[#26A69A]'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className={isActive ? 'text-[#26A69A]' : 'text-[#8E9DAE]'}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-[#26A69A] text-white">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Storage & User Status Card */}
      <div className="p-4 border-t border-[#F5F8F5]">
        <div className="bg-[#F7FAF7] border border-[#EAEFEA] rounded-2xl p-3.5">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-[#2D3E50]">Dung lượng nghiên cứu</span>
            <span className="text-[11px] font-bold text-[#26A69A]">4 / 10 Vở</span>
          </div>
          {/* Progress Bar */}
          <div className="w-full h-2 bg-[#E0E8E4] rounded-full overflow-hidden">
            <div 
              className="h-full bg-[#26A69A] rounded-full transition-all duration-500" 
              style={{ width: '40%' }}
            />
          </div>
          <p className="text-[11px] text-[#8E9DAE] mt-2 flex items-center gap-1">
            <span>💡 Mẹo: Tải PDF để AI tóm tắt tự động</span>
          </p>
        </div>
      </div>
    </aside>
  );
}
