import React from 'react';
import { render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import QuickActions from '@/components/home/QuickActions';
import RecentNotesList from '@/components/home/RecentNotesList';
import type { DocumentItem } from '@/types';

vi.mock('next/image', () => ({ default: ({ alt }: { alt: string }) => <span>{alt}</span> }));

test('AI tắt vẫn cho mở thẻ học, khóa thao tác tạo hỏi đáp và tóm tắt', () => {
  render(<QuickActions aiEnabled={false} />);
  expect(screen.getByRole('button', { name: /Tóm tắt tài liệu/ })).toBeDisabled();
  expect(screen.getByRole('button', { name: /Chat với AI/ })).toBeDisabled();
  expect(screen.getByRole('link', { name: /Flashcards/ })).toHaveAttribute('href', '/flashcards');
  expect(screen.queryByRole('link', { name: /Chat với AI/ })).not.toBeInTheDocument();
});

test('file chỉ lưu được ghi là đã lưu, không giả hiển thị đang phân tích', () => {
  const document: DocumentItem = { document_id: 'document', notebook_id: 'notebook', file_name: 'Nguồn.txt', uploaded_at: '2026-11-10T10:00:00Z', status: 'uploaded' };
  render(<RecentNotesList documents={[document]} aiEnabled={false} />);
  expect(screen.getByText('Đã lưu')).toBeInTheDocument();
  expect(screen.queryByText('Đang phân tích')).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Đọc tài liệu' })).toHaveAttribute('href', '/notebooks/notebook');
  expect(screen.queryByTitle('Hỏi đáp AI trên tài liệu này')).not.toBeInTheDocument();
});
