'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { 
  Sparkles, 
  RotateCw, 
  ArrowLeft, 
  ArrowRight, 
  CheckCircle2, 
  HelpCircle,
  Layers,
  BookOpen
} from 'lucide-react';

interface Flashcard {
  id: number;
  question: string;
  answer: string;
  category: string;
}

const SAMPLE_CARDS: Flashcard[] = [
  {
    id: 1,
    question: 'Cơ chế Self-Attention trong kiến trúc Transformer hoạt động như thế nào?',
    answer: 'Self-Attention tính toán mối tương quan giữa tất cả các từ trong một câu bằng cách ánh xạ Query (Q), Key (K), và Value (V). Công thức: Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) * V.',
    category: 'Deep Learning',
  },
  {
    id: 2,
    question: 'Điểm khác biệt cốt lõi giữa PhoBERT và XLM-RoBERTa trong xử lý tiếng Việt là gì?',
    answer: 'PhoBERT được huấn luyện chuyên sâu trên kho ngữ liệu tiếng Việt quy mô lớn với bộ tách từ (word-level tokenization) đặc thù của tiếng Việt, trong khi XLM-RoBERTa là mô hình đa ngôn ngữ dùng BPE cấp độ subword.',
    category: 'Vietnamese NLP',
  },
  {
    id: 3,
    question: 'IBM Docling xử lý tài liệu PDF phức tạp như thế nào?',
    answer: 'Docling sử dụng các mạng nơ-ron nhận diện bố cục (Layout Analysis), trích xuất cấu trúc bảng biểu, hình ảnh và chuyển đổi văn bản sang định dạng Markdown nguyên vẹn cấu trúc phân cấp.',
    category: 'Document AI',
  },
];

export default function FlashcardsPage() {
  const [cards] = useState<Flashcard[]>(SAMPLE_CARDS);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [rememberedCount, setRememberedCount] = useState(0);

  const currentCard = cards[currentIndex];

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % cards.length);
  };

  const handlePrev = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
  };

  const handleMarkRemembered = () => {
    setRememberedCount((prev) => prev + 1);
    handleNext();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div className="text-center">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#FFE9B3] text-[#B78103] text-xs font-bold mb-2">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Ôn tập thông minh</span>
        </div>
        <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
          Flashcards Ghi Nhớ Kiến Thức
        </h2>
        <p className="text-xs text-[#8E9DAE] font-medium mt-1">
          Lật thẻ để kiểm tra mức độ ghi nhớ các khái niệm cốt lõi từ tài liệu học tập
        </p>
      </div>

      {/* Progress */}
      <div className="flex items-center justify-between text-xs font-bold text-[#8E9DAE] px-2">
        <span>Thẻ {currentIndex + 1} / {cards.length}</span>
        <span className="text-[#26A69A]">Đã ghi nhớ: {rememberedCount}</span>
      </div>

      {/* 3D Flip Card Container */}
      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="w-full h-96 perspective-1000 cursor-pointer"
      >
        <div
          className={`relative w-full h-full rounded-3xl transition-transform duration-500 transform-style-3d shadow-md hover:shadow-xl ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
        >
          {/* Front Face: Question */}
          <div className="absolute inset-0 bg-white border-2 border-[#D2EFE6] rounded-3xl p-8 flex flex-col justify-between backface-hidden">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#E6F7F1] text-[#26A69A]">
                {currentCard.category}
              </span>
              <span className="text-xs font-bold text-[#8E9DAE] flex items-center gap-1">
                <RotateCw className="w-3.5 h-3.5" />
                <span>Bấm để lật xem đáp án</span>
              </span>
            </div>

            <div className="my-auto text-center px-6">
              <div className="text-xs font-bold text-[#26A69A] uppercase tracking-wider mb-2">
                Câu hỏi / Khái niệm
              </div>
              <h3 className="font-outfit text-2xl font-bold text-[#2D3E50] leading-snug">
                {currentCard.question}
              </h3>
            </div>

            <div className="text-center text-xs text-[#8E9DAE]">
              💡 Hãy thử nhớ lại định nghĩa trước khi lật mặt sau
            </div>
          </div>

          {/* Back Face: Answer */}
          <div className="absolute inset-0 bg-linear-to-br from-[#E6F7F1] to-white border-2 border-[#26A69A] rounded-3xl p-8 flex flex-col justify-between backface-hidden rotate-y-180">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold px-3 py-1 rounded-full bg-[#26A69A] text-white">
                Đáp án giải thích
              </span>
              <span className="text-xs font-bold text-[#26A69A] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Kiến thức chuẩn xác</span>
              </span>
            </div>

            <div className="my-auto text-left px-6">
              <p className="font-inter text-base text-[#2D3E50] leading-relaxed font-medium">
                {currentCard.answer}
              </p>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-[#D2EFE6]">
              <span className="text-xs text-[#8E9DAE]">Bấm thẻ để lật lại câu hỏi</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleMarkRemembered();
                }}
                className="px-4 py-1.5 rounded-xl bg-[#26A69A] text-white text-xs font-bold hover:bg-[#1E877B] transition-colors"
              >
                Đã thuộc thẻ này
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="flex items-center justify-center gap-4 pt-4">
        <button
          onClick={handlePrev}
          className="p-3.5 rounded-2xl bg-white border border-[#EAEFEA] hover:border-[#26A69A] text-[#2D3E50] hover:text-[#26A69A] transition-all cursor-pointer shadow-xs"
          title="Thẻ trước"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <button
          onClick={() => setIsFlipped(!isFlipped)}
          className="px-6 py-3.5 rounded-2xl bg-[#26A69A] hover:bg-[#1E877B] text-white text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center gap-2 cursor-pointer"
        >
          <RotateCw className="w-4 h-4" />
          <span>Lật thẻ</span>
        </button>

        <button
          onClick={handleNext}
          className="p-3.5 rounded-2xl bg-white border border-[#EAEFEA] hover:border-[#26A69A] text-[#2D3E50] hover:text-[#26A69A] transition-all cursor-pointer shadow-xs"
          title="Thẻ tiếp theo"
        >
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
