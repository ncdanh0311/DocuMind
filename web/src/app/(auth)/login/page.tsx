'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { Mail, Lock, Eye, EyeOff, ArrowRight, Loader2, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Vui lòng điền đầy đủ email và mật khẩu.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(email.trim(), password);
    } catch (err: any) {
      console.error('Login error:', err);
      const msg = err.response?.data?.detail || 'Đăng nhập không thành công. Vui lòng kiểm tra lại email và mật khẩu.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7FAF7] flex items-center justify-center p-4 lg:p-8">
      <div className="w-full max-w-5xl bg-white border border-[#EAEFEA] rounded-3xl shadow-xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[640px]">
        {/* Left Section: Visual Mascot matching Mobile */}
        <div className="lg:col-span-6 bg-linear-to-br from-[#E6F7F1] via-[#F2FAF7] to-[#EAF5FC] p-8 lg:p-12 flex flex-col justify-between relative overflow-hidden">
          {/* Decorative Clouds & Botanical Leaves */}
          <div className="absolute -left-12 -top-12 w-48 h-48 opacity-30 pointer-events-none">
            <Image
              src="/assets/decor/clouds/decor-cloud-mint-01.png"
              alt="Cloud Decor"
              fill
              className="object-contain"
            />
          </div>
          <div className="absolute -right-8 bottom-4 w-40 h-40 opacity-30 pointer-events-none rotate-45">
            <Image
              src="/assets/decor/botanical/decor-leaf-sprig-03.png"
              alt="Leaf Decor"
              fill
              className="object-contain"
            />
          </div>

          {/* Top Brand */}
          <div className="relative z-10 flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-white p-1 shadow-xs border border-[#D2EFE6]">
              <Image
                src="/assets/mascot/mascot-owl-avatar-circle.png"
                alt="DocuMind"
                width={40}
                height={40}
                className="object-contain"
              />
            </div>
            <div>
              <h1 className="font-outfit font-extrabold text-xl text-[#2D3E50]">
                Docu<span className="text-[#26A69A]">Mind</span>
              </h1>
              <p className="text-xs text-[#8E9DAE] font-medium">Trợ lý học tập & nghiên cứu AI</p>
            </div>
          </div>

          {/* Center Mascot Image */}
          <div className="relative z-10 my-8 flex flex-col items-center justify-center">
            <div className="relative w-64 h-64 drop-shadow-md">
              <Image
                src="/assets/mascot/mascot-owl-reading-book.png"
                alt="DocuMind Owl Mascot"
                fill
                className="object-contain"
                priority
              />
            </div>
            <div className="mt-4 text-center max-w-xs">
              <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">
                Học tập thông minh hơn mỗi ngày
              </h3>
              <p className="text-xs text-[#8E9DAE] mt-1">
                Tóm tắt và hỏi đáp tài liệu tiếng Việt với các mô hình Deep Learning tiên tiến
              </p>
            </div>
          </div>

          {/* Bottom badge */}
          <div className="relative z-10 text-xs text-[#8E9DAE] text-center font-medium">
            IBM Docling • ViT5 • BARTpho • PhoBERT
          </div>
        </div>

        {/* Right Section: Login Form */}
        <div className="lg:col-span-6 p-8 lg:p-14 flex flex-col justify-center">
          <div className="max-w-md w-full mx-auto">
            <div className="mb-8">
              <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
                Đăng nhập
              </h2>
              <p className="text-sm text-[#8E9DAE] font-medium mt-1.5">
                Chào mừng bạn trở lại! Hãy nhập thông tin để tiếp tục.
              </p>
            </div>

            {error && (
              <div className="mb-6 p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
                  Email
                </label>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-13 transition-all">
                  <Mail className="w-5 h-5 text-[#8E9DAE] shrink-0" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-[#2D3E50] uppercase tracking-wider">
                    Mật khẩu
                  </label>
                  <a href="#" onClick={(e) => { e.preventDefault(); alert('Chức năng quên mật khẩu: Vui lòng kiểm tra email xác thực OTP'); }} className="text-xs font-bold text-[#26A69A] hover:underline">
                    Quên mật khẩu?
                  </a>
                </div>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-13 transition-all">
                  <Lock className="w-5 h-5 text-[#8E9DAE] shrink-0" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Nhập mật khẩu của bạn"
                    className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1 text-[#8E9DAE] hover:text-[#2D3E50] cursor-pointer transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#26A69A] hover:bg-[#1E877B] active:scale-[0.99] text-white font-bold h-13 rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed mt-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Đang đăng nhập...</span>
                  </>
                ) : (
                  <>
                    <span>Đăng nhập</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-8 text-center text-sm text-[#8E9DAE] font-medium">
              Chưa có tài khoản?{' '}
              <Link href="/register" className="font-bold text-[#26A69A] hover:underline">
                Đăng ký ngay
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
