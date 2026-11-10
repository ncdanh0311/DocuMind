import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DocumentReader from '@/components/notebooks/DocumentReader';
import NotebookHistory from '@/components/notebooks/NotebookHistory';
import { learningApi, selectedSource } from '@/lib/learning-api';
import fixtures from '../../contracts/learning.json';

vi.mock('@/lib/learning-api', async importOriginal => {
  const original = await importOriginal<typeof import('@/lib/learning-api')>();
  return { ...original, learningApi: { extract: vi.fn(), source: vi.fn(), history: vi.fn(), historyDetail: vi.fn(), download: vi.fn() } };
});

beforeEach(() => {
  vi.clearAllMocks();
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) { this.setAttribute('open', ''); });
  vi.mocked(learningApi.extract).mockResolvedValue({ text_status: 'ready' });
});

describe('Đọc và lịch sử khi AI tắt', () => {
  it('chuyển vị trí emoji từ UTF-16 sang code point dùng cho nguồn', () => {
    for (const item of fixtures.selection_examples) expect(selectedSource(item.text, item.start_utf16, item.end_utf16, item.base)).toEqual(item.expected);
  });
  it('đọc nguồn thật và tải file gốc khi trích văn bản gặp lỗi', async () => {
    vi.mocked(learningApi.extract).mockRejectedValue(new Error('PDF cần OCR'));
    render(<DocumentReader id="document" name="source.pdf" onClose={vi.fn()} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('PDF cần OCR');
    fireEvent.click(screen.getByRole('button', { name: 'Tải file gốc' }));
    expect(learningApi.download).toHaveBeenCalledWith('/documents/document/download', 'source.pdf');
  });
  it('nguồn phiên bản cũ được mở trực tiếp, không trích lại file', async () => {
    vi.mocked(learningApi.source).mockResolvedValue({ document_id: 'doc', version: 2, text: 'Nội dung gốc', start_offset: 0, end_offset: 12, sections: [{ start: 0, end: 12, section_path: 'Trang 1' }] });
    render(<DocumentReader id="doc" name="Nguồn" version={2} onClose={vi.fn()} />);
    expect(await screen.findByRole('textbox', { name: 'Nội dung tài liệu' })).toHaveValue('Nội dung gốc');
    expect(learningApi.extract).not.toHaveBeenCalled();
    expect(learningApi.source).toHaveBeenCalledWith('doc', 2);
  });
  it('mở lịch sử có nguồn đã xóa và phân trang từ server', async () => {
    const item = { id: 'qa1', kind: 'qa' as const, title: 'Câu hỏi đã lưu', model: 'xlmroberta_qa', created_at: '2026-11-10T10:00:00Z' };
    vi.mocked(learningApi.history).mockResolvedValueOnce({ items: [item], next_cursor: 'next' }).mockResolvedValueOnce({ items: [], next_cursor: null });
    vi.mocked(learningApi.historyDetail).mockResolvedValue({ id: 'qa1', model: 'xlmroberta_qa', model_version: 'old', created_at: item.created_at, answer: 'Câu trả lời thật', citations: [{ document_id: 'doc', version: 1, start_offset: 0, end_offset: 2, source_title: 'Đã xóa.pdf', snippet: 'Trích đoạn còn giữ', source_state: 'missing' }] });
    render(<NotebookHistory notebookId="notebook" />);
    fireEvent.click(await screen.findByRole('button', { name: /Câu hỏi đã lưu/ }));
    expect(await screen.findByText('Câu trả lời thật')).toBeInTheDocument();
    expect(screen.getByText('Trích đoạn còn giữ')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Mở nguồn đã lưu' })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Xem thêm lịch sử' }));
    await waitFor(() => expect(learningApi.history).toHaveBeenLastCalledWith('notebook', 'next'));
  });
});
