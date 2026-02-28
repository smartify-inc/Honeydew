"""SQLAlchemy database models for the Kanban board."""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import ForeignKey, String, Text, Integer, Float, Date, DateTime, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Association table for Card-Label many-to-many relationship
card_labels = Table(
    "card_labels",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Board(Base):
    """A Kanban board containing columns."""
    
    __tablename__ = "boards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relationships
    columns: Mapped[List["BoardColumn"]] = relationship(
        "BoardColumn",
        back_populates="board",
        cascade="all, delete-orphan",
        order_by="BoardColumn.position",
    )


class BoardColumn(Base):
    """A column within a board (e.g., To Do, In Progress, Done)."""
    
    __tablename__ = "columns"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    board: Mapped["Board"] = relationship("Board", back_populates="columns")
    cards: Mapped[List["Card"]] = relationship(
        "Card",
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="Card.position",
    )


class Card(Base):
    """A card/task within a column."""
    
    __tablename__ = "cards"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="CASCADE"))
    profile: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=2)  # 1=Low, 2=Medium, 3=High, 4=Urgent
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    
    # Agent completion metadata (populated when an agent reports task completion)
    agent_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    agent_model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    agent_execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    agent_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agent_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    column: Mapped["BoardColumn"] = relationship("BoardColumn", back_populates="cards")
    labels: Mapped[List["Label"]] = relationship(
        "Label",
        secondary=card_labels,
        back_populates="cards",
    )
    comments: Mapped[List["CardComment"]] = relationship(
        "CardComment",
        back_populates="card",
        cascade="all, delete-orphan",
        order_by="CardComment.created_at",
    )


class CardComment(Base):
    """A comment on a card/task."""

    __tablename__ = "card_comments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id", ondelete="CASCADE"))
    profile: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    card: Mapped["Card"] = relationship("Card", back_populates="comments")


class Label(Base):
    """A label that can be applied to cards."""
    
    __tablename__ = "labels"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    color: Mapped[str] = mapped_column(String(7), default="#6366f1")  # Hex color
    
    # Relationships
    cards: Mapped[List["Card"]] = relationship(
        "Card",
        secondary=card_labels,
        back_populates="labels",
    )
