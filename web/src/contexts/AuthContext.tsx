'use client';

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import type { User } from '@/types';
import { apiService, tokenManager } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  resetPassword: (resetToken: string, newPassword: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}
const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const operation = useRef(0);
  const router = useRouter();
  const invalidateOperation = useCallback(() => { operation.current++; }, []);

  useEffect(() => {
    const syncCredentials = () => {
      const current = tokenManager.getAccessToken();
      setToken(current);
      if (!current) { operation.current++; setUser(null); setIsLoading(false); }
    };
    window.addEventListener('auth-changed', syncCredentials);
    window.addEventListener('storage', syncCredentials);
    const currentOperation = ++operation.current;
    async function init() {
      if (tokenManager.getAccessToken()) {
        try {
          const profile = await apiService.getProfile();
          if (operation.current === currentOperation) {
            setUser(profile);
            setToken(tokenManager.getAccessToken());
          }
        } catch { /* Keep stored credentials during temporary connection failures. */ }
      }
      if (operation.current === currentOperation) setIsLoading(false);
    }
    init();
    return () => { invalidateOperation(); window.removeEventListener('auth-changed', syncCredentials); window.removeEventListener('storage', syncCredentials); };
  }, [invalidateOperation]);

  const establishSession = async (action: () => Promise<unknown>) => {
    const currentOperation = ++operation.current;
    setIsLoading(true);
    setUser(null);
    try {
      await action();
      const profile = await apiService.getProfile();
      if (operation.current === currentOperation) {
        setUser(profile);
        setToken(tokenManager.getAccessToken());
        router.replace('/');
      }
    } finally { if (operation.current === currentOperation) setIsLoading(false); }
  };
  const login = (email: string, password: string) => establishSession(() => apiService.login(email, password));
  const register = (email: string, password: string, fullName?: string) => establishSession(() => apiService.register(email, password, fullName));
  const resetPassword = (resetToken: string, newPassword: string) => establishSession(() => apiService.resetPassword(resetToken, newPassword));
  const logout = async () => {
    operation.current++;
    await apiService.logout();
    setToken(null);
    setUser(null);
    setIsLoading(false);
    router.replace('/login');
  };
  const refreshUser = async () => {
    const profile = await apiService.getProfile();
    setUser(profile);
    setToken(tokenManager.getAccessToken());
  };
  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token && !!user, isLoading, login, register, resetPassword, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
}
