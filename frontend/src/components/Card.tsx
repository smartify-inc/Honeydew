import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Card as CardType } from '../types';
import { PRIORITY_LABELS } from '../types';

interface CardProps {
  card: CardType;
  onClick: () => void;
}

export function Card({ card, onClick }: CardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: `card-${card.id}` });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    touchAction: 'manipulation' as const,
  };

  const priority = PRIORITY_LABELS[card.priority] || PRIORITY_LABELS[2];

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      className={`
        bg-[#1a1a24] rounded-lg border border-[#2a2a3a] p-3 min-h-[44px] cursor-pointer
        hover:border-cyan-500/50 hover:shadow-[0_0_20px_rgba(0,245,255,0.25),0_0_40px_rgba(0,245,255,0.1)]
        transition-all duration-200
        ${isDragging ? 'opacity-0 pointer-events-none' : ''}
      `}
    >
      {/* Labels */}
      {card.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {card.labels.map((label) => (
            <span
              key={label.id}
              className="px-2 py-0.5 text-xs font-medium rounded-full text-white shadow-sm"
              style={{ 
                backgroundColor: label.color,
                boxShadow: `0 0 8px ${label.color}40`
              }}
            >
              {label.name}
            </span>
          ))}
        </div>
      )}

      {/* Title */}
      <h4 className="text-sm font-medium text-gray-100 mb-1">{card.title}</h4>

      {/* Description preview */}
      {card.description && (
        <p className="text-xs text-gray-500 line-clamp-2 mb-2">
          {card.description}
        </p>
      )}

      {/* Footer with priority and due date */}
      <div className="flex items-center justify-between mt-2">
        <span className={`text-xs px-2 py-0.5 rounded-full ${priority.color}`}>
          {priority.label}
        </span>
        {card.due_date && (
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            {new Date(card.due_date).toLocaleDateString()}
          </span>
        )}
      </div>
    </div>
  );
}
