import { useState, useEffect, useCallback, useRef } from 'react';
import honeydewLogoOnly from '../assets/honeydew-logo-only.png';
import honeydewTextOnly from '../assets/honeydew-text-only.png';
import flipIcon from '../assets/flip-icon.png';
import agentIcon from '../assets/agent-icon.png';
import {
  DndContext,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core';
import type { DragEndEvent, DragOverEvent, DragStartEvent } from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import type { Board as BoardType, Card as CardType, Column as ColumnType, CardUpdate } from '../types';
import { useConfig } from '../configContext';
import { boardsApi, cardsApi } from '../api/client';
import { Column } from './Column';
import { Card } from './Card';
import { CardModal } from './CardModal';

const POLL_INTERVAL = 5000;

const BOARD_GRADIENTS = [
  { bg: 'from-cyan-500 to-purple-500', shadow: 'rgba(0,245,255,0.3)' },
  { bg: 'from-violet-500 to-fuchsia-500', shadow: 'rgba(139,92,246,0.3)' },
  { bg: 'from-teal-400 to-blue-500', shadow: 'rgba(45,212,191,0.3)' },
  { bg: 'from-blue-500 to-indigo-500', shadow: 'rgba(59,130,246,0.3)' },
  { bg: 'from-emerald-400 to-cyan-500', shadow: 'rgba(52,211,153,0.3)' },
  { bg: 'from-sky-400 to-violet-500', shadow: 'rgba(56,189,248,0.3)' },
  { bg: 'from-purple-500 to-pink-500', shadow: 'rgba(168,85,247,0.3)' },
  { bg: 'from-indigo-400 to-cyan-400', shadow: 'rgba(129,140,248,0.3)' },
];

function getBoardGradient(boardId: number) {
  return BOARD_GRADIENTS[boardId % BOARD_GRADIENTS.length];
}

interface BoardListItem {
  id: number;
  name: string;
}

export function Board() {
  const { config, profiles, profileIds } = useConfig();
  const [currentProfile, setCurrentProfile] = useState(config.user.profile_id);
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const [boardList, setBoardList] = useState<BoardListItem[]>([]);
  const [currentBoardId, setCurrentBoardId] = useState<number | null>(null);
  const [board, setBoard] = useState<BoardType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCard, setActiveCard] = useState<CardType | null>(null);
  const [showBoardMenu, setShowBoardMenu] = useState(false);
  const [swapAnimating, setSwapAnimating] = useState(false);
  const [isPolling, setIsPolling] = useState(true);

  const lastBoardHash = useRef<string>('');
  const pollInProgressRef = useRef(false);

  const [overColumnId, setOverColumnId] = useState<number | null>(null);
  const [modalCard, setModalCard] = useState<CardType | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [createColumnId, setCreateColumnId] = useState<number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(TouchSensor, {
      activationConstraint: {
        delay: 200,
        tolerance: 5,
      },
    })
  );

  const getBoardHash = useCallback((boardData: BoardType): string => {
    return boardData.columns.map(col => 
      `${col.id}:${col.cards.map(c => `${c.id}-${c.column_id}-${c.position}-${c.updated_at}`).join(',')}`
    ).join('|');
  }, []);

  const fetchBoard = useCallback(async (isBackgroundPoll = false) => {
    if (currentBoardId == null) return;
    if (isBackgroundPoll && pollInProgressRef.current) return;
    if (isBackgroundPoll) pollInProgressRef.current = true;
    try {
      if (!isBackgroundPoll) {
        setLoading(true);
      }
      const data = await boardsApi.get(currentBoardId);

      const newHash = getBoardHash(data);
      if (newHash !== lastBoardHash.current) {
        lastBoardHash.current = newHash;
        setBoard(data);
      }

      setError(null);
    } catch (err) {
      if (!isBackgroundPoll) {
        setError(err instanceof Error ? err.message : 'Failed to load board');
      }
    } finally {
      if (!isBackgroundPoll) {
        setLoading(false);
      }
      if (isBackgroundPoll) pollInProgressRef.current = false;
    }
  }, [currentBoardId, getBoardHash]);

  useEffect(() => {
    boardsApi.list().then((list) => {
      setBoardList(list);
      if (list.length > 0) {
        setCurrentBoardId((prev) => (prev === null ? list[0].id : prev));
      } else {
        setLoading(false);
      }
    }).catch(() => {
      setError('Failed to load boards');
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (currentBoardId == null) return;
    lastBoardHash.current = '';
    fetchBoard();
  }, [currentBoardId, fetchBoard]);

  useEffect(() => {
    if (!isPolling) return;

    const interval = setInterval(() => {
      fetchBoard(true);
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [fetchBoard, isPolling]);

  const findCardAndColumn = (cardId: number): { card: CardType; column: ColumnType } | null => {
    if (!board) return null;
    for (const column of board.columns) {
      const card = column.cards.find((c) => c.id === cardId);
      if (card) return { card, column };
    }
    return null;
  };

  const handleDragStart = (event: DragStartEvent) => {
    const cardId = Number(String(event.active.id).replace('card-', ''));
    const found = findCardAndColumn(cardId);
    if (found) {
      setActiveCard(found.card);
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { over } = event;
    if (!over || !board) {
      setOverColumnId(null);
      return;
    }

    const overId = String(over.id);
    let targetColumnId: number | null = null;
    if (overId.startsWith('column-')) {
      targetColumnId = Number(overId.replace('column-', ''));
    } else if (overId.startsWith('card-')) {
      const overCardId = Number(overId.replace('card-', ''));
      const found = findCardAndColumn(overCardId);
      if (found) targetColumnId = found.column.id;
    }
    setOverColumnId(targetColumnId);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCard(null);
    setOverColumnId(null);

    if (!over || !board) return;

    const activeId = Number(String(active.id).replace('card-', ''));
    const overId = String(over.id);

    let targetColumnId: number;
    let targetPosition: number;

    if (overId.startsWith('column-')) {
      targetColumnId = Number(overId.replace('column-', ''));
      const targetColumn = board.columns.find((c) => c.id === targetColumnId);
      targetPosition = targetColumn?.cards.filter((c) => c.id !== activeId).length || 0;
    } else if (overId.startsWith('card-')) {
      const overCardId = Number(overId.replace('card-', ''));
      const found = findCardAndColumn(overCardId);
      if (!found) return;
      targetColumnId = found.column.id;
      const targetColumn = board.columns.find((c) => c.id === targetColumnId);
      if (!targetColumn) return;
      const overIndex = targetColumn.cards.findIndex((c) => c.id === overCardId);
      targetPosition = overIndex;
    } else {
      return;
    }

    const activeFound = findCardAndColumn(activeId);
    if (!activeFound) return;

    const sameColumn = activeFound.column.id === targetColumnId;

    setBoard((prev) => {
      if (!prev) return prev;
      const newColumns = prev.columns.map((col) => {
        if (sameColumn && col.id === targetColumnId) {
          const cards = [...col.cards];
          const activeIndex = cards.findIndex((c) => c.id === activeId);
          if (activeIndex !== -1) {
            const reordered = arrayMove(cards, activeIndex, targetPosition);
            return { ...col, cards: reordered.map((c, i) => ({ ...c, position: i })) };
          }
        }
        if (!sameColumn && col.id === activeFound.column.id) {
          return { ...col, cards: col.cards.filter((c) => c.id !== activeId) };
        }
        if (!sameColumn && col.id === targetColumnId) {
          const movedCard = { ...activeFound.card, column_id: targetColumnId, position: targetPosition };
          const cards = [...col.cards];
          cards.splice(targetPosition, 0, movedCard);
          return { ...col, cards: cards.map((c, i) => ({ ...c, position: i })) };
        }
        return col;
      });
      return { ...prev, columns: newColumns };
    });

    try {
      await cardsApi.move(activeId, {
        column_id: targetColumnId,
        position: targetPosition,
      });
    } catch (err) {
      console.error('Failed to move card:', err);
      fetchBoard();
    }
  };

  const handleCardClick = (card: CardType) => {
    setModalCard(card);
    setIsCreating(false);
    setCreateColumnId(null);
  };

  const handleAddCard = (columnId: number) => {
    setModalCard(null);
    setIsCreating(true);
    setCreateColumnId(columnId);
  };

  const handleCloseModal = () => {
    setModalCard(null);
    setIsCreating(false);
    setCreateColumnId(null);
  };

  const handleSaveCard = async (data: CardUpdate & { column_id?: number; title?: string }) => {
    try {
      if (isCreating && createColumnId && data.title) {
        await cardsApi.create({
          column_id: createColumnId,
          title: data.title,
          description: data.description,
          priority: data.priority,
          due_date: data.due_date,
          profile: currentProfile,
        });
      } else if (modalCard) {
        await cardsApi.update(modalCard.id, data);
      }
      handleCloseModal();
      fetchBoard();
    } catch (err) {
      console.error('Failed to save card:', err);
    }
  };

  const handleMoveToBoard = async (targetBoardId: number) => {
    if (!modalCard) return;
    try {
      await cardsApi.moveToBoard(modalCard.id, targetBoardId);
      handleCloseModal();
      fetchBoard();
    } catch (err) {
      console.error('Failed to move card to board:', err);
    }
  };

  const handleMarkComplete = async (cardId: number, completionColumnId: number) => {
    try {
      await cardsApi.move(cardId, { column_id: completionColumnId, position: 0 });
      handleCloseModal();
      fetchBoard();
    } catch (err) {
      console.error('Failed to mark card complete:', err);
    }
  };

  const handleDeleteCard = async () => {
    if (!modalCard) return;
    try {
      await cardsApi.delete(modalCard.id);
      handleCloseModal();
      fetchBoard();
    } catch (err) {
      console.error('Failed to delete card:', err);
    }
  };

  const currentBoardName = boardList.find(b => b.id === currentBoardId)?.name ?? 'Board';
  const currentGradient = getBoardGradient(currentBoardId ?? 0);

  const handleBoardSwap = () => {
    setSwapAnimating(true);
    if (boardList.length === 2) {
      const other = boardList.find(b => b.id !== currentBoardId);
      if (other) setCurrentBoardId(other.id);
    } else if (boardList.length > 2) {
      setShowBoardMenu(prev => !prev);
    }
  };

  if (boardList.length === 0 && !error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-cyan-400 border-t-transparent neon-border"></div>
      </div>
    );
  }

  if (boardList.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <div className="text-gray-400">No boards found. Add boards in config.json and restart the backend.</div>
      </div>
    );
  }

  if (loading && !board) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-cyan-400 border-t-transparent neon-border"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <div className="text-red-400 text-lg">{error}</div>
        <button
          onClick={() => fetchBoard()}
          className="px-4 py-2 bg-cyan-500 text-black font-semibold rounded-lg hover:bg-cyan-400 transition-all hover:shadow-[0_0_20px_rgba(0,245,255,0.5)]"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!board) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-[#12121a]/80 backdrop-blur-sm border-b border-[#2a2a3a] px-3 py-1 md:px-6 relative z-50">
        <div className="flex items-center">
          {/* Left — logo + wordmark */}
          <div className="flex items-center gap-2 md:gap-3 min-w-0 shrink-0">
            <img src={honeydewLogoOnly} alt="HoneyDew" className="h-10 w-10 md:h-[86px] md:w-[86px] object-contain shrink-0" />
            <div className="flex items-center gap-1.5 md:block">
              <img src={honeydewTextOnly} alt="HoneyDew" className="h-4 md:h-7 w-auto object-contain" />
              <p className="text-[9px] md:text-xs font-bold tracking-widest md:mt-1 bg-gradient-to-r from-green-400 to-orange-400 bg-clip-text text-transparent drop-shadow-[0_0_6px_rgba(74,222,128,0.5)]">by Smartify Inc.</p>
            </div>
          </div>

          {/* Center — board title + swap button */}
          <div className="flex-1 flex justify-center items-center gap-2 min-w-0">
            {boardList.length > 1 ? (
              <button
                onClick={handleBoardSwap}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-br ${currentGradient.bg} hover:scale-105 transition-transform cursor-pointer ${swapAnimating ? 'animate-glow-burst' : ''}`}
                style={{ boxShadow: `0 0 20px ${currentGradient.shadow}` }}
                title={boardList.length === 2 ? 'Switch board' : 'Choose board'}
              >
                <span className="font-bold text-black text-sm md:text-base truncate">{currentBoardName}</span>
                <img
                  src={flipIcon}
                  alt="Switch board"
                  className={`w-7 h-7 ${swapAnimating ? 'animate-board-flip' : ''}`}
                  onAnimationEnd={() => setSwapAnimating(false)}
                />
              </button>
            ) : (
              <span className="font-semibold text-gray-100 text-sm md:text-base truncate">{currentBoardName}</span>
            )}
          </div>

          {/* Right — live indicator + profile selector */}
          <div className="flex items-center gap-2 md:gap-3 shrink-0">
            <div className="flex items-center gap-1.5 md:gap-2 text-xs text-gray-500">
              <div className={`w-2 h-2 rounded-full ${isPolling ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
              <span className="hidden md:inline">Live</span>
              <button
                onClick={() => setIsPolling(!isPolling)}
                className="text-gray-400 hover:text-gray-200 transition-colors p-1"
                title={isPolling ? 'Pause live updates' : 'Resume live updates'}
              >
                {isPolling ? '⏸' : '▶'}
              </button>
            </div>

            {profileIds.length > 1 && (
              <div className="relative">
                <button
                  onClick={() => setShowProfileMenu(prev => !prev)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-gradient-to-br ${profiles[currentProfile]?.color ?? 'from-cyan-400 to-purple-500'} hover:scale-105 transition-transform cursor-pointer`}
                  title={`Viewing as ${profiles[currentProfile]?.name ?? currentProfile}`}
                >
                  {profiles[currentProfile]?.role === 'agent' ? (
                    <img src={agentIcon} alt="Agent" className="w-7 h-7 object-contain" />
                  ) : (
                    <span className="w-5 h-5 rounded-full bg-black/20 flex items-center justify-center text-[10px] font-bold text-white">
                      {profiles[currentProfile]?.icon ?? '?'}
                    </span>
                  )}
                  <span className="hidden md:inline text-xs font-semibold text-white">{profiles[currentProfile]?.name ?? currentProfile}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Board */}
      <div className="flex-1 overflow-x-auto p-3 md:p-6">
        <DndContext
          sensors={sensors}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
          onDragCancel={() => { setActiveCard(null); setOverColumnId(null); }}
        >
          <div className="flex flex-col md:flex-row md:flex-wrap gap-4 md:items-start">
            {board.columns.map((column) => (
              <Column
                key={column.id}
                column={column}
                isDropTarget={overColumnId === column.id}
                onCardClick={handleCardClick}
                onAddCard={() => handleAddCard(column.id)}
              />
            ))}
          </div>

          <DragOverlay>
            {activeCard && (
              <Card card={activeCard} onClick={() => {}} />
            )}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Card Modal */}
      {(modalCard || isCreating) && (
        <CardModal
          card={modalCard}
          isCreating={isCreating}
          columnId={createColumnId}
          currentProfile={currentProfile}
          currentBoardId={currentBoardId ?? undefined}
          boardList={boardList}
          columns={board?.columns.map(c => ({ id: c.id, name: c.name })) ?? []}
          onClose={handleCloseModal}
          onSave={handleSaveCard}
          onDelete={modalCard ? handleDeleteCard : undefined}
          onMoveToBoard={modalCard ? handleMoveToBoard : undefined}
          onMarkComplete={modalCard ? handleMarkComplete : undefined}
        />
      )}
      
      {/* Profile Dropdown Portal */}
      {showProfileMenu && profileIds.length > 1 && (
        <>
          <div
            className="fixed inset-0 z-[9998]"
            onClick={() => setShowProfileMenu(false)}
          />
          <div
            className="fixed top-14 right-4 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg shadow-2xl z-[9999] overflow-hidden min-w-[160px]"
          >
            {profileIds.map((pid) => (
              <button
                key={pid}
                onClick={() => {
                  setCurrentProfile(pid);
                  setShowProfileMenu(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 min-h-[48px] hover:bg-[#2a2a3a] transition-colors cursor-pointer ${
                  currentProfile === pid ? 'bg-[#2a2a3a]' : ''
                }`}
              >
                {profiles[pid]?.role === 'agent' ? (
                  <img src={agentIcon} alt="Agent" className="w-6 h-6 object-contain" />
                ) : (
                  <span className={`w-6 h-6 rounded-full bg-gradient-to-br ${profiles[pid]?.color ?? 'from-cyan-400 to-purple-500'} flex items-center justify-center text-xs font-bold text-white`}>
                    {profiles[pid]?.icon ?? '?'}
                  </span>
                )}
                <span className="text-gray-200 text-sm">{profiles[pid]?.name ?? pid}</span>
                {currentProfile === pid && (
                  <svg className="w-4 h-4 text-cyan-400 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}

      {/* Board Dropdown Portal (3+ boards) */}
      {showBoardMenu && boardList.length > 2 && (
        <>
          <div
            className="fixed inset-0 z-[9998]"
            onClick={() => setShowBoardMenu(false)}
          />
          <div
            className="fixed top-14 left-1/2 -translate-x-1/2 bg-[#1a1a24] border border-[#2a2a3a] rounded-lg shadow-2xl z-[9999] overflow-hidden min-w-[200px]"
          >
            {boardList.map((b) => (
              <button
                key={b.id}
                onClick={() => {
                  setCurrentBoardId(b.id);
                  setShowBoardMenu(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 min-h-[48px] hover:bg-[#2a2a3a] transition-colors cursor-pointer ${
                  currentBoardId === b.id ? 'bg-[#2a2a3a]' : ''
                }`}
              >
                <span className="text-gray-200">{b.name}</span>
                {currentBoardId === b.id && (
                  <svg className="w-4 h-4 text-cyan-400 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}

    </div>
  );
}
