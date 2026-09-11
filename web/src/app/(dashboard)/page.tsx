'use client';

import React, { useEffect, useState } from 'react';
import HomeBanner from '@/components/home/HomeBanner';
import QuickActions from '@/components/home/QuickActions';
import NotebookGrid from '@/components/home/NotebookGrid';
import RecentNotesList from '@/components/home/RecentNotesList';
import { apiService, MOCK_NOTEBOOKS, MOCK_RECENT_DOCUMENTS } from '@/lib/api';
import { Notebook, DocumentItem } from '@/types';

export default function DashboardHomePage() {
  const [notebooks, setNotebooks] = useState<Notebook[]>(MOCK_NOTEBOOKS);
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>(MOCK_RECENT_DOCUMENTS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [nbData, docsData] = await Promise.all([
          apiService.getNotebooks(),
          apiService.getRecentDocuments(),
        ]);
        if (nbData && nbData.length > 0) setNotebooks(nbData);
        if (docsData && docsData.length > 0) setRecentDocs(docsData);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
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
