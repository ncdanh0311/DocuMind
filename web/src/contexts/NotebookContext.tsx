'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { Notebook } from '@/types';
import { apiService } from '@/lib/api';
import { useAuth } from './AuthContext';

interface NotebookContextType {
  notebooks: Notebook[];
  loading: boolean;
  isLoading: boolean;
  refreshNotebooks: () => Promise<void>;
  isCreateOpen: boolean;
  openCreateModal: () => void;
  closeCreateModal: () => void;
}

const NotebookContext = createContext<NotebookContextType | undefined>(undefined);

export function NotebookProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [loading, setLoading] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const refreshNotebooks = useCallback(async () => {
    if (!isAuthenticated) {
      setNotebooks([]);
      return;
    }
    setLoading(true);
    try {
      const data = await apiService.getNotebooks();
      setNotebooks(data);
    } catch (err) {
      console.error('Failed to load notebooks:', err);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refreshNotebooks();
    } else {
      setNotebooks([]);
    }
  }, [isAuthenticated, refreshNotebooks]);

  const openCreateModal = () => setIsCreateOpen(true);
  const closeCreateModal = () => setIsCreateOpen(false);

  return (
    <NotebookContext.Provider
      value={{
        notebooks,
        loading,
        isLoading: loading,
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
