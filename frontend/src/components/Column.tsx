import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import type { Column as ColumnType, Card as CardType } from '../types';
import { Card } from './Card';

interface ColumnProps {
  column: ColumnType;
  isDropTarget?: boolean;
  onCardClick: (card: CardType) => void;
  onAddCard: () => void;
}

export function Column({ column, isDropTarget = false, onCardClick, onAddCard }: ColumnProps) {
  const { setNodeRef } = useDroppable({
    id: `column-${column.id}`,
  });

  const cardIds = column.cards.map((card) => `card-${card.id}`);

  // Column-specific accent colors
  const columnAccents: Record<string, { border: string; glow: string; badge: string }> = {
    'To Do': { 
      border: 'border-cyan-500/30', 
      glow: 'shadow-[0_0_15px_rgba(0,245,255,0.15)]',
      badge: 'bg-cyan-500/20 text-cyan-400'
    },
    'In Progress': { 
      border: 'border-purple-500/30', 
      glow: 'shadow-[0_0_15px_rgba(168,85,247,0.15)]',
      badge: 'bg-purple-500/20 text-purple-400'
    },
    'Blocked': { 
      border: 'border-red-500/30', 
      glow: 'shadow-[0_0_15px_rgba(239,68,68,0.15)]',
      badge: 'bg-red-500/20 text-red-400'
    },
    'Done': { 
      border: 'border-green-500/30', 
      glow: 'shadow-[0_0_15px_rgba(34,197,94,0.15)]',
      badge: 'bg-green-500/20 text-green-400'
    },
  };

  const accent = columnAccents[column.name] || columnAccents['To Do'];

  return (
    <div
      className={`
        flex flex-col bg-[#12121a]/60 backdrop-blur-sm rounded-xl w-full md:w-80 md:min-w-80 h-fit self-start
        border ${accent.border} ${accent.glow}
        ${isDropTarget ? 'ring-2 ring-cyan-400/50 bg-cyan-500/5' : ''}
        transition-all duration-200
      `}
    >
      {/* Column header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#2a2a3a]">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-gray-200">{column.name}</h3>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${accent.badge} transition-all duration-300`}>
            {column.cards.length}
          </span>
        </div>
        <button
          onClick={onAddCard}
          className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center hover:bg-[#2a2a3a] rounded-lg transition-colors group"
          title="Add card"
        >
          <svg
            className="w-5 h-5 text-gray-500 group-hover:text-cyan-400 transition-colors"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </button>
      </div>

      {/* Cards container with auto-animate */}
      <div
        ref={setNodeRef}
        className="p-2 space-y-2 min-h-16"
      >
        <SortableContext items={cardIds} strategy={verticalListSortingStrategy}>
          {column.cards.map((card) => (
            <Card
              key={card.id}
              card={card}
              onClick={() => onCardClick(card)}
            />
          ))}
        </SortableContext>

        {column.cards.length === 0 && (
          <div className="text-center text-gray-600 text-sm py-8 border-2 border-dashed border-[#2a2a3a] rounded-lg">
            Drop cards here
          </div>
        )}
      </div>
    </div>
  );
}
