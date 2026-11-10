import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import fixtures from '../../contracts/learning.json';
import FlashcardDeck from '@/components/notebooks/FlashcardDeck';
import { learningApi, type Flashcard } from '@/lib/learning-api';

vi.mock('@/lib/learning-api', async importOriginal => {
  const original = await importOriginal<typeof import('@/lib/learning-api')>();
  return { ...original, learningApi: { ...original.learningApi, cards: vi.fn(), stats: vi.fn(), due: vi.fn(), review: vi.fn(), createCard: vi.fn(), editCard: vi.fn(), deleteCard: vi.fn(), download: vi.fn() } };
});
vi.mock('@/lib/api', async importOriginal => {
  const original = await importOriginal<typeof import('@/lib/api')>();
  return { ...original, apiService: { ...original.apiService, getDocuments: vi.fn().mockResolvedValue([]) } };
});

const card = fixtures.card as Flashcard;
const stats = { total_cards: 1, due_cards: 1, reviewed_today: 0, streak_days: 0, timezone: 'Asia/Ho_Chi_Minh', server_now: '2026-11-10T10:00:00Z' };
beforeEach(() => {
  vi.clearAllMocks();
  HTMLDialogElement.prototype.showModal = vi.fn(function (this: HTMLDialogElement) { this.setAttribute('open', ''); });
  vi.mocked(learningApi.cards).mockResolvedValue({ items: [card], next_cursor: null });
  vi.mocked(learningApi.stats).mockResolvedValue(stats);
  vi.mocked(learningApi.due).mockResolvedValue({ items: [card], next_cursor: null });
});

it('lượt ôn lỗi mạng giữ thẻ và dùng lại UUID đến khi server xác nhận', async () => {
  vi.mocked(learningApi.review).mockRejectedValueOnce(new Error('Mất mạng, chưa xác nhận lưu')).mockResolvedValueOnce({ ...card.review, revision: 1 });
  render(<FlashcardDeck notebookId={card.notebook_id} />);
  await screen.findByText(card.question);
  fireEvent.click(screen.getByRole('button', { name: 'Ôn thẻ đến hạn' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Xem đáp án' }));
  fireEvent.click(screen.getByRole('button', { name: 'Đã nhớ' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Mất mạng');
  expect(screen.getByText(card.question)).toBeInTheDocument();
  const identifier = vi.mocked(learningApi.review).mock.calls[0][2];
  fireEvent.click(screen.getByRole('button', { name: 'Thử lưu lại lượt ôn' }));
  expect(await screen.findByText('Không còn thẻ đến hạn trong lượt này.')).toBeInTheDocument();
  expect(vi.mocked(learningApi.review).mock.calls[1][2]).toBe(identifier);
});

it('tạo thẻ thật qua API, dữ liệu đang nhập được giữ khi lưu lỗi', async () => {
  vi.mocked(learningApi.createCard).mockRejectedValueOnce(new Error('Chưa kết nối')).mockResolvedValueOnce(card);
  render(<FlashcardDeck notebookId={card.notebook_id} />);
  await screen.findByText(card.question);
  fireEvent.click(screen.getByRole('button', { name: 'Tạo thẻ' }));
  fireEvent.change(screen.getByLabelText('Câu hỏi'), { target: { value: 'Câu hỏi do tôi nhập' } });
  fireEvent.change(screen.getByLabelText('Đáp án'), { target: { value: 'Đáp án do tôi nhập' } });
  fireEvent.click(screen.getByRole('button', { name: 'Lưu thẻ' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Chưa kết nối');
  expect(screen.getByLabelText('Câu hỏi')).toHaveValue('Câu hỏi do tôi nhập');
  fireEvent.click(screen.getByRole('button', { name: 'Lưu thẻ' }));
  await waitFor(() => expect(screen.queryByRole('heading', { name: 'Tạo thẻ học' })).not.toBeInTheDocument());
  expect(learningApi.createCard).toHaveBeenLastCalledWith(card.notebook_id, { question: 'Câu hỏi do tôi nhập', answer: 'Đáp án do tôi nhập', source: null });
});

it('xung đột từ thiết bị khác tải lại hàng đợi từ server', async () => {
  vi.mocked(learningApi.due).mockResolvedValueOnce({ items: [card], next_cursor: null }).mockResolvedValueOnce({ items: [], next_cursor: null });
  vi.mocked(learningApi.review).mockRejectedValue({ isAxiosError: true, response: { status: 409, data: { detail: 'ERR_REVIEW_CONFLICT' } } });
  render(<FlashcardDeck notebookId={card.notebook_id} />);
  await screen.findByText(card.question);
  fireEvent.click(screen.getByRole('button', { name: 'Ôn thẻ đến hạn' }));
  fireEvent.click(await screen.findByRole('button', { name: 'Xem đáp án' }));
  fireEvent.click(screen.getByRole('button', { name: 'Đã nhớ' }));
  expect(await screen.findByText('Không còn thẻ đến hạn trong lượt này.')).toBeInTheDocument();
  expect(learningApi.due).toHaveBeenCalledTimes(2);
  expect(await screen.findByRole('alert')).toHaveTextContent('thiết bị khác');
});
