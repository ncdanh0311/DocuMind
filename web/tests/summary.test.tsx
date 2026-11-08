import React from 'react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, fireEvent, render, screen } from '@testing-library/react';
import SummaryPage from '../src/app/(dashboard)/summary/page';
import { apiService } from '../src/lib/api';
import type { SummaryRecord } from '../src/types';
import fixtures from '../../contracts/phase3.json';

vi.mock('next/navigation', () => ({ useSearchParams: () => new URLSearchParams('notebookId=notebook-a') }));
vi.mock('@/contexts/NotebookContext', () => ({ useNotebooks: () => ({ notebooks: [{ notebook_id: 'notebook-a', title: 'A' }, { notebook_id: 'notebook-b', title: 'B' }] }) }));
const complete: SummaryRecord = { ...fixtures.summary, model: 'vit5', status: 'succeeded' };
const queued: SummaryRecord = { ...complete, status: 'queued', summary: null, processed_units: 0, coverage: 0 };

beforeEach(() => {
  localStorage.clear(); vi.useFakeTimers();
  vi.spyOn(apiService, 'getCapabilities').mockResolvedValue([{ id: 'vit5', task: 'summarization', ready: true, version: 'v1' }]);
});
afterEach(() => { vi.useRealTimers(); vi.restoreAllMocks(); });
async function mount() { const value = render(<SummaryPage />); await act(async () => {}); return value; }

test('polls a durable summary and stops on completion', async () => {
  const start = vi.spyOn(apiService, 'summarizeNotebook').mockResolvedValue(queued);
  const poll = vi.spyOn(apiService, 'getSummary').mockResolvedValue(complete);
  await mount();
  await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Tạo bản tóm tắt' })); });
  expect(start).toHaveBeenCalledTimes(1);
  expect(screen.getByText('Đang chờ xử lý')).toBeInTheDocument();
  await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
  expect(screen.getByText('A summary.')).toBeInTheDocument();
  await act(async () => { await vi.advanceTimersByTimeAsync(9000); });
  expect(poll).toHaveBeenCalledTimes(1);
});

test('resumes stored job and cancels polling on unmount', async () => {
  localStorage.setItem('documind:summary:notebook-a:vit5', queued.summary_id);
  const poll = vi.spyOn(apiService, 'getSummary').mockResolvedValue(queued);
  const start = vi.spyOn(apiService, 'summarizeNotebook');
  const view = await mount();
  expect(poll).toHaveBeenCalledWith(queued.summary_id);
  expect(start).not.toHaveBeenCalled();
  view.unmount();
  await act(async () => { await vi.advanceTimersByTimeAsync(9000); });
  expect(poll).toHaveBeenCalledTimes(1);
});

test('ignores a late result from the previous notebook', async () => {
  let resolve!: (record: SummaryRecord) => void;
  localStorage.setItem('documind:summary:notebook-a:vit5', queued.summary_id);
  vi.spyOn(apiService, 'getSummary').mockImplementation(() => new Promise((done) => { resolve = done; }));
  await mount();
  await act(async () => { fireEvent.change(screen.getByLabelText('Sổ tay'), { target: { value: 'notebook-b' } }); });
  await act(async () => { resolve(complete); });
  expect(screen.queryByText('A summary.')).not.toBeInTheDocument();
});

test('stale summaries hide cached content and do not poll', async () => {
  localStorage.setItem('documind:summary:notebook-a:vit5', queued.summary_id);
  const poll = vi.spyOn(apiService, 'getSummary').mockResolvedValue({ ...complete, stale: true });
  await mount();
  expect(screen.queryByText('A summary.')).not.toBeInTheDocument();
  expect(screen.getByRole('alert')).toHaveTextContent('Tài liệu đã thay đổi');
  await act(async () => { await vi.advanceTimersByTimeAsync(9000); });
  expect(poll).toHaveBeenCalledTimes(1);
});
