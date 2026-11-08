'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { Notebook } from '@/types';
import { apiService, getErrorMessage } from '@/lib/api';
import { useAuth } from './AuthContext';

interface NotebookContextType {
  notebooks: Notebook[];
  loading: boolean;
  isLoading: boolean;
  error: string | null;
  refreshNotebooks: () => Promise<void>;
  isCreateOpen: boolean;
  openCreateModal: () => void;
  closeCreateModal: () => void;
}

const NotebookContext = createContext<NotebookContextType | undefined>(undefined);

export function NotebookProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const invalidate = useCallback(() => { generation.current++; }, []);

  const refreshNotebooks = useCallback(async () => {
    const request = ++generation.current;
    if (!isAuthenticated) {
      setNotebooks([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getNotebooks();
      if (request === generation.current) setNotebooks(data);
    } catch (err) {
      if (request === generation.current) setError(getErrorMessage(err));
    } finally {
      if (request === generation.current) setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    setNotebooks([]); setIsCreateOpen(false);
    if (isAuthenticated) {
      refreshNotebooks();
    } else {
      setNotebooks([]);
      setLoading(false); setError(null);
    }
    return invalidate;
  }, [isAuthenticated, user?.user_id, refreshNotebooks, invalidate]);

  const openCreateModal = () => setIsCreateOpen(true);
  const closeCreateModal = () => setIsCreateOpen(false);

  return (
    <NotebookContext.Provider
      value={{
        notebooks,
        loading,
        isLoading: loading,
        error,
        refreshNotebooks,
        isCreateOpen,
        openCreateModal,
        closeCreateModal,
      }}
    >
      {children}
    </NotebookContext.Provider>
  );
}

export function useNotebooks() {
  const context = useContext(NotebookContext);
  if (!context) {
    throw new Error('useNotebooks must be used within a NotebookProvider');
  }
  return context;
}
