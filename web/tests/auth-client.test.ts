import { beforeEach, afterEach, expect, test, vi } from 'vitest';
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { apiClient, apiService, tokenManager } from '../src/lib/api';
import fixtures from '../../contracts/phase3.json';
import type { TokenResponse, ResetTokenResponse, ChatResponse, NotificationItem, Notebook } from '../src/types';

const initialAdapter = apiClient.defaults.adapter;
const refreshAdapter = axios.defaults.adapter;
const response = (config: InternalAxiosRequestConfig, data: unknown, status = 200) => ({ data, status, statusText: String(status), headers: {}, config });
function unauthorized(config: InternalAxiosRequestConfig): never {
  throw new AxiosError('Expired', 'ERR_BAD_REQUEST', config, undefined, response(config, { detail: 'ERR_UNAUTHORIZED' }, 401));
}
beforeEach(() => { localStorage.clear(); });
afterEach(() => { apiClient.defaults.adapter = initialAdapter; axios.defaults.adapter = refreshAdapter; });

test('parallel expired requests rotate refresh credentials only once', async () => {
  tokenManager.setTokens('expired', 'refresh-old');
  const refresh = vi.fn(async (config: InternalAxiosRequestConfig) => {
    await new Promise((resolve) => setTimeout(resolve, 15));
    return response(config, { ...fixtures.token, access_token: 'fresh', refresh_token: 'rotated' });
  });
  axios.defaults.adapter = refresh;
  apiClient.defaults.adapter = async (config) => {
    if (config.headers.Authorization !== 'Bearer fresh') unauthorized(config);
    return response(config, fixtures.user);
  };
  const results = await Promise.all(Array.from({ length: 8 }, () => apiService.getProfile()));
  expect(results).toHaveLength(8);
  expect(refresh).toHaveBeenCalledTimes(1);
  expect(tokenManager.getRefreshToken()).toBe('rotated');
});

test('bad login never invokes refresh interceptor', async () => {
  tokenManager.setTokens('expired', 'refresh-old');
  const refresh = vi.fn(); axios.defaults.adapter = refresh;
  apiClient.defaults.adapter = async (config) => unauthorized(config);
  await expect(apiService.login('alice@example.com', 'wrong')).rejects.toMatchObject({ response: { status: 401 } });
  expect(refresh).not.toHaveBeenCalled();
});

test('invalid refresh clears credentials but a network outage retains them', async () => {
  tokenManager.setTokens('expired', 'refresh-old');
  apiClient.defaults.adapter = async (config) => unauthorized(config);
  axios.defaults.adapter = async (config) => { throw new AxiosError('Offline', 'ERR_NETWORK', config); };
  await expect(apiService.getProfile()).rejects.toBeDefined();
  expect(tokenManager.getRefreshToken()).toBe('refresh-old');
  axios.defaults.adapter = async (config) => unauthorized(config);
  await expect(apiService.getProfile()).rejects.toBeDefined();
  expect(tokenManager.getAccessToken()).toBeNull();
});

test('late refresh cannot restore a logged-out session', async () => {
  tokenManager.setTokens('expired', 'refresh-old');
  apiClient.defaults.adapter = async (config) => unauthorized(config);
  axios.defaults.adapter = async (config) => {
    tokenManager.clearAuth();
    return response(config, fixtures.token);
  };
  await expect(apiService.getProfile()).rejects.toThrow('Session changed');
  expect(tokenManager.getAccessToken()).toBeNull();
});

test('wire DTOs retain canonical reset, source, notification and count fields', () => {
  const token: TokenResponse = fixtures.token as TokenResponse;
  const reset: ResetTokenResponse = fixtures.reset;
  const chat: ChatResponse = { ...fixtures.chat, status: 'answered' };
  const notification: NotificationItem = fixtures.notification;
  const notebook: Notebook = { ...fixtures.notebook, category: 'study' };
  expect(token.refresh_token).toBe('fixture-refresh');
  expect(reset.reset_token).toBe('fixture-reset');
  expect(chat.citations[0]).toMatchObject({ source_title: 'Study.pdf', page_number: 3, snippet: 'An answer.' });
  expect(notification.body).toBe('Document processed');
  expect(notebook.document_count).toBe(2);
});
