// API client for the Kanban board backend

const API_BASE = 'http://localhost:8000/api';

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Board endpoints
export const boardsApi = {
  list: () => request<{ id: number; name: string; created_at: string }[]>('/boards'),
  get: (id: number, profile?: string) => {
    const query = profile ? `?profile=${profile}` : '';
    return request<import('../types').Board>(`/boards/${id}${query}`);
  },
  create: (name: string) => request<import('../types').Board>('/boards', {
    method: 'POST',
    body: JSON.stringify({ name }),
  }),
  delete: (id: number) => request<void>(`/boards/${id}`, { method: 'DELETE' }),
};

// Column endpoints
export const columnsApi = {
  create: (boardId: number, name: string, position?: number) =>
    request<import('../types').Column>('/columns', {
      method: 'POST',
      body: JSON.stringify({ board_id: boardId, name, position }),
    }),
  update: (id: number, data: { name?: string; position?: number }) =>
    request<import('../types').Column>(`/columns/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<void>(`/columns/${id}`, { method: 'DELETE' }),
};

// Card endpoints
export const cardsApi = {
  list: (params?: { board_id?: number; column_id?: number; priority?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.board_id) searchParams.set('board_id', String(params.board_id));
    if (params?.column_id) searchParams.set('column_id', String(params.column_id));
    if (params?.priority) searchParams.set('priority', String(params.priority));
    const query = searchParams.toString();
    return request<import('../types').Card[]>(`/cards${query ? `?${query}` : ''}`);
  },
  get: (id: number) => request<import('../types').Card>(`/cards/${id}`),
  create: (data: import('../types').CardCreate) =>
    request<import('../types').Card>('/cards', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  update: (id: number, data: import('../types').CardUpdate) =>
    request<import('../types').Card>(`/cards/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  move: (id: number, data: import('../types').CardMove) =>
    request<import('../types').Card>(`/cards/${id}/move`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<void>(`/cards/${id}`, { method: 'DELETE' }),
  transfer: (id: number, targetProfile: string) =>
    request<import('../types').Card>(`/cards/${id}/transfer`, {
      method: 'POST',
      body: JSON.stringify({ target_profile: targetProfile }),
    }),
  moveToBoard: (cardId: number, boardId: number) =>
    request<import('../types').Card>(`/cards/${cardId}/move-to-board`, {
      method: 'POST',
      body: JSON.stringify({ board_id: boardId }),
    }),
  addLabel: (cardId: number, labelId: number) =>
    request<import('../types').Card>(`/cards/${cardId}/labels/${labelId}`, {
      method: 'POST',
    }),
  removeLabel: (cardId: number, labelId: number) =>
    request<void>(`/cards/${cardId}/labels/${labelId}`, { method: 'DELETE' }),
  addComment: (cardId: number, body: string, profile?: string) =>
    request<import('../types').CardComment>(`/cards/${cardId}/comments`, {
      method: 'POST',
      body: JSON.stringify({ body, ...(profile ? { profile } : {}) }),
    }),
};

// Label endpoints
export const labelsApi = {
  list: () => request<import('../types').Label[]>('/labels'),
  create: (name: string, color: string) =>
    request<import('../types').Label>('/labels', {
      method: 'POST',
      body: JSON.stringify({ name, color }),
    }),
  update: (id: number, data: { name?: string; color?: string }) =>
    request<import('../types').Label>(`/labels/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  delete: (id: number) => request<void>(`/labels/${id}`, { method: 'DELETE' }),
};
