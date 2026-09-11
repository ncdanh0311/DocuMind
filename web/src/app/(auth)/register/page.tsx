'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, Loader2, AlertCircle } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim() || !password) {
      setError('Vui lòng điền đầy đủ các thông tin.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Mật khẩu xác nhận không trùng khớp.');
      return;
    }

    if (password.length < 6) {
      setError('Mật khẩu phải chứa ít nhất 6 ký tự.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await register(email.trim(), password, fullName.trim());
    } catch (err: any) {
      console.error('Register error:', err);
      const msg = err.response?.data?.detail || 'Đăng ký không thành công. Email này có thể đã được sử dụng.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7FAF7] flex items-center justify-center p-4 lg:p-8">
      <div className="w-full max-w-5xl bg-white border border-[#EAEFEA] rounded-3xl shadow-xl overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[680px]">
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
          <div className="relative z-10 my-6 flex flex-col items-center justify-center">
            <div className="relative w-60 h-60 drop-shadow-md">
              <Image
                src="/assets/mascot/mascot-owl-waving-backpack.png"
                alt="DocuMind Owl Waving"
                fill
                className="object-contain"
                priority
              />
            </div>
            <div className="mt-4 text-center max-w-xs">
              <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">
                Bắt đầu hành trình cùng DocuMind
              </h3>
              <p className="text-xs text-[#8E9DAE] mt-1">
                Tạo tài khoản miễn phí để quản lý tài liệu và trò chuyện với trợ lý học tập AI
              </p>
            </div>
          </div>

          {/* Bottom badge */}
          <div className="relative z-10 text-xs text-[#8E9DAE] text-center font-medium">
            Bảo mật • Nhanh chóng • Đột phá
          </div>
        </div>

        {/* Right Section: Register Form */}
        <div className="lg:col-span-6 p-8 lg:p-14 flex flex-col justify-center">
          <div className="max-w-md w-full mx-auto">
            <div className="mb-6">
              <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
                Đăng ký tài khoản
              </h2>
              <p className="text-sm text-[#8E9DAE] font-medium mt-1.5">
                Nhập thông tin của bạn để tạo tài khoản mới.
              </p>
            </div>

            {error && (
              <div className="mb-5 p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name */}
              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                  Họ và tên
                </label>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-12 transition-all">
                  <User className="w-4.5 h-4.5 text-[#8E9DAE] shrink-0" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Nguyễn Văn A"
                    className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                  Email
                </label>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-12 transition-all">
                  <Mail className="w-4.5 h-4.5 text-[#8E9DAE] shrink-0" />
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
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                  Mật khẩu
                </label>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-12 transition-all">
                  <Lock className="w-4.5 h-4.5 text-[#8E9DAE] shrink-0" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Tối thiểu 6 ký tự"
                    className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="p-1 text-[#8E9DAE] hover:text-[#2D3E50] cursor-pointer transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                  Xác nhận mật khẩu
                </label>
                <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-12 transition-all">
                  <Lock className="w-4.5 h-4.5 text-[#8E9DAE] shrink-0" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Nhập lại mật khẩu"
                    className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-[#26A69A] hover:bg-[#1E877B] active:scale-[0.99] text-white font-bold h-12 rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed pt-1"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Đang đăng ký...</span>
                  </>
                ) : (
                  <>
                    <span>Tạo tài khoản</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 text-center text-sm text-[#8E9DAE] font-medium">
              Đã có tài khoản?{' '}
              <Link href="/login" className="font-bold text-[#26A69A] hover:underline">
                Đăng nhập
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
