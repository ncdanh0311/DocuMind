'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { QuickActionItem } from '@/types';

export default function QuickActions() {
  const actions: QuickActionItem[] = [
    {
      id: 'qa-1',
      key: 'action_summary',
      title: 'Tóm tắt tài liệu',
      subtitle: 'BARTpho & ViT5',
      icon: '/assets/icons/actions/icon-actions-summary.png',
      href: '/summary',
      badge: 'Nhanh',
    },
    {
      id: 'qa-2',
      key: 'action_ai_chat',
      title: 'Chat với AI',
      subtitle: 'Hỏi đáp PhoBERT RAG',
      icon: '/assets/icons/actions/icon-actions-ai-chat.png',
      href: '/ai-chat',
      badge: 'Hot',
    },
    {
      id: 'qa-3',
      key: 'action_flashcard',
      title: 'Flashcards',
      subtitle: 'Ôn tập kiến thức',
      icon: '/assets/icons/actions/icon-actions-flashcards.png',
      href: '/flashcards',
    },
    {
      id: 'qa-4',
      key: 'action_more',
      title: 'Vở bài tập',
      subtitle: 'Tất cả chủ đề',
      icon: '/assets/icons/actions/icon-action-more.png',
      href: '/notebooks',
    },
  ];

  return (
    <section className="mb-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {actions.map((item) => (
          <Link
            key={item.id}
            href={item.href}
            className="group relative bg-white hover:bg-linear-to-b hover:from-white hover:to-[#F4FAF8] border border-[#EAEFEA] hover:border-[#26A69A]/40 rounded-2xl p-5 transition-all duration-300 hover:shadow-md hover:-translate-y-1 cursor-pointer flex flex-col items-center text-center"
          >
            {item.badge && (
              <span className="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#E6F7F1] text-[#26A69A]">
                {item.badge}
              </span>
            )}

            {/* 3D Action Icon matching mobile */}
            <div className="relative w-16 h-16 mb-3 transition-transform duration-300 group-hover:scale-110">
              <Image
                src={item.icon}
                alt={item.title}
                fill
                className="object-contain"
              />
            </div>

            <h3 className="font-inter font-bold text-sm text-[#2D3E50] group-hover:text-[#26A69A] transition-colors">
              {item.title}
            </h3>
            <p className="text-[11px] text-[#8E9DAE] font-medium mt-0.5">
              {item.subtitle}
            </p>
          </Link>
        ))}
      </div>
    </section>
  );
}
