"""Label API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Label as LabelModel
from ..schemas import Label, LabelCreate, LabelUpdate

router = APIRouter()


@router.get("", response_model=List[Label])
def list_labels(db: Session = Depends(get_db)):
    """List all labels."""
    labels = db.query(LabelModel).order_by(LabelModel.name).all()
    return labels


@router.post("", response_model=Label, status_code=status.HTTP_201_CREATED)
def create_label(label: LabelCreate, db: Session = Depends(get_db)):
    """Create a new label."""
    db_label = LabelModel(
        name=label.name,
        color=label.color,
    )
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    
    return db_label


@router.get("/{label_id}", response_model=Label)
def get_label(label_id: int, db: Session = Depends(get_db)):
    """Get a label's details."""
    label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found",
        )
    
    return label


@router.patch("/{label_id}", response_model=Label)
def update_label(label_id: int, label_update: LabelUpdate, db: Session = Depends(get_db)):
    """Update a label."""
    label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found",
        )
    
    if label_update.name is not None:
        label.name = label_update.name
    if label_update.color is not None:
        label.color = label_update.color
    
    db.commit()
    db.refresh(label)
    
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_label(label_id: int, db: Session = Depends(get_db)):
    """Delete a label."""
    label = db.query(LabelModel).filter(LabelModel.id == label_id).first()
    
    if not label:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with id {label_id} not found",
        )
    
    db.delete(label)
    db.commit()
