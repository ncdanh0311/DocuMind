'use client';

import React, { useState, useEffect } from 'react';
import { apiService } from '@/lib/api';
import { NotificationItem } from '@/types';
import { Bell, X, CheckCheck, Loader2, Info, AlertTriangle, CheckCircle } from 'lucide-react';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNotificationsRead: () => void;
}

export default function NotificationDrawer({ isOpen, onClose, onNotificationsRead }: NotificationDrawerProps) {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [markingRead, setMarkingRead] = useState(false);

  const loadNotifications = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiService.getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen, loadNotifications]);

  const handleMarkAllRead = async () => {
    setMarkingRead(true);
    try {
      await apiService.markAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      onNotificationsRead();
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    } finally {
      setMarkingRead(false);
    }
  };

  if (!isOpen) return null;

  const formatTime = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit',
        day: '2-digit',
        month: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-xs animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-[#EAEFEA] animate-in slide-in-from-right duration-300">
        {/* Header */}
        <div className="px-6 py-5 border-b border-[#F5F8F5] flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-[#E6F7F1] text-[#26A69A] flex items-center justify-center">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-outfit font-bold text-lg text-[#2D3E50]">Thông báo</h3>
              <p className="text-xs text-[#8E9DAE]">Cập nhật về tiến trình xử lý và tài liệu</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-gray-100 text-[#8E9DAE] hover:text-[#2D3E50] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action bar */}
        <div className="px-6 py-3 bg-[#F7FAF7] border-b border-[#EAEFEA] flex items-center justify-between">
          <span className="text-xs font-semibold text-[#8E9DAE]">
            {notifications.filter((n) => !n.is_read).length} chưa đọc
          </span>
          <button
            onClick={handleMarkAllRead}
            disabled={markingRead || notifications.length === 0}
            className="text-xs font-bold text-[#26A69A] hover:text-[#1E877B] flex items-center gap-1 cursor-pointer disabled:opacity-50"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            <span>{markingRead ? 'Đang cập nhật...' : 'Đánh dấu đã đọc tất cả'}</span>
          </button>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-[#8E9DAE] gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-[#26A69A]" />
              <span className="text-xs font-medium">Đang tải thông báo...</span>
            </div>
          ) : notifications.length === 0 ? (
            <div className="py-16 text-center text-[#8E9DAE]">
              <div className="w-12 h-12 rounded-full bg-[#F5F8F5] flex items-center justify-center mx-auto mb-3 text-[#B0BEC5]">
                <Bell className="w-6 h-6" />
              </div>
              <p className="text-sm font-semibold text-[#2D3E50]">Không có thông báo mới</p>
              <p className="text-xs text-[#8E9DAE] mt-1">Bạn đã cập nhật hết tất cả các thông tin</p>
            </div>
          ) : (
            notifications.map((item) => (
              <div
                key={item.notification_id || item.id}
                className={`p-4 rounded-2xl border transition-all ${
                  item.is_read
                    ? 'bg-white border-[#EAEFEA] text-[#2D3E50]'
                    : 'bg-[#F2FAF7] border-[#D2EFE6] text-[#2D3E50] shadow-2xs'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">
                    {item.type === 'error' ? (
                      <AlertTriangle className="w-4 h-4 text-[#EF5350]" />
                    ) : item.type === 'success' ? (
                      <CheckCircle className="w-4 h-4 text-[#26A69A]" />
                    ) : (
                      <Info className="w-4 h-4 text-[#0088CC]" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <h4 className="text-xs font-bold truncate">{item.title}</h4>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-[#26A69A] shrink-0" />
                      )}
                    </div>
                    <p className="text-xs text-[#8E9DAE] mt-1 line-clamp-2">{item.message}</p>
                    <span className="text-[10px] text-[#B0BEC5] mt-2 block font-medium">
                      {formatTime(item.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
