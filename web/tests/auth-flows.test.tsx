import React from 'react';
import { beforeEach, afterEach, expect, test, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AuthProvider, useAuth } from '../src/contexts/AuthContext';
import { apiService, tokenManager } from '../src/lib/api';
import LoginPage from '../src/app/(auth)/login/page';
import ResetPasswordPage from '../src/app/(auth)/reset-password/page';
import fixtures from '../../contracts/phase3.json';

const { replace } = vi.hoisted(() => ({ replace: vi.fn() }));
vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace, push: replace }),
  useSearchParams: () => new URLSearchParams('email=alice%40example.com'),
}));
vi.mock('next/image', () => ({ default: ({ alt }: { alt: string }) => <span>{alt}</span> }));

function SessionProbe() {
  const { user, isAuthenticated } = useAuth();
  return <output data-testid="session">{isAuthenticated ? user?.email : 'anonymous'}</output>;
}
beforeEach(() => { localStorage.clear(); replace.mockClear(); });
afterEach(() => { vi.restoreAllMocks(); });

test('login loads the real profile into context before navigating', async () => {
  const login = vi.spyOn(apiService, 'login').mockImplementation(async () => {
    tokenManager.setTokens(fixtures.token.access_token, fixtures.token.refresh_token);
    return { ...fixtures.token, token_type: 'bearer' };
  });
  vi.spyOn(apiService, 'getProfile').mockResolvedValue(fixtures.user);
  render(<AuthProvider><LoginPage /><SessionProbe /></AuthProvider>);
  await userEvent.type(screen.getByPlaceholderText('name@example.com'), 'alice@example.com');
  await userEvent.type(screen.getByPlaceholderText('Nhập mật khẩu của bạn'), 'correct-password');
  await userEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }));
  await waitFor(() => expect(screen.getByTestId('session')).toHaveTextContent('alice@example.com'));
  expect(login).toHaveBeenCalledWith('alice@example.com', 'correct-password');
  expect(replace).toHaveBeenCalledWith('/');
});

test('OTP reset sends reset_token and synchronizes the authenticated profile', async () => {
  vi.spyOn(apiService, 'verifyOtp').mockResolvedValue(fixtures.reset);
  const reset = vi.spyOn(apiService, 'resetPassword').mockImplementation(async () => {
    tokenManager.setTokens(fixtures.token.access_token, fixtures.token.refresh_token);
    return { ...fixtures.token, token_type: 'bearer', message: 'MSG_PASSWORD_RESET_SUCCESS' };
  });
  vi.spyOn(apiService, 'getProfile').mockResolvedValue(fixtures.user);
  render(<AuthProvider><ResetPasswordPage /><SessionProbe /></AuthProvider>);
  await userEvent.type(screen.getByPlaceholderText('VD: 123456'), '123456');
  await userEvent.type(screen.getByPlaceholderText('Tối thiểu 8 ký tự'), 'new-password');
  await userEvent.type(screen.getByPlaceholderText('Nhập lại mật khẩu mới'), 'new-password');
  const submit = document.querySelector<HTMLButtonElement>('button[type="submit"]');
  expect(submit).not.toBeNull();
  await userEvent.click(submit!);
  await waitFor(() => expect(reset).toHaveBeenCalledWith('fixture-reset', 'new-password'));
  await waitFor(() => expect(screen.getByTestId('session')).toHaveTextContent('alice@example.com'));
  expect(replace).toHaveBeenCalledWith('/');
});
