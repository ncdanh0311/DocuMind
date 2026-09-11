'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { UploadCloud, Sparkles } from 'lucide-react';

export default function HomeBanner() {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-linear-to-r from-[#E6F7F1] via-[#F2FAF7] to-[#EAF5FC] border border-[#D2EFE6] p-7 md:p-9 shadow-xs mb-8">
      {/* Decorative background clouds & botanical leaves */}
      <div className="absolute -left-10 -top-8 w-44 h-44 opacity-25 pointer-events-none">
        <Image
          src="/assets/decor/clouds/decor-cloud-mint-01.png"
          alt="Cloud Decor"
          fill
          className="object-contain"
        />
      </div>
      <div className="absolute right-40 -bottom-10 w-40 h-40 opacity-30 pointer-events-none rotate-45">
        <Image
          src="/assets/decor/botanical/decor-leaf-sprig-03.png"
          alt="Leaf Decor"
          fill
          className="object-contain"
        />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Text and CTAs */}
        <div className="max-w-xl space-y-3.5 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 border border-[#26A69A]/20 text-[#26A69A] text-xs font-semibold shadow-2xs">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Trợ lý Deep Learning tiếng Việt</span>
          </div>

          <h2 className="font-outfit text-2xl md:text-3xl font-extrabold text-[#2D3E50] leading-tight">
            Nâng tầm nghiên cứu với <span className="text-[#26A69A]">DocuMind AI</span>
          </h2>

          <p className="text-sm text-[#8E9DAE] font-medium leading-relaxed">
            Tải lên tài liệu PDF, DOCX để trích xuất cấu trúc thông minh với IBM Docling, tóm tắt tự động cùng BARTpho & ViT5 và hỏi đáp RAG đa tài liệu.
          </p>

          <div className="pt-2 flex flex-wrap items-center justify-center md:justify-start gap-3">
            <Link
              href="/notebooks"
              className="bg-[#26A69A] hover:bg-[#1E877B] text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-xs hover:shadow-md transition-all flex items-center gap-2 cursor-pointer"
            >
              <UploadCloud className="w-4.5 h-4.5" />
              <span>Khám phá Sổ tay & Tài liệu</span>
            </Link>
            <Link
              href="/ai-chat"
              className="bg-white hover:bg-[#F5F8F5] text-[#2D3E50] border border-[#D2EFE6] text-sm font-semibold px-5 py-2.5 rounded-xl transition-all cursor-pointer"
            >
              <span>Trải nghiệm AI Chat</span>
            </Link>
          </div>
        </div>

        {/* Mascot reading book illustration */}
        <div className="relative w-44 h-44 md:w-56 md:h-52 shrink-0 drop-shadow-md">
          <Image
            src="/assets/mascot/mascot-owl-reading-book.png"
            alt="DocuMind Owl Reading Book"
            fill
            className="object-contain"
            priority
          />
        </div>
      </div>
    </div>
  );
}
