'use client';

import React, { useEffect } from 'react';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { useAuth } from '@/contexts/AuthContext';
import { NotebookProvider, useNotebooks } from '@/contexts/NotebookContext';
import CreateNotebookModal from '@/components/notebooks/CreateNotebookModal';
import { Loader2 } from 'lucide-react';

function DashboardContent({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const { isCreateOpen, closeCreateModal, refreshNotebooks } = useNotebooks();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F7FAF7] flex flex-col items-center justify-center p-4">
        <div className="relative w-20 h-20 mb-4 animate-bounce">
          <Image
            src="/assets/mascot/mascot-owl-avatar-circle.png"
            alt="DocuMind Loading"
            fill
            className="object-contain"
          />
        </div>
        <div className="flex items-center gap-2 text-[#26A69A] font-bold text-sm">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Đang tải không gian học tập...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="flex min-h-screen bg-[#F7FAF7]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Workspace Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Global Create Notebook Modal */}
      <CreateNotebookModal
        isOpen={isCreateOpen}
        onClose={closeCreateModal}
        onCreated={refreshNotebooks}
      />
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <NotebookProvider>
      <DashboardContent>{children}</DashboardContent>
    </NotebookProvider>
  );
}
