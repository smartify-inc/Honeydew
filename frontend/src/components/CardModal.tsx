import { useState, useEffect } from 'react';
import type { Card, CardUpdate, CardComment } from '../types';
import { PRIORITY_LABELS } from '../types';
import { cardsApi } from '../api/client';

interface BoardListItem {
  id: number;
  name: string;
}

interface ColumnInfo {
  id: number;
  name: string;
}

const COMPLETION_SYNONYMS = ['done', 'complete', 'completed', 'over', 'finished'];

interface CardModalProps {
  card: Card | null;
  isCreating: boolean;
  columnId: number | null;
  currentProfile: string;
  currentBoardId?: number;
  boardList: BoardListItem[];
  columns: ColumnInfo[];
  onClose: () => void;
  onSave: (data: CardUpdate & { column_id?: number; title?: string }) => void;
  onDelete?: () => void;
  onMoveToBoard?: (boardId: number) => void;
  onMarkComplete?: (cardId: number, completionColumnId: number) => void;
}

export function CardModal({
  card,
  isCreating,
  columnId,
  currentProfile,
  currentBoardId,
  boardList,
  columns,
  onClose,
  onSave,
  onDelete,
  onMoveToBoard,
  onMarkComplete,
}: CardModalProps) {
  const completionColumn = columns.find(c => COMPLETION_SYNONYMS.includes(c.name.trim().toLowerCase()));
  const completionColumnId = completionColumn?.id;
  const canMarkComplete = !isCreating && card && completionColumnId != null && card.column_id !== completionColumnId;

  const nextBoardId = (() => {
    if (boardList.length <= 1) return '';
    const idx = boardList.findIndex(b => b.id === currentBoardId);
    const next = boardList[(idx + 1) % boardList.length];
    return next && next.id !== currentBoardId ? next.id : boardList.find(b => b.id !== currentBoardId)?.id ?? '';
  })();
  const [selectedMoveBoardId, setSelectedMoveBoardId] = useState<number | ''>(nextBoardId);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(2);
  const [dueDate, setDueDate] = useState('');
  const [comments, setComments] = useState<CardComment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [addingComment, setAddingComment] = useState(false);

  useEffect(() => {
    if (card) {
      setTitle(card.title);
      setDescription(card.description || '');
      setPriority(card.priority);
      setDueDate(card.due_date || '');
      setComments(card.comments ?? []);
    } else {
      setTitle('');
      setDescription('');
      setPriority(2);
      setDueDate('');
      setComments([]);
    }
  }, [card]);

  const handleAddComment = async () => {
    if (!card || !newComment.trim()) return;
    setAddingComment(true);
    try {
      const created = await cardsApi.addComment(card.id, newComment.trim(), currentProfile);
      setComments(prev => [...prev, created]);
      setNewComment('');
    } catch (err) {
      console.error('Failed to add comment:', err);
    } finally {
      setAddingComment(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const data: CardUpdate & { column_id?: number; title?: string } = {
      title: title.trim(),
      description: description.trim() || null,
      priority,
      due_date: dueDate || null,
    };

    if (isCreating && columnId) {
      data.column_id = columnId;
    }

    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-end md:items-center justify-center z-50">
      <div className="bg-[#12121a] border border-[#2a2a3a] rounded-t-xl md:rounded-xl shadow-[0_0_50px_rgba(0,245,255,0.1)] w-full max-h-[90dvh] md:max-h-[85vh] md:max-w-lg md:mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 md:px-6 md:py-4 border-b border-[#2a2a3a] shrink-0">
          <h2 className="text-lg font-semibold text-gray-100">
            {isCreating ? 'Create Task' : 'Edit Task'}
          </h2>
          <button
            onClick={onClose}
            className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-[#2a2a3a] rounded-lg transition-colors group"
          >
            <svg
              className="w-5 h-5 text-gray-500 group-hover:text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 md:p-6 space-y-4 overflow-y-auto flex-1">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done?"
              className="w-full px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 placeholder-gray-600 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add more details..."
              rows={3}
              className="w-full px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 placeholder-gray-600 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all resize-none"
            />
          </div>

          {/* Priority and Due Date */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Priority
              </label>
              <select
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
              >
                {Object.entries(PRIORITY_LABELS).map(([value, { label }]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                style={{ colorScheme: 'dark' }}
              />
            </div>
          </div>

          {/* Move to board (only for existing cards, when multiple boards exist) */}
          {!isCreating && onMoveToBoard && card && boardList.length > 1 && (
            <div className="border-t border-[#2a2a3a] pt-4">
              <p className="text-sm text-gray-400 mb-2">Move to another board:</p>
              <div className="flex gap-2 items-center">
                <select
                  value={selectedMoveBoardId}
                  onChange={(e) => setSelectedMoveBoardId(Number(e.target.value))}
                  className="flex-1 px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 focus:ring-2 focus:ring-cyan-500/50"
                >
                  {boardList
                    .filter(b => b.id !== currentBoardId)
                    .map((b) => (
                      <option key={b.id} value={b.id}>{b.name}</option>
                    ))}
                </select>
                <button
                  type="button"
                  disabled={selectedMoveBoardId === ''}
                  onClick={() => {
                    if (selectedMoveBoardId !== '') {
                      onMoveToBoard(selectedMoveBoardId);
                      setSelectedMoveBoardId('');
                    }
                  }}
                  className="px-4 py-2.5 min-h-[44px] rounded-lg border border-purple-500/30 hover:bg-purple-500/10 text-purple-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Move
                </button>
              </div>
            </div>
          )}

          {/* Agent Completion Metadata (read-only, shown when agent reported it) */}
          {!isCreating && card && (card.agent_tokens_used || card.agent_model || card.agent_execution_time_seconds || card.agent_started_at || card.agent_completed_at) && (
            <div className="border-t border-[#2a2a3a] pt-4">
              <p className="text-sm font-medium text-purple-400 mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Agent Completion
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                {card.agent_model && (
                  <div>
                    <span className="text-gray-500">Model</span>
                    <p className="text-gray-200 font-mono mt-0.5">{card.agent_model}</p>
                  </div>
                )}
                {card.agent_tokens_used != null && (
                  <div>
                    <span className="text-gray-500">Tokens used</span>
                    <p className="text-gray-200 mt-0.5">{card.agent_tokens_used.toLocaleString()}</p>
                  </div>
                )}
                {card.agent_execution_time_seconds != null && (
                  <div>
                    <span className="text-gray-500">Execution time</span>
                    <p className="text-gray-200 mt-0.5">
                      {card.agent_execution_time_seconds >= 60
                        ? `${(card.agent_execution_time_seconds / 60).toFixed(1)} min`
                        : `${card.agent_execution_time_seconds.toFixed(1)}s`}
                    </p>
                  </div>
                )}
                {card.agent_started_at && (
                  <div>
                    <span className="text-gray-500">Started</span>
                    <p className="text-gray-200 mt-0.5">{new Date(card.agent_started_at).toLocaleString()}</p>
                  </div>
                )}
                {card.agent_completed_at && (
                  <div>
                    <span className="text-gray-500">Completed</span>
                    <p className="text-gray-200 mt-0.5">{new Date(card.agent_completed_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Comments */}
          {!isCreating && card && (
            <div className="border-t border-[#2a2a3a] pt-4">
              <p className="text-sm font-medium text-gray-400 mb-3 flex items-center gap-1.5">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                Comments {comments.length > 0 && <span className="text-gray-600">({comments.length})</span>}
              </p>

              {comments.length > 0 && (
                <div className="space-y-3 mb-3 max-h-48 overflow-y-auto">
                  {comments.map((c) => (
                    <div key={c.id} className="bg-[#1a1a24] rounded-lg px-3 py-2 border border-[#2a2a3a]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-cyan-400">{c.profile}</span>
                        <span className="text-xs text-gray-600">{new Date(c.created_at).toLocaleString()}</span>
                      </div>
                      <p className="text-sm text-gray-200 whitespace-pre-wrap">{c.body}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-2">
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey && newComment.trim()) {
                      e.preventDefault();
                      handleAddComment();
                    }
                  }}
                  placeholder="Add a comment..."
                  className="flex-1 px-3 py-2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg text-gray-100 placeholder-gray-600 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all text-sm"
                />
                <button
                  type="button"
                  disabled={!newComment.trim() || addingComment}
                  onClick={handleAddComment}
                  className="px-3 py-2 min-h-[44px] rounded-lg border border-cyan-500/30 hover:bg-cyan-500/10 text-cyan-400 text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {addingComment ? '...' : 'Add'}
                </button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-4">
            <div>
              {!isCreating && onDelete && (
                <button
                  type="button"
                  onClick={onDelete}
                  className="px-4 py-2.5 min-h-[44px] text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  Delete
                </button>
              )}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2.5 min-h-[44px] text-gray-400 hover:bg-[#2a2a3a] rounded-lg transition-colors"
              >
                Cancel
              </button>
              {canMarkComplete && onMarkComplete && (
                <button
                  type="button"
                  onClick={() => onMarkComplete(card.id, completionColumnId)}
                  className="px-4 py-2.5 min-h-[44px] bg-green-600 hover:bg-green-500 text-white font-semibold rounded-lg hover:shadow-[0_0_20px_rgba(34,197,94,0.4)] transition-all"
                >
                  Complete
                </button>
              )}
              <button
                type="submit"
                disabled={!title.trim()}
                className="px-5 py-2.5 min-h-[44px] bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold rounded-lg hover:shadow-[0_0_20px_rgba(0,245,255,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none"
              >
                {isCreating ? 'Create' : 'Save'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
