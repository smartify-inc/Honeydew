import { createContext, useContext } from 'react';
import type { AppConfig, ProfileInfo } from './types';

export interface ConfigContextValue {
  config: AppConfig;
  profiles: Record<string, ProfileInfo>;
  profileIds: string[];
}

export const ConfigContext = createContext<ConfigContextValue | null>(null);

export function useConfig(): ConfigContextValue {
  const ctx = useContext(ConfigContext);
  if (!ctx) throw new Error('useConfig must be used within ConfigProvider');
  return ctx;
}
