import React from 'react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import CreateNotebookModal from '../src/components/notebooks/CreateNotebookModal';
import NotebookPage from '../src/app/(dashboard)/notebooks/[id]/page';
import { apiService } from '../src/lib/api';
import { selectDocuments, selectNotebooks } from '../src/lib/management';
import type { Notebook, DocumentItem } from '../src/types';
import fixtures from '../../contracts/phase3.json';
import cases from '../../contracts/management.json';

const route = vi.hoisted(() => ({ id: 'notebook-a', refresh: vi.fn(), push: vi.fn() }));
vi.mock('next/navigation', () => ({ useParams: () => ({ id: route.id }), useRouter: () => ({ push: route.push }) }));
vi.mock('next/image', () => ({ default: ({ alt }: { alt: string }) => <span>{alt}</span> }));
vi.mock('@/contexts/NotebookContext', () => ({ useNotebooks: () => ({ refreshNotebooks: route.refresh }) }));
const notebook: Notebook = { ...fixtures.notebook, category: 'study' };

beforeEach(() => { route.id = 'notebook-a'; route.refresh.mockClear(); });
afterEach(() => { vi.restoreAllMocks(); vi.useRealTimers(); });

test('search/filter/sort use the shared Vietnamese cases', () => {
  for (const row of cases.notebook_cases) expect(selectNotebooks(cases.notebooks as Notebook[], row.query, row.category, row.sort as 'newest' | 'oldest' | 'name').map(item => item.notebook_id)).toEqual(row.expected);
  for (const row of cases.document_cases) expect(selectDocuments(cases.documents as DocumentItem[], row.query, row.extension, row.status, row.sort as 'newest' | 'oldest' | 'name').map(item => item.document_id)).toEqual(row.expected);
  expect(cases.notebooks[0].title).toBe('Đề cương Toán');
});

test('create persists description and chosen category independently of title', async () => {
  const create = vi.spyOn(apiService, 'createNotebook').mockResolvedValue(notebook);
  const saved = vi.fn();
  render(<CreateNotebookModal isOpen onClose={vi.fn()} onCreated={saved} />);
  fireEvent.change(screen.getByLabelText('Tên sổ tay'), { target: { value: 'Toán học' } });
  fireEvent.change(screen.getByLabelText('Mô tả'), { target: { value: 'Mô tả thật' } });
  fireEvent.click(screen.getByRole('button', { name: /Nghiên cứu/ }));
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Tạo sổ tay' })); });
  expect(create).toHaveBeenCalledWith('Toán học', expect.objectContaining({ category: 'research', description: 'Mô tả thật' }));
  expect(saved).toHaveBeenCalledTimes(1);
});

test('edit can clear description without creating another notebook', async () => {
  const update = vi.spyOn(apiService, 'updateNotebook').mockResolvedValue(notebook);
  const create = vi.spyOn(apiService, 'createNotebook');
  render(<CreateNotebookModal isOpen notebook={notebook} onClose={vi.fn()} onCreated={vi.fn()} />);
  fireEvent.change(screen.getByLabelText('Mô tả'), { target: { value: '' } });
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Lưu thay đổi' })); });
  expect(update).toHaveBeenCalledWith(notebook.notebook_id, expect.objectContaining({ category: 'study', description: '' }));
  expect(create).not.toHaveBeenCalled();
});

test('late modal save cannot close the editor for another notebook', async () => {
  let finish!: (value: Notebook) => void;
  vi.spyOn(apiService, 'updateNotebook').mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  const saved = vi.fn(); const close = vi.fn();
  const view = render(<CreateNotebookModal isOpen notebook={notebook} onClose={close} onCreated={saved} />);
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Lưu thay đổi' })); });
  view.rerender(<CreateNotebookModal isOpen notebook={{ ...notebook, notebook_id: 'b', title: 'Notebook B' }} onClose={close} onCreated={saved} />);
  await act(async () => { finish(notebook); });
  expect(saved).not.toHaveBeenCalled(); expect(close).not.toHaveBeenCalled();
  expect(screen.getByLabelText('Tên sổ tay')).toHaveValue('Notebook B');
});

test('storage-only page disables AI and never polls uploaded documents', async () => {
  vi.useFakeTimers();
  vi.spyOn(apiService, 'getAppConfig').mockResolvedValue({ ai_enabled: false });
  vi.spyOn(apiService, 'getNotebook').mockResolvedValue(notebook);
  const documents = vi.spyOn(apiService, 'getDocuments').mockResolvedValue(cases.documents as DocumentItem[]);
  render(<NotebookPage />); await act(async () => {});
  expect(screen.getByRole('button', { name: 'Chat với AI' })).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Tóm tắt' })).toBeDisabled();
  await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
  expect(documents).toHaveBeenCalledTimes(1);
  fireEvent.change(screen.getByLabelText('Tìm tài liệu'), { target: { value: 'DE CUONG' } });
  expect(screen.getByText('Đề cương.PDF')).toBeInTheDocument();
  expect(screen.queryByText('Bài tập.txt')).not.toBeInTheDocument();
});

test('late document response from a previous notebook is ignored', async () => {
  let finish!: (value: DocumentItem[]) => void;
  vi.spyOn(apiService, 'getAppConfig').mockResolvedValue({ ai_enabled: false });
  vi.spyOn(apiService, 'getNotebook').mockImplementation(async id => ({ ...notebook, notebook_id: id, title: id }));
  vi.spyOn(apiService, 'getDocuments').mockImplementation(id => id === 'notebook-a' ? new Promise(resolve => { finish = resolve; }) : Promise.resolve([]));
  const view = render(<NotebookPage />); await act(async () => {});
  route.id = 'notebook-b'; view.rerender(<NotebookPage />); await act(async () => {});
  await act(async () => { finish(cases.documents as DocumentItem[]); });
  expect(screen.queryByText('Đề cương.PDF')).not.toBeInTheDocument();
  expect(screen.getByRole('heading', { name: 'notebook-b' })).toBeInTheDocument();
});
