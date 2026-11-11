'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { QuickActionItem } from '@/types';

export default function QuickActions({ aiEnabled = false }: { aiEnabled?: boolean }) {
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

  return <section className="mb-8"><div className="grid grid-cols-2 md:grid-cols-4 gap-4">
    {actions.map(item => {
      const disabled = !aiEnabled && (item.key === 'action_summary' || item.key === 'action_ai_chat');
      const style = 'relative bg-white border border-[#EAEFEA] rounded-2xl p-5 flex flex-col items-center text-center';
      const content = <><div className="relative w-16 h-16 mb-3"><Image src={item.icon} alt="" fill sizes="64px" className="object-contain" /></div><h3 className="font-bold text-sm text-[#2D3E50]">{item.title}</h3><p className="text-xs text-gray-500 mt-1">{disabled ? 'AI đang tạm hoãn' : item.subtitle}</p></>;
      return disabled ? <button key={item.id} disabled className={style + ' opacity-60'}>{content}</button>
        : <Link key={item.id} href={item.href} className={style + ' hover:border-[#26A69A]'}>{content}</Link>;
    })}
  </div></section>;
}
