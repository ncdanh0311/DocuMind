'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { apiService } from '@/lib/api';
import { useNotebooks } from '@/contexts/NotebookContext';
import { ChatMessage } from '@/types';
import ReactMarkdown from 'react-markdown';
import { 
  Send, 
  Sparkles, 
  Trash2, 
  BookOpen, 
  Loader2, 
  Copy, 
  Check, 
  ChevronDown,
  Info,
  HelpCircle,
  Plus
} from 'lucide-react';

function AIChatContent() {
  const searchParams = useSearchParams();
  const initialNotebookId = searchParams.get('notebookId') || '';

  const { notebooks, openCreateModal } = useNotebooks();
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>(initialNotebookId);
  const [selectedModel, setSelectedModel] = useState<string>('phobert_qa');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-select first notebook if not set
  useEffect(() => {
    if (!selectedNotebookId && notebooks.length > 0) {
      setSelectedNotebookId(notebooks[0].notebook_id || notebooks[0].id || '');
    }
  }, [notebooks, selectedNotebookId]);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || !selectedNotebookId || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setLoading(true);

    try {
      const res = await apiService.askAI(selectedNotebookId, text.trim(), selectedModel);
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.answer || res.response || 'Đã xử lý thông tin từ tài liệu của bạn.',
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        citations: res.citations || [],
        model: selectedModel,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: unknown) {
      console.error('Chat error:', err);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: '⚠️ Không thể kết nối với dịch vụ AI hoặc sổ tay chưa có tài liệu nào sẵn sàng. Vui lòng đảm bảo bạn đã tải lên tài liệu trong sổ tay này.',
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClearHistory = () => {
    if (messages.length === 0) return;
    if (confirm('Bạn có chắc muốn xóa lịch sử đoạn chat này không?')) {
      setMessages([]);
    }
  };

  const selectedNotebook = notebooks.find(
    (n) => n.notebook_id === selectedNotebookId || n.id === selectedNotebookId
  );

  const sampleQuestions = [
    'Tóm tắt các ý chính trong các tài liệu của sổ tay này?',
    'Định nghĩa và công thức cốt lõi được đề cập là gì?',
    'Phân tích ưu và nhược điểm của phương pháp trong bài viết?',
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-130px)] animate-in fade-in duration-300">
      {/* Chat Header Toolbar */}
      <div className="bg-white border border-[#EAEFEA] rounded-2xl p-4 mb-4 flex flex-wrap items-center justify-between gap-4 shadow-2xs">
        <div className="flex flex-wrap items-center gap-3">
          {/* Notebook Selector */}
          <div className="relative">
            <select
              value={selectedNotebookId}
              onChange={(e) => {
                setSelectedNotebookId(e.target.value);
                setMessages([]);
              }}
              className="appearance-none bg-[#F5F7F7] border border-[#D2EFE6] rounded-xl pl-9 pr-9 py-2 text-xs font-bold text-[#2D3E50] focus:outline-hidden focus:border-[#26A69A] cursor-pointer"
            >
              {notebooks.length === 0 ? (
                <option value="">Chưa có sổ tay nào</option>
              ) : (
                notebooks.map((nb) => (
                  <option key={nb.notebook_id || nb.id} value={nb.notebook_id || nb.id}>
                    {nb.title} ({nb.count ?? 0} tài liệu)
                  </option>
                ))
              )}
            </select>
            <BookOpen className="w-4 h-4 text-[#26A69A] absolute left-3 top-2.5 pointer-events-none" />
            <ChevronDown className="w-3.5 h-3.5 text-[#8E9DAE] absolute right-3 top-3 pointer-events-none" />
          </div>

          {/* Model Selector */}
          <div className="flex items-center gap-1.5 bg-[#F5F7F7] p-1 rounded-xl border border-[#EAEFEA]">
            <button
              onClick={() => setSelectedModel('phobert_qa')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedModel === 'phobert_qa'
                  ? 'bg-white text-[#26A69A] shadow-2xs'
                  : 'text-[#8E9DAE] hover:text-[#2D3E50]'
              }`}
            >
              PhoBERT QA
            </button>
            <button
              onClick={() => setSelectedModel('xlm_roberta')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
                selectedModel === 'xlm_roberta'
                  ? 'bg-white text-[#26A69A] shadow-2xs'
                  : 'text-[#8E9DAE] hover:text-[#2D3E50]'
              }`}
            >
              XLM-RoBERTa
            </button>
          </div>
        </div>

        {/* Clear Chat */}
        <button
          onClick={handleClearHistory}
          disabled={messages.length === 0}
          className="p-2 rounded-xl text-[#B0BEC5] hover:text-[#EF5350] hover:bg-[#FFEBEE] transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          title="Xóa lịch sử chat"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>

      {/* Chat Messages Body */}
      <div className="flex-1 bg-white border border-[#EAEFEA] rounded-3xl p-6 overflow-y-auto space-y-6 shadow-xs">
        {notebooks.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto p-4">
            <div className="w-16 h-16 rounded-full bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center mb-3">
              <BookOpen className="w-8 h-8" />
            </div>
            <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">Chưa có vở bài tập nào</h3>
            <p className="text-xs text-[#8E9DAE] mt-1 mb-5">
              Bạn cần tạo ít nhất một vở bài tập và tải lên tài liệu để bắt đầu trò chuyện với trợ lý AI.
            </p>
            <button
              onClick={openCreateModal}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#26A69A] text-white text-xs font-bold shadow-md hover:bg-[#1E877B] transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Tạo vở bài tập ngay</span>
            </button>
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto p-4">
            <div className="relative w-24 h-24 mb-4">
              <Image
                src="/assets/mascot/mascot-owl-reading-book.png"
                alt="DocuMind Assistant"
                fill
                className="object-contain"
              />
            </div>
            <h3 className="font-outfit font-bold text-xl text-[#2D3E50]">
              Hỏi đáp ngữ cảnh với <span className="text-[#26A69A]">{selectedNotebook?.title || 'DocuMind'}</span>
            </h3>
            <p className="text-xs text-[#8E9DAE] mt-2 mb-6">
              Hệ thống RAG kết hợp mô hình PhoBERT sẽ tìm kiếm các đoạn trích liên quan nhất trong tài liệu của bạn để đưa ra câu trả lời chính xác kèm số trang.
            </p>

            {/* Quick Prompts */}
            <div className="w-full space-y-2">
              <div className="text-xs font-bold text-[#8E9DAE] uppercase tracking-wider mb-2 flex items-center justify-center gap-1">
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Gợi ý câu hỏi bắt đầu</span>
              </div>
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="w-full p-3 rounded-2xl bg-[#F7FAF7] hover:bg-[#E6F7F1]/60 border border-[#EAEFEA] text-left text-xs font-medium text-[#2D3E50] hover:text-[#26A69A] transition-all cursor-pointer flex items-center justify-between group"
                >
                  <span>{q}</span>
                  <Sparkles className="w-3.5 h-3.5 text-[#26A69A] opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.sender === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="relative w-8 h-8 rounded-full overflow-hidden bg-[#E6F7F1] border border-[#26A69A]/30 shrink-0 mt-1">
                    <Image
                      src="/assets/mascot/mascot-owl-avatar-circle.png"
                      alt="AI"
                      fill
                      className="object-cover"
                    />
                  </div>
                )}

                <div className={`max-w-2xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`rounded-3xl p-4 text-sm leading-relaxed ${
                      isUser
                        ? 'bg-[#26A69A] text-white rounded-br-xs shadow-xs'
                        : 'bg-[#F7FAF7] border border-[#EAEFEA] text-[#2D3E50] rounded-bl-xs'
                    }`}
                  >
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>

                  {/* Citations / Source Chunks */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-1 space-y-1.5">
                      <div className="text-[11px] font-bold text-[#8E9DAE] flex items-center gap-1">
                        <Info className="w-3 h-3 text-[#26A69A]" />
                        <span>Trích dẫn từ tài liệu:</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {msg.citations.map((cite, cIdx) => (
                          <span
                            key={cIdx}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#E6F7F1] border border-[#D2EFE6] text-[#26A69A] text-[11px] font-semibold"
                          >
                            <span>Trang {cite.page || '1'}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Message Footer */}
                  <div className={`flex items-center gap-2 text-[10px] text-[#8E9DAE] px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <span>{msg.timestamp}</span>
                    {!isUser && (
                      <button
                        onClick={() => handleCopy(msg.id, msg.text)}
                        className="hover:text-[#26A69A] transition-colors cursor-pointer"
                        title="Sao chép câu trả lời"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3 h-3 text-[#26A69A]" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}

        {loading && (
          <div className="flex gap-3.5 justify-start animate-in fade-in">
            <div className="relative w-8 h-8 rounded-full overflow-hidden bg-[#E6F7F1] border border-[#26A69A]/30 shrink-0">
              <Image
                src="/assets/mascot/mascot-owl-avatar-circle.png"
                alt="AI"
                fill
                className="object-cover"
              />
            </div>
            <div className="p-4 rounded-3xl rounded-bl-xs bg-[#F7FAF7] border border-[#EAEFEA] flex items-center gap-2 text-xs text-[#26A69A] font-semibold">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>PhoBERT đang phân tích tài liệu và suy luận...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="mt-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center bg-white border border-[#EAEFEA] focus-within:border-[#26A69A] rounded-2xl p-2 shadow-xs transition-all"
        >
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={notebooks.length === 0 || loading}
            placeholder={
              notebooks.length === 0
                ? 'Hãy tạo sổ tay trước để trò chuyện với AI...'
                : 'Nhập câu hỏi của bạn về nội dung các tài liệu...'
            }
            className="w-full bg-transparent border-none outline-hidden px-4 text-sm text-[#2D3E50] placeholder-[#8E9DAE] disabled:opacity-50"
          />

          <button
            type="submit"
            disabled={!inputText.trim() || loading || notebooks.length === 0}
            className="w-10 h-10 rounded-xl bg-[#26A69A] hover:bg-[#1E877B] text-white flex items-center justify-center shrink-0 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AIChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-[#8E9DAE]">Đang tải giao diện AI Chat...</div>}>
      <AIChatContent />
    </Suspense>
  );
}
