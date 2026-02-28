"""Column API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BoardColumn as ColumnModel, Board as BoardModel
from ..schemas import Column, ColumnCreate, ColumnUpdate, ColumnSimple

router = APIRouter()


@router.post("", response_model=Column, status_code=status.HTTP_201_CREATED)
def create_column(column: ColumnCreate, db: Session = Depends(get_db)):
    """Create a new column in a board."""
    # Verify board exists
    board = db.query(BoardModel).filter(BoardModel.id == column.board_id).first()
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Board with id {column.board_id} not found",
        )
    
    # Calculate position if not provided
    if column.position is None:
        max_position = (
            db.query(ColumnModel)
            .filter(ColumnModel.board_id == column.board_id)
            .count()
        )
        position = max_position
    else:
        position = column.position
    
    db_column = ColumnModel(
        board_id=column.board_id,
        name=column.name,
        position=position,
    )
    db.add(db_column)
    db.commit()
    db.refresh(db_column)
    
    return db_column


@router.get("/{column_id}", response_model=Column)
def get_column(column_id: int, db: Session = Depends(get_db)):
    """Get a column with its cards."""
    column = db.query(ColumnModel).filter(ColumnModel.id == column_id).first()
    
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with id {column_id} not found",
        )
    
    return column


@router.patch("/{column_id}", response_model=ColumnSimple)
def update_column(column_id: int, column_update: ColumnUpdate, db: Session = Depends(get_db)):
    """Update a column's name or position."""
    column = db.query(ColumnModel).filter(ColumnModel.id == column_id).first()
    
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with id {column_id} not found",
        )
    
    if column_update.name is not None:
        column.name = column_update.name
    
    if column_update.position is not None:
        # Reorder other columns
        old_position = column.position
        new_position = column_update.position
        
        if old_position != new_position:
            if new_position > old_position:
                # Moving right: shift columns left
                db.query(ColumnModel).filter(
                    ColumnModel.board_id == column.board_id,
                    ColumnModel.position > old_position,
                    ColumnModel.position <= new_position,
                ).update({ColumnModel.position: ColumnModel.position - 1})
            else:
                # Moving left: shift columns right
                db.query(ColumnModel).filter(
                    ColumnModel.board_id == column.board_id,
                    ColumnModel.position >= new_position,
                    ColumnModel.position < old_position,
                ).update({ColumnModel.position: ColumnModel.position + 1})
            
            column.position = new_position
    
    db.commit()
    db.refresh(column)
    
    return column


@router.delete("/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_column(column_id: int, db: Session = Depends(get_db)):
    """Delete a column and all its cards."""
    column = db.query(ColumnModel).filter(ColumnModel.id == column_id).first()
    
    if not column:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with id {column_id} not found",
        )
    
    board_id = column.board_id
    position = column.position
    
    db.delete(column)
    
    # Reorder remaining columns
    db.query(ColumnModel).filter(
        ColumnModel.board_id == board_id,
        ColumnModel.position > position,
    ).update({ColumnModel.position: ColumnModel.position - 1})
    
    db.commit()
