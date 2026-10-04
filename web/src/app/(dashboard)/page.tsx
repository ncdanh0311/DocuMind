'use client';

import React, { useEffect, useState } from 'react';
import HomeBanner from '@/components/home/HomeBanner';
import QuickActions from '@/components/home/QuickActions';
import NotebookGrid from '@/components/home/NotebookGrid';
import RecentNotesList from '@/components/home/RecentNotesList';
import { apiService } from '@/lib/api';
import { DocumentItem } from '@/types';
import { useNotebooks } from '@/contexts/NotebookContext';

export default function DashboardHomePage() {
  const { notebooks } = useNotebooks();
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>([]);

  useEffect(() => {
    async function loadRecentDocs() {
      try {
        const docsData = await apiService.getRecentDocuments();
        setRecentDocs(docsData);
      } catch (err) {
        console.error('Error loading recent documents:', err);
      }
    }
    loadRecentDocs();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-12">
      {/* Hero Welcome Banner */}
      <HomeBanner />

      {/* 4 Quick Action 3D Cards */}
      <QuickActions />

      {/* Notebooks Grid */}
      <NotebookGrid notebooks={notebooks} />

      {/* Recent Notes List */}
      <RecentNotesList documents={recentDocs} />
    </div>
  );
}
