"""Pydantic schemas for request/response validation."""

import re
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validate_hex_color(v: str) -> str:
    if not HEX_COLOR_RE.match(v):
        raise ValueError("color must be a 7-character hex string like #ff00aa")
    return v.lower()


# ============ Label Schemas ============

class LabelBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(default="#6366f1", max_length=7)

    @field_validator("color")
    @classmethod
    def color_is_hex(cls, v: str) -> str:
        return _validate_hex_color(v)


class LabelCreate(LabelBase):
    pass


class LabelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=7)

    @field_validator("color")
    @classmethod
    def color_is_hex(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_hex_color(v)


class Label(LabelBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


# ============ Card Schemas ============

class CardBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: int = Field(default=2, ge=1, le=4)
    due_date: Optional[date] = None


class CardCreate(CardBase):
    column_id: int
    profile: Optional[str] = Field(default=None, max_length=50)


class CardUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[int] = Field(default=None, ge=1, le=4)
    due_date: Optional[date] = None
    profile: Optional[str] = Field(default=None, max_length=50)
    agent_tokens_used: Optional[int] = None
    agent_model: Optional[str] = Field(default=None, max_length=120)
    agent_execution_time_seconds: Optional[float] = None
    agent_started_at: Optional[datetime] = None
    agent_completed_at: Optional[datetime] = None


class CardCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    profile: Optional[str] = Field(default=None, max_length=50)


class CardComment(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    profile: str
    body: str
    created_at: datetime


class CardMove(BaseModel):
    column_id: int
    position: int = Field(default=0, ge=0)


class CardTransfer(BaseModel):
    target_profile: str = Field(min_length=1, max_length=50)


class CardMoveToBoard(BaseModel):
    board_id: int
    column_name: Optional[str] = Field(default=None, max_length=255)


class Card(CardBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    column_id: int
    profile: str
    position: int
    created_at: datetime
    updated_at: datetime
    labels: List[Label] = []
    comments: List[CardComment] = []
    agent_tokens_used: Optional[int] = None
    agent_model: Optional[str] = None
    agent_execution_time_seconds: Optional[float] = None
    agent_started_at: Optional[datetime] = None
    agent_completed_at: Optional[datetime] = None


# ============ Column Schemas ============

class ColumnBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class ColumnCreate(ColumnBase):
    board_id: int
    position: Optional[int] = Field(default=None, ge=0)


class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    position: Optional[int] = Field(default=None, ge=0)


class Column(ColumnBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    board_id: int
    position: int
    cards: List[Card] = []


class ColumnSimple(ColumnBase):
    """Column without nested cards."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    board_id: int
    position: int


# ============ Board Schemas ============

class BoardBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class BoardCreate(BoardBase):
    columns: Optional[List[str]] = None


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class Board(BoardBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    columns: List[Column] = []


class BoardSimple(BoardBase):
    """Board without nested columns."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
