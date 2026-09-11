'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Image from 'next/image';
import { apiService, MOCK_NOTEBOOKS } from '@/lib/api';
import { Notebook, ChatMessage } from '@/types';
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
  HelpCircle
} from 'lucide-react';

function AIChatContent() {
  const searchParams = useSearchParams();
  const initialNotebookId = searchParams.get('notebookId') || '';

  const [notebooks, setNotebooks] = useState<Notebook[]>(MOCK_NOTEBOOKS);
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>(initialNotebookId);
  const [selectedModel, setSelectedModel] = useState<string>('phobert_qa');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load available notebooks
  useEffect(() => {
    async function loadNotebooks() {
      try {
        const data = await apiService.getNotebooks();
        if (data && data.length > 0) {
          setNotebooks(data);
          if (!selectedNotebookId) {
            setSelectedNotebookId(data[0].notebook_id || data[0].id || '');
          }
        }
      } catch (err) {
        console.error('Failed to load notebooks for chat:', err);
      }
    }
    loadNotebooks();
  }, []);

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
    } catch (err: any) {
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const selectedNotebook = notebooks.find(
    (n) => n.notebook_id === selectedNotebookId || n.id === selectedNotebookId
  );

  const samplePrompts = [
    'Tóm tắt các nội dung cốt lõi của tài liệu này?',
    'Giải thích thuật ngữ quan trọng nhất một cách dễ hiểu?',
    'Đặt 3 câu hỏi trắc nghiệm kiểm tra kiến thức?',
  ];

  return (
    <div className="h-[calc(100vh-8.5rem)] flex flex-col bg-white border border-[#EAEFEA] rounded-3xl overflow-hidden shadow-xs animate-in fade-in duration-300">
      {/* Top Bar: Notebook & Model Selector */}
      <div className="px-6 py-4 border-b border-[#F5F8F5] flex flex-wrap items-center justify-between gap-4 bg-white sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center p-1 border border-[#D2EFE6]">
            <Image
              src="/assets/mascot/mascot-owl-avatar-circle.png"
              alt="AI"
              width={34}
              height={34}
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-outfit font-bold text-base text-[#2D3E50]">DocuMind AI Chat</h3>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#E6F7F1] text-[#26A69A] uppercase tracking-wider">
                RAG Studio
              </span>
            </div>
            <p className="text-xs text-[#8E9DAE]">Hỏi đáp trực tiếp theo ngữ cảnh tài liệu học tập</p>
          </div>
        </div>

        {/* Selectors */}
        <div className="flex items-center gap-3">
          {/* Notebook Dropdown */}
          <div className="relative">
            <select
              value={selectedNotebookId}
              onChange={(e) => {
                setSelectedNotebookId(e.target.value);
                setMessages([]);
              }}
              className="bg-[#F5F7F7] hover:bg-[#EAEFEA] text-xs font-bold text-[#2D3E50] py-2 pl-3 pr-8 rounded-xl appearance-none outline-hidden border border-transparent focus:border-[#26A69A] transition-all cursor-pointer"
            >
              {notebooks.map((nb) => {
                const id = nb.notebook_id || nb.id || '';
                return (
                  <option key={id} value={id}>
                    📖 {nb.title}
                  </option>
                );
              })}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#8E9DAE] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Model Dropdown */}
          <div className="relative">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-[#E6F7F1] text-xs font-bold text-[#26A69A] py-2 pl-3 pr-8 rounded-xl appearance-none outline-hidden border border-[#D2EFE6] transition-all cursor-pointer"
            >
              <option value="phobert_qa">PhoBERT QA (Tiếng Việt)</option>
              <option value="rag">Semantic RAG Search</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[#26A69A] absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Clear Messages */}
          {messages.length > 0 && (
            <button
              onClick={() => setMessages([])}
              className="p-2 rounded-xl text-gray-400 hover:text-[#E53935] hover:bg-[#FFEBEE] transition-colors cursor-pointer"
              title="Xóa đoạn hội thoại"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 p-6 overflow-y-auto space-y-5 bg-[#F7FAF7]/60">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 max-w-lg mx-auto">
            <div className="relative w-36 h-36 mb-4 drop-shadow-sm">
              <Image
                src="/assets/mascot/mascot-owl-reading-book.png"
                alt="DocuMind Mascot"
                fill
                className="object-contain"
              />
            </div>
            <h4 className="font-outfit font-bold text-xl text-[#2D3E50]">
              Bạn cần giải đáp gì trong <span className="text-[#26A69A]">{selectedNotebook?.title || 'sổ tay này'}</span>?
            </h4>
            <p className="text-xs text-[#8E9DAE] mt-1.5 mb-6 leading-relaxed">
              DocuMind AI sẽ quét nội dung từ các tài liệu bạn đã tải lên, phân tích và trích xuất câu trả lời chính xác nhất.
            </p>

            {/* Prompt suggestions */}
            <div className="w-full space-y-2 text-left">
              {samplePrompts.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="w-full bg-white hover:bg-[#E6F7F1]/50 border border-[#EAEFEA] hover:border-[#26A69A]/40 rounded-2xl p-3 text-xs font-semibold text-[#2D3E50] hover:text-[#26A69A] transition-all flex items-center justify-between group cursor-pointer shadow-2xs"
                >
                  <span>{prompt}</span>
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
                className={`flex items-start gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-9 h-9 rounded-2xl bg-[#E6F7F1] p-1 shrink-0 border border-[#D2EFE6]">
                    <Image
                      src="/assets/mascot/mascot-owl-avatar-circle.png"
                      alt="AI"
                      width={32}
                      height={32}
                    />
                  </div>
                )}

                <div className={`max-w-2xl flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                  <div
                    className={`rounded-3xl p-4.5 text-sm leading-relaxed ${
                      isUser
                        ? 'bg-[#26A69A] text-white rounded-br-xs shadow-xs font-medium'
                        : 'bg-white text-[#2D3E50] border border-[#EAEFEA] rounded-bl-xs shadow-2xs'
                    }`}
                  >
                    {isUser ? (
                      <div>{msg.text}</div>
                    ) : (
                      <div className="prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 text-[#2D3E50]">
                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                      </div>
                    )}

                    {/* Citations block */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100 space-y-1.5">
                        <div className="text-[11px] font-bold text-[#26A69A] flex items-center gap-1">
                          <BookOpen className="w-3 h-3" />
                          <span>Nguồn trích dẫn:</span>
                        </div>
                        {msg.citations.map((cite, cIdx) => (
                          <div
                            key={cIdx}
                            className="bg-[#F7FAF7] border border-[#EAEFEA] rounded-xl p-2.5 text-xs text-[#2D3E50] font-normal"
                          >
                            <p className="italic line-clamp-2">"{cite.content}"</p>
                            {cite.page_number && (
                              <span className="text-[10px] font-bold text-[#8E9DAE] mt-1 block">
                                Trang {cite.page_number}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Message Meta & Action */}
                  <div className="flex items-center gap-2 mt-1 px-1 text-[10px] text-[#8E9DAE]">
                    <span>{msg.timestamp}</span>
                    {!isUser && (
                      <button
                        onClick={() => handleCopy(msg.text, msg.id)}
                        className="hover:text-[#26A69A] flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check className="w-3 h-3 text-[#26A69A]" />
                            <span className="text-[#26A69A]">Đã chép</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3 h-3" />
                            <span>Sao chép</span>
                          </>
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
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-2xl bg-[#E6F7F1] p-1 shrink-0 border border-[#D2EFE6]">
              <Image
                src="/assets/mascot/mascot-owl-avatar-circle.png"
                alt="AI"
                width={32}
                height={32}
              />
            </div>
            <div className="bg-white border border-[#EAEFEA] rounded-3xl rounded-bl-xs p-4 shadow-2xs flex items-center gap-2.5 text-xs text-[#8E9DAE]">
              <Loader2 className="w-4 h-4 animate-spin text-[#26A69A]" />
              <span>DocuMind đang đọc tài liệu và phân tích câu trả lời...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <div className="p-4 bg-white border-t border-[#F5F8F5]">
        <div className="max-w-4xl mx-auto flex items-center gap-2 bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 py-2 transition-all">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Hỏi bất kỳ điều gì về tài liệu của bạn (Enter để gửi)..."
            rows={1}
            className="flex-1 bg-transparent border-none outline-hidden text-sm text-[#2D3E50] placeholder-[#8E9DAE] resize-none py-1.5 max-h-32"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputText.trim() || loading}
            className="w-10 h-10 rounded-xl bg-[#26A69A] hover:bg-[#1E877B] text-white flex items-center justify-center shrink-0 transition-all cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AIChatPage() {
  return (
    <Suspense fallback={
      <div className="h-[calc(100vh-8.5rem)] flex items-center justify-center bg-white rounded-3xl border border-[#EAEFEA]">
        <Loader2 className="w-8 h-8 animate-spin text-[#26A69A]" />
      </div>
    }>
      <AIChatContent />
    </Suspense>
  );
}
