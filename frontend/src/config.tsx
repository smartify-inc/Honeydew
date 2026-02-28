import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { AppConfig, ProfileInfo } from './types';
import { ConfigContext, type ConfigContextValue } from './configContext';

const API_BASE = 'http://localhost:8000';

const DEFAULT_CONFIG: AppConfig = {
  user: { profile_id: 'user', display_name: 'User' },
  agent: { profile_id: 'agent', display_name: 'Agent' },
  boards: [{ name: 'My Board', columns: ['To Do', 'In Progress', 'Done'] }],
};

function buildProfiles(config: AppConfig): Record<string, ProfileInfo> {
  return {
    [config.user.profile_id]: {
      name: config.user.display_name,
      icon: config.user.display_name[0].toUpperCase(),
      color: 'from-cyan-400 to-purple-500',
      role: 'user',
    },
    [config.agent.profile_id]: {
      name: config.agent.display_name,
      icon: config.agent.display_name[0].toUpperCase(),
      color: 'from-purple-500 to-pink-500',
      role: 'agent',
    },
  };
}

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [value, setValue] = useState<ConfigContextValue | null>(null);

  useEffect(() => {
    fetch(`${API_BASE}/api/config`)
      .then((res) => res.json())
      .then((data: AppConfig) => {
        const profiles = buildProfiles(data);
        setValue({ config: data, profiles, profileIds: Object.keys(profiles) });
      })
      .catch(() => {
        const profiles = buildProfiles(DEFAULT_CONFIG);
        setValue({ config: DEFAULT_CONFIG, profiles, profileIds: Object.keys(profiles) });
      });
  }, []);

  if (!value) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-cyan-400 border-t-transparent"></div>
      </div>
    );
  }

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}
