'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter, useSearchParams } from 'next/navigation';
import { apiService, getErrorMessage } from '@/lib/api';
import { KeyRound, Lock, Eye, EyeOff, ArrowLeft, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialEmail = searchParams.get('email') || '';

  const [email, setEmail] = useState(initialEmail);
  const [otpCode, setOtpCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !otpCode.trim() || !newPassword) {
      setError('Vui lòng điền đầy đủ email, mã OTP và mật khẩu mới.');
      return;
    }

    if (newPassword.length < 6) {
      setError('Mật khẩu mới phải có ít nhất 6 ký tự.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // 1. Verify OTP to get reset token
      const verifyRes = await apiService.verifyOtp(email.trim(), otpCode.trim());
      const resetToken = verifyRes.token || verifyRes.access_token || otpCode.trim();

      // 2. Reset Password with token
      await apiService.resetPassword(resetToken, newPassword);
      setSuccess(true);
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } catch (err: unknown) {
      console.error('Reset password error:', err);
      setError(getErrorMessage(err, 'Mã OTP không hợp lệ hoặc đã hết hạn.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-xl bg-white border border-[#EAEFEA] rounded-3xl shadow-xl p-8 lg:p-12">
      {/* Brand */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-2xl bg-[#E6F7F1] p-1 border border-[#D2EFE6] flex items-center justify-center">
          <Image
            src="/assets/mascot/mascot-owl-avatar-circle.png"
            alt="DocuMind"
            width={36}
            height={36}
            className="object-contain"
          />
        </div>
        <div>
          <h1 className="font-outfit font-extrabold text-lg text-[#2D3E50]">
            Docu<span className="text-[#26A69A]">Mind</span>
          </h1>
          <p className="text-xs text-[#8E9DAE] font-medium">Đặt lại mật khẩu</p>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="font-outfit text-2xl font-extrabold text-[#2D3E50]">
          Xác thực mã OTP & Mật khẩu mới
        </h2>
        <p className="text-sm text-[#8E9DAE] font-medium mt-1.5">
          Nhập mã OTP gồm 6 chữ số đã gửi tới email cùng mật khẩu mới của bạn.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-2xl bg-[#FFEBEE] border border-[#FFCDD2] text-[#C62828] text-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 rounded-2xl bg-[#E6F7F1] border border-[#A7E2D4] text-[#1E877B] text-sm flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
          <span>Đặt lại mật khẩu thành công! Đang chuyển hướng về trang chủ...</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="name@example.com"
            className="w-full bg-[#F5F7F7] border border-transparent focus:border-[#26A69A] focus:bg-white rounded-2xl px-4 h-13 text-sm text-[#2D3E50] placeholder-[#8E9DAE] outline-hidden transition-all"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Mã OTP (6 chữ số)
          </label>
          <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-13 transition-all">
            <KeyRound className="w-5 h-5 text-[#8E9DAE] shrink-0" />
            <input
              type="text"
              required
              maxLength={6}
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.trim())}
              placeholder="VD: 123456"
              className="w-full bg-transparent border-none outline-hidden px-3 text-sm font-bold tracking-widest text-[#2D3E50] placeholder-[#8E9DAE]"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Mật khẩu mới
          </label>
          <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-13 transition-all">
            <Lock className="w-5 h-5 text-[#8E9DAE] shrink-0" />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Tối thiểu 6 ký tự"
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

        <div>
          <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
            Xác nhận mật khẩu mới
          </label>
          <div className="relative flex items-center bg-[#F5F7F7] border border-transparent focus-within:border-[#26A69A] focus-within:bg-white rounded-2xl px-4 h-13 transition-all">
            <Lock className="w-5 h-5 text-[#8E9DAE] shrink-0" />
            <input
              type={showPassword ? 'text' : 'password'}
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Nhập lại mật khẩu mới"
              className="w-full bg-transparent border-none outline-hidden px-3 text-sm text-[#2D3E50] placeholder-[#8E9DAE]"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || success}
          className="w-full bg-[#26A69A] hover:bg-[#1E877B] active:scale-[0.99] text-white font-bold h-13 rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed mt-4"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Đang xác thực...</span>
            </>
          ) : (
            <>
              <span>Hoàn tất & Đăng nhập</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="mt-8 text-center">
        <Link
          href="/login"
          className="inline-flex items-center gap-2 text-sm font-bold text-[#8E9DAE] hover:text-[#26A69A] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Quay lại trang Đăng nhập</span>
        </Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen bg-[#F7FAF7] flex items-center justify-center p-4 lg:p-8">
      <Suspense fallback={<div className="p-8 text-center text-[#8E9DAE]">Đang tải...</div>}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
