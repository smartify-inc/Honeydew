"""Board API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Board as BoardModel, BoardColumn, Card as CardModel
from ..schemas import Board, BoardCreate, BoardUpdate, BoardSimple

router = APIRouter()


@router.get("", response_model=List[BoardSimple])
def list_boards(db: Session = Depends(get_db)):
    """List all boards."""
    boards = db.query(BoardModel).order_by(BoardModel.created_at.desc()).all()
    return boards


@router.post("", response_model=Board, status_code=status.HTTP_201_CREATED)
def create_board(board: BoardCreate, db: Session = Depends(get_db)):
    """Create a new board with optional custom columns."""
    db_board = BoardModel(name=board.name)
    db.add(db_board)
    db.flush()

    column_names = board.columns if board.columns else ["To Do", "In Progress", "Done"]
    for pos, name in enumerate(column_names):
        db.add(BoardColumn(board_id=db_board.id, name=name, position=pos))
    db.commit()
    db.refresh(db_board)

    return db_board


@router.get("/{board_id}", response_model=Board)
def get_board(
    board_id: int,
    profile: Optional[str] = Query(None, description="Filter cards by profile"),
    db: Session = Depends(get_db),
):
    """Get a board with all its columns and cards, optionally filtered by profile."""
    board = (
        db.query(BoardModel)
        .options(joinedload(BoardModel.columns))
        .filter(BoardModel.id == board_id)
        .first()
    )
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board with id {board_id} not found",
        )
    
    # Build the response with filtered cards
    columns_data = []
    for column in sorted(board.columns, key=lambda c: c.position):
        # Query cards for this column, optionally filtered by profile
        cards_query = db.query(CardModel).options(
            joinedload(CardModel.labels),
            joinedload(CardModel.comments),
        ).filter(CardModel.column_id == column.id)
        if profile:
            cards_query = cards_query.filter(CardModel.profile == profile)
        cards = cards_query.order_by(CardModel.position).all()
        
        columns_data.append({
            "id": column.id,
            "board_id": column.board_id,
            "name": column.name,
            "position": column.position,
            "cards": cards,
        })
    
    return {
        "id": board.id,
        "name": board.name,
        "created_at": board.created_at,
        "columns": columns_data,
    }


@router.patch("/{board_id}", response_model=Board)
def update_board(board_id: int, board_update: BoardUpdate, db: Session = Depends(get_db)):
    """Update a board's name."""
    board = db.query(BoardModel).filter(BoardModel.id == board_id).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board with id {board_id} not found",
        )
    
    if board_update.name is not None:
        board.name = board_update.name
    
    db.commit()
    db.refresh(board)
    
    return board


@router.delete("/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_board(board_id: int, db: Session = Depends(get_db)):
    """Delete a board and all its columns and cards."""
    board = db.query(BoardModel).filter(BoardModel.id == board_id).first()
    
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board with id {board_id} not found",
        )
    
    db.delete(board)
    db.commit()
