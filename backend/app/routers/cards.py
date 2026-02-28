"""Card API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from ..config import get_valid_profile_ids, get_default_profile_id
from ..database import get_db
from ..models import Board as BoardModel, Card as CardModel, BoardColumn as ColumnModel, Label as LabelModel, CardComment as CardCommentModel
from ..schemas import Card, CardCreate, CardUpdate, CardMove, CardTransfer, CardMoveToBoard, CardComment, CardCommentCreate

router = APIRouter()


def resolve_column_for_board(
    db: Session,
    board_id: int,
    preferred_column_name: Optional[str] = None,
    card: Optional[CardModel] = None,
) -> ColumnModel:
    """Resolve which column on the target board to use. Prefer explicit name, else card's current column name, else first column."""
    board = db.query(BoardModel).filter(BoardModel.id == board_id).first()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Board with id {board_id} not found")
    columns = sorted(db.query(ColumnModel).filter(ColumnModel.board_id == board_id).all(), key=lambda c: c.position)
    if not columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Board {board_id} has no columns",
        )
    if preferred_column_name:
        name_lower = preferred_column_name.strip().lower()
        for col in columns:
            if col.name.lower() == name_lower:
                return col
    if card:
        current_col = db.query(ColumnModel).filter(ColumnModel.id == card.column_id).first()
        if current_col:
            name_lower = current_col.name.lower()
            for col in columns:
                if col.name.lower() == name_lower:
                    return col
    return columns[0]


@router.get("", response_model=List[Card])
def list_cards(
    board_id: Optional[int] = Query(None, description="Filter by board ID"),
    column_id: Optional[int] = Query(None, description="Filter by column ID"),
    profile: Optional[str] = Query(None, description="Filter by profile"),
    priority: Optional[int] = Query(None, description="Filter by priority (1-4)"),
    has_due_date: Optional[bool] = Query(None, description="Filter cards with/without due date"),
    db: Session = Depends(get_db),
):
    """List cards with optional filters."""
    query = db.query(CardModel).options(joinedload(CardModel.labels), joinedload(CardModel.comments))
    
    if column_id is not None:
        query = query.filter(CardModel.column_id == column_id)
    elif board_id is not None:
        # Get all columns for the board, then filter cards
        column_ids = [
            c.id for c in db.query(ColumnModel).filter(ColumnModel.board_id == board_id).all()
        ]
        query = query.filter(CardModel.column_id.in_(column_ids))
    
    if profile is not None:
        query = query.filter(CardModel.profile == profile)
    
    if priority is not None:
        query = query.filter(CardModel.priority == priority)
    
    if has_due_date is not None:
        if has_due_date:
            query = query.filter(CardModel.due_date.isnot(None))
        else:
            query = query.filter(CardModel.due_date.is_(None))
    
    cards = query.order_by(CardModel.position).all()
    return cards


@router.post("", response_model=Card, status_code=status.HTTP_201_CREATED)
def create_card(card: CardCreate, db: Session = Depends(get_db)):
    """Create a new card in a column."""
    # Verify column exists
    column = db.query(ColumnModel).filter(ColumnModel.id == card.column_id).first()
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with id {card.column_id} not found",
        )
    
    # Calculate position (add to end of column)
    max_position = (
        db.query(CardModel)
        .filter(CardModel.column_id == card.column_id)
        .count()
    )
    
    profile = card.profile or get_default_profile_id()
    valid_profiles = get_valid_profile_ids()
    if profile not in valid_profiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile must be one of: {valid_profiles}",
        )
    db_card = CardModel(
        column_id=card.column_id,
        profile=profile,
        title=card.title,
        description=card.description,
        priority=card.priority,
        due_date=card.due_date,
        position=max_position,
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    
    return db_card


@router.get("/{card_id}", response_model=Card)
def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get a card's details."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels), joinedload(CardModel.comments))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    return card


@router.patch("/{card_id}", response_model=Card)
def update_card(card_id: int, card_update: CardUpdate, db: Session = Depends(get_db)):
    """Update a card's details."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    update_data = card_update.model_dump(exclude_unset=True)
    if "profile" in update_data and update_data["profile"] is not None:
        valid_profiles = get_valid_profile_ids()
        if update_data["profile"] not in valid_profiles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Profile must be one of: {valid_profiles}",
            )
    for field, value in update_data.items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    
    return card


@router.post("/{card_id}/move", response_model=Card)
def move_card(card_id: int, move: CardMove, db: Session = Depends(get_db)):
    """Move a card to a different column and/or position."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    # Verify target column exists
    target_column = db.query(ColumnModel).filter(ColumnModel.id == move.column_id).first()
    if not target_column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with id {move.column_id} not found",
        )
    
    old_column_id = card.column_id
    old_position = card.position
    new_column_id = move.column_id
    new_position = move.position
    
    if old_column_id == new_column_id:
        # Moving within the same column
        if old_position != new_position:
            if new_position > old_position:
                # Moving down: shift cards up
                db.query(CardModel).filter(
                    CardModel.column_id == old_column_id,
                    CardModel.position > old_position,
                    CardModel.position <= new_position,
                ).update({CardModel.position: CardModel.position - 1})
            else:
                # Moving up: shift cards down
                db.query(CardModel).filter(
                    CardModel.column_id == old_column_id,
                    CardModel.position >= new_position,
                    CardModel.position < old_position,
                ).update({CardModel.position: CardModel.position + 1})
            
            card.position = new_position
    else:
        # Moving to a different column
        # Update positions in old column
        db.query(CardModel).filter(
            CardModel.column_id == old_column_id,
            CardModel.position > old_position,
        ).update({CardModel.position: CardModel.position - 1})
        
        # Update positions in new column
        db.query(CardModel).filter(
            CardModel.column_id == new_column_id,
            CardModel.position >= new_position,
        ).update({CardModel.position: CardModel.position + 1})
        
        card.column_id = new_column_id
        card.position = new_position
    
    db.commit()
    db.refresh(card)
    
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, db: Session = Depends(get_db)):
    """Delete a card."""
    card = db.query(CardModel).filter(CardModel.id == card_id).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    column_id = card.column_id
    position = card.position
    
    db.delete(card)
    
    # Reorder remaining cards
    db.query(CardModel).filter(
        CardModel.column_id == column_id,
        CardModel.position > position,
    ).update({CardModel.position: CardModel.position - 1})
    
    db.commit()


@router.post("/{card_id}/move-to-board", response_model=Card)
def move_card_to_board(card_id: int, body: CardMoveToBoard, db: Session = Depends(get_db)):
    """Move a card to another board. Resolves target column by name if provided, else by matching current column name, else first column."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    target_column = resolve_column_for_board(db, body.board_id, body.column_name, card)
    if card.column_id == target_column.id:
        db.commit()
        db.refresh(card)
        return card
    old_column_id = card.column_id
    old_position = card.position
    new_position = (
        db.query(CardModel).filter(CardModel.column_id == target_column.id).count()
    )
    db.query(CardModel).filter(
        CardModel.column_id == old_column_id,
        CardModel.position > old_position,
    ).update({CardModel.position: CardModel.position - 1})
    card.column_id = target_column.id
    card.position = new_position
    db.commit()
    db.refresh(card)
    return card


@router.post("/{card_id}/transfer", response_model=Card)
def transfer_card(card_id: int, transfer: CardTransfer, db: Session = Depends(get_db)):
    """Transfer a card to a different profile."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    valid_profiles = get_valid_profile_ids()
    if transfer.target_profile not in valid_profiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile must be one of: {valid_profiles}",
        )
    
    card.profile = transfer.target_profile
    db.commit()
    db.refresh(card)
    
    return card


@router.post("/{card_id}/labels/{label_id}", response_model=Card)
def add_label_to_card(card_id: int, label_id: int, db: Session = Depends(get_db)):
    """Add a label to a card."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found",
        )
    
    if label not in card.labels:
        card.labels.append(label)
        db.commit()
        db.refresh(card)
    
    return card


@router.delete("/{card_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_label_from_card(card_id: int, label_id: int, db: Session = Depends(get_db)):
    """Remove a label from a card."""
    card = (
        db.query(CardModel)
        .options(joinedload(CardModel.labels))
        .filter(CardModel.id == card_id)
        .first()
    )
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    
    label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found",
        )
    
    if label in card.labels:
        card.labels.remove(label)
        db.commit()


@router.get("/{card_id}/comments", response_model=List[CardComment])
def list_comments(card_id: int, db: Session = Depends(get_db)):
    """List all comments for a card."""
    card = db.query(CardModel).filter(CardModel.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    comments = (
        db.query(CardCommentModel)
        .filter(CardCommentModel.card_id == card_id)
        .order_by(CardCommentModel.created_at)
        .all()
    )
    return comments


@router.post("/{card_id}/comments", response_model=CardComment, status_code=status.HTTP_201_CREATED)
def add_comment(card_id: int, comment: CardCommentCreate, db: Session = Depends(get_db)):
    """Add a comment to a card."""
    card = db.query(CardModel).filter(CardModel.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card with id {card_id} not found",
        )
    profile = comment.profile or get_default_profile_id()
    valid_profiles = get_valid_profile_ids()
    if profile not in valid_profiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile must be one of: {valid_profiles}",
        )
    db_comment = CardCommentModel(
        card_id=card_id,
        profile=profile,
        body=comment.body,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment
