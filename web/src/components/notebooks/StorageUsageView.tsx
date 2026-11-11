'use client';
import { useCallback, useEffect, useState } from 'react';
import { learningApi, type StorageUsage } from '@/lib/learning-api';
import { getErrorMessage } from '@/lib/api';

export default function StorageUsageView({ refreshKey }: { refreshKey: string }) {
  const [usage, setUsage] = useState<StorageUsage | null>(null); const [error, setError] = useState('');
  const load = useCallback(async () => { try { setUsage(await learningApi.usage()); setError(''); } catch (err) { setError(getErrorMessage(err)); } }, []);
  useEffect(() => { void load(); }, [refreshKey, load]);
  return <aside className="text-sm border rounded-xl p-3" aria-label="Dung lượng lưu trữ">
    {usage ? <>Dung lượng: {(usage.used_bytes / 1048576).toFixed(1)} / {(usage.limit_bytes / 1048576).toFixed(0)} MiB
      <progress className="block w-full mt-2" aria-label="Dung lượng đã dùng" value={usage.used_bytes} max={usage.limit_bytes} />
      <span className="text-xs text-gray-600">Tối đa {(usage.max_file_bytes / 1048576).toFixed(0)} MiB/file.</span></> : 'Đang kiểm tra dung lượng…'}
    {error && <p role="alert">{error} <button className="underline" onClick={load}>Kiểm tra lại</button></p>}
  </aside>;
}
