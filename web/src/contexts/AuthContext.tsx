'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '@/types';
import { apiService, tokenManager } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function initAuth() {
      const savedToken = tokenManager.getAccessToken();

      if (savedToken) {
        setToken(savedToken);
        try {
          const profile = await apiService.getProfile();
          setUser(profile);
        } catch {
          // Token is expired or invalid -> clear
          tokenManager.clearAuth();
          setToken(null);
          setUser(null);
        }
      } else {
        setToken(null);
        setUser(null);
      }
      setIsLoading(false);
    }
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await apiService.login(email, password);
      setToken(res.access_token);
      // Fetch full user profile
      try {
        const profile = await apiService.getProfile();
        setUser(profile);
      } catch {
        setUser({
          user_id: res.user_id || 'user-logged',
          email,
          full_name: res.full_name || email.split('@')[0],
        });
      }
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    try {
      const res = await apiService.register(email, password, fullName);
      setToken(res.access_token);
      try {
        const profile = await apiService.getProfile();
        setUser(profile);
      } catch {
        setUser({
          user_id: res.user_id || 'user-new',
          email,
          full_name: fullName || res.full_name || email.split('@')[0],
        });
      }
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiService.logout();
    } catch {
      // Continue logout even if server fails
    }
    tokenManager.clearAuth();
    setToken(null);
    setUser(null);
    router.push('/login');
  };

  const refreshUser = async () => {
    try {
      const profile = await apiService.getProfile();
      setUser(profile);
    } catch {
      // Keep existing state
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
