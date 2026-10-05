'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { apiService, getErrorMessage } from '@/lib/api';
import { Mail, ArrowLeft, ArrowRight, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      setError('Vui lòng nhập địa chỉ email của bạn.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await apiService.forgotPassword(email.trim());
      setSuccess(true);
      setTimeout(() => {
        router.push(`/reset-password?email=${encodeURIComponent(email.trim())}`);
      }, 1500);
    } catch (err: unknown) {
      console.error('Forgot password error:', err);
      setError(getErrorMessage(err, 'Không thể gửi mã xác thực. Vui lòng kiểm tra lại email.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7FAF7] flex items-center justify-center p-4 lg:p-8">
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
            <p className="text-xs text-[#8E9DAE] font-medium">Khôi phục mật khẩu tài khoản</p>
          </div>
        </div>

        <div className="mb-6">
          <h2 className="font-outfit text-2xl font-extrabold text-[#2D3E50]">
            Quên mật khẩu?
          </h2>
          <p className="text-sm text-[#8E9DAE] font-medium mt-1.5">
            Nhập địa chỉ email đăng ký của bạn. Chúng tôi sẽ gửi mã OTP gồm 6 chữ số để bạn đặt lại mật khẩu.
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
            <span>Mã OTP đã được gửi đến email! Đang chuyển tới trang xác nhận...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-2">
              Email đăng ký
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

          <button
            type="submit"
            disabled={loading || success}
            className="w-full bg-[#26A69A] hover:bg-[#1E877B] active:scale-[0.99] text-white font-bold h-13 rounded-2xl shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 text-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Đang gửi mã...</span>
              </>
            ) : (
              <>
                <span>Nhận mã OTP</span>
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
    </div>
  );
}
