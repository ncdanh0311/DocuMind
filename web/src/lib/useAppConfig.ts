'use client';
import { useEffect, useState } from 'react';
import { apiService } from './api';

export function useAppConfig() {
  const [aiEnabled, setAIEnabled] = useState(false);
  useEffect(() => {
    let active = true;
    apiService.getAppConfig().then(value => { if (active) setAIEnabled(value.ai_enabled); }).catch(() => {});
    return () => { active = false; };
  }, []);
  return { aiEnabled };
}
