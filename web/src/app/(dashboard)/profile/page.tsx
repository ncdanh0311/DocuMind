'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/lib/api';
import { 
  User, 
  Mail, 
  Lock, 
  LogOut, 
  Check, 
  AlertCircle, 
  Loader2, 
  ShieldCheck, 
  Sparkles
} from 'lucide-react';

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [securityLoading, setSecurityLoading] = useState(false);
  const [securitySuccess, setSecuritySuccess] = useState(false);
  const [securityError, setSecurityError] = useState<string | null>(null);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) return;

    setProfileLoading(true);
    setProfileSuccess(false);
    setProfileError(null);

    try {
      await apiService.updateProfile({ full_name: fullName.trim() });
      await refreshUser();
      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err: any) {
      setProfileError(err.response?.data?.detail || 'Không thể cập nhật hồ sơ');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleUpdateSecurity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oldPassword || !newPassword) return;

    if (newPassword !== confirmPassword) {
      setSecurityError('Mật khẩu xác nhận không khớp');
      return;
    }

    setSecurityLoading(true);
    setSecuritySuccess(false);
    setSecurityError(null);

    try {
      await apiService.updateSecurity({ old_password: oldPassword, new_password: newPassword });
      setSecuritySuccess(true);
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setSecuritySuccess(false), 3000);
    } catch (err: any) {
      setSecurityError(err.response?.data?.detail || 'Mật khẩu cũ không chính xác');
    } finally {
      setSecurityLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300 max-w-4xl mx-auto pb-12">
      {/* Header */}
      <div>
        <h2 className="font-outfit text-3xl font-extrabold text-[#2D3E50]">
          Hồ sơ cá nhân & Cài đặt
        </h2>
        <p className="text-xs text-[#8E9DAE] font-medium mt-1">
          Quản lý tài khoản, thông tin sinh viên và thiết lập bảo mật
        </p>
      </div>

      {/* User Hero Card */}
      <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 lg:p-8 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-4">
          <div className="relative w-18 h-18 rounded-2xl overflow-hidden bg-[#E6F7F1] border-2 border-[#26A69A]/30 p-1">
            <Image
              src="/assets/mascot/mascot-owl-avatar-circle.png"
              alt="Avatar"
              fill
              className="object-cover"
            />
          </div>
          <div>
            <h3 className="font-outfit text-xl font-bold text-[#2D3E50]">
              {user?.full_name || 'Người dùng DocuMind'}
            </h3>
            <p className="text-xs text-[#8E9DAE] font-medium mt-0.5">
              {user?.email || 'user@documind.vn'}
            </p>
            <div className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-0.5 rounded-md bg-[#E6F7F1] text-[#26A69A] text-[11px] font-bold">
              <Sparkles className="w-3 h-3" />
              <span>Thành viên nghiên cứu AI</span>
            </div>
          </div>
        </div>

        <button
          onClick={logout}
          className="px-4 py-2.5 rounded-2xl bg-[#FFEBEE] hover:bg-[#FFCDD2] text-[#C62828] text-xs font-bold transition-all flex items-center gap-2 cursor-pointer"
        >
          <LogOut className="w-4 h-4" />
          <span>Đăng xuất</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Update Profile Form */}
        <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 shadow-xs">
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-9 h-9 rounded-xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-outfit font-bold text-base text-[#2D3E50]">Thông tin cơ bản</h4>
              <p className="text-xs text-[#8E9DAE]">Cập nhật tên hiển thị của bạn</p>
            </div>
          </div>

          {profileSuccess && (
            <div className="mb-4 p-3 rounded-xl bg-[#E6F7F1] text-[#26A69A] text-xs font-bold flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>Cập nhật hồ sơ thành công!</span>
            </div>
          )}

          {profileError && (
            <div className="mb-4 p-3 rounded-xl bg-[#FFEBEE] text-[#C62828] text-xs font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{profileError}</span>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                Họ và tên
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Nhập họ và tên"
                className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-xs text-[#2D3E50] outline-hidden transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                Địa chỉ Email
              </label>
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="w-full bg-[#F5F7F7] border border-transparent rounded-2xl px-4 py-3 text-xs text-[#8E9DAE] outline-hidden cursor-not-allowed opacity-80"
              />
            </div>

            <button
              type="submit"
              disabled={profileLoading}
              className="w-full bg-[#26A69A] hover:bg-[#1E877B] text-white font-bold h-11 rounded-2xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 text-xs cursor-pointer disabled:opacity-60"
            >
              {profileLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Lưu thay đổi</span>}
            </button>
          </form>
        </div>

        {/* Change Password Form */}
        <div className="bg-white border border-[#EAEFEA] rounded-3xl p-6 shadow-xs">
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-9 h-9 rounded-xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h4 className="font-outfit font-bold text-base text-[#2D3E50]">Đổi mật khẩu</h4>
              <p className="text-xs text-[#8E9DAE]">Bảo vệ an toàn cho tài khoản</p>
            </div>
          </div>

          {securitySuccess && (
            <div className="mb-4 p-3 rounded-xl bg-[#E6F7F1] text-[#26A69A] text-xs font-bold flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>Đổi mật khẩu thành công!</span>
            </div>
          )}

          {securityError && (
            <div className="mb-4 p-3 rounded-xl bg-[#FFEBEE] text-[#C62828] text-xs font-medium flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{securityError}</span>
            </div>
          )}

          <form onSubmit={handleUpdateSecurity} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                Mật khẩu hiện tại
              </label>
              <input
                type="password"
                required
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="Nhập mật khẩu hiện tại"
                className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-xs text-[#2D3E50] outline-hidden transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                Mật khẩu mới
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Tối thiểu 6 ký tự"
                className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-xs text-[#2D3E50] outline-hidden transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-[#2D3E50] uppercase tracking-wider mb-1.5">
                Xác nhận mật khẩu mới
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Nhập lại mật khẩu mới"
                className="w-full bg-[#F5F7F7] focus:bg-white border border-transparent focus:border-[#26A69A] rounded-2xl px-4 py-3 text-xs text-[#2D3E50] outline-hidden transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={securityLoading}
              className="w-full bg-[#26A69A] hover:bg-[#1E877B] text-white font-bold h-11 rounded-2xl shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 text-xs cursor-pointer disabled:opacity-60"
            >
              {securityLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Đổi mật khẩu</span>}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
