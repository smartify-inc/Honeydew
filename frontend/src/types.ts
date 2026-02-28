// TypeScript types for the Kanban board

export interface Label {
  id: number;
  name: string;
  color: string;
}

export interface CardComment {
  id: number;
  card_id: number;
  profile: string;
  body: string;
  created_at: string;
}

export interface Card {
  id: number;
  column_id: number;
  profile: string;
  title: string;
  description: string | null;
  priority: number;
  due_date: string | null;
  position: number;
  created_at: string;
  updated_at: string;
  labels: Label[];
  comments: CardComment[];
  agent_tokens_used?: number | null;
  agent_model?: string | null;
  agent_execution_time_seconds?: number | null;
  agent_started_at?: string | null;
  agent_completed_at?: string | null;
}

export interface Column {
  id: number;
  board_id: number;
  name: string;
  position: number;
  cards: Card[];
}

export interface Board {
  id: number;
  name: string;
  created_at: string;
  columns: Column[];
}

export interface CardCreate {
  column_id: number;
  title: string;
  description?: string | null;
  priority?: number;
  due_date?: string | null;
  profile?: string;
}

export interface CardUpdate {
  title?: string;
  description?: string | null;
  priority?: number;
  due_date?: string | null;
}

export interface CardMove {
  column_id: number;
  position: number;
}

// Dark theme priority labels with neon accents
export const PRIORITY_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'Low', color: 'bg-gray-700/50 text-gray-400' },
  2: { label: 'Medium', color: 'bg-cyan-500/20 text-cyan-400' },
  3: { label: 'High', color: 'bg-orange-500/20 text-orange-400' },
  4: { label: 'Urgent', color: 'bg-red-500/20 text-red-400' },
};

// Config types
export interface ProfileConfig {
  profile_id: string;
  display_name: string;
}

export interface BoardConfig {
  name: string;
  columns: string[];
}

export interface AppConfig {
  user: ProfileConfig;
  agent: ProfileConfig;
  boards?: BoardConfig[];
}

export interface ProfileInfo {
  name: string;
  icon: string;
  color: string;
  role: 'user' | 'agent';
}
