"""Comments API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.core.rate_limit import standard_limit
from app.models.comment import Comment, CommentLike, CommentStatus
from app.models.user import User

router = APIRouter()


# Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    content_type: str = Field(..., pattern="^(institution|review|answer)$")
    content_id: int
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    content: str
    content_type: str
    content_id: int
    parent_id: Optional[int]
    reply_count: int
    like_count: int
    status: str
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


# Endpoints
@router.post("/comments", response_model=CommentResponse)
@standard_limit()
def create_comment(
    request: Request,
    comment: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new comment."""
    # If it's a reply, verify parent exists
    if comment.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        
        # Update parent's reply count
        parent.reply_count += 1
    
    db_comment = Comment(
        user_id=current_user.id,
        content=comment.content,
        content_type=comment.content_type,
        content_id=comment.content_id,
        parent_id=comment.parent_id,
        status=CommentStatus.APPROVED  # Auto-approve
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return _comment_to_response(db_comment)


@router.get("/comments/{content_type}/{content_id}", response_model=List[CommentResponse])
def list_comments(
    content_type: str,
    content_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List comments for a content item."""
    query = db.query(Comment).filter(
        Comment.content_type == content_type,
        Comment.content_id == content_id,
        Comment.status == CommentStatus.APPROVED
    )
    
    # Filter by parent (for threaded replies)
    if parent_id:
        query = query.filter(Comment.parent_id == parent_id)
    else:
        # Only top-level comments
        query = query.filter(Comment.parent_id == None)
    
    query = query.order_by(desc(Comment.created_at))
    
    comments = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return [_comment_to_response(c) for c in comments]


@router.put("/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    comment_id: int,
    comment_update: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update own comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    comment.content = comment_update.content
    db.commit()
    db.refresh(comment)
    
    return _comment_to_response(comment)


@router.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete own comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    # If it's a reply, update parent's count
    if comment.parent_id:
        parent = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if parent:
            parent.reply_count -= 1
    
    comment.status = CommentStatus.REJECTED  # Soft delete
    db.commit()
    
    return {"message": "Comment deleted successfully"}


@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Like a comment."""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if already liked
    existing = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_id == current_user.id
    ).first()
    
    if existing:
        # Unlike
        db.delete(existing)
        comment.like_count -= 1
        db.commit()
        return {"message": "Comment unliked", "like_count": comment.like_count}
    else:
        # Like
        new_like = CommentLike(
            comment_id=comment_id,
            user_id=current_user.id
        )
        db.add(new_like)
        comment.like_count += 1
        db.commit()
        return {"message": "Comment liked", "like_count": comment.like_count}


# Helper function
def _comment_to_response(comment: Comment) -> dict:
    """Convert comment model to response dict."""
    return {
        "id": comment.id,
        "user_id": comment.user_id,
        "user_name": comment.user.full_name if comment.user else "Anonymous",
        "content": comment.content,
        "content_type": comment.content_type,
        "content_id": comment.content_id,
        "parent_id": comment.parent_id,
        "reply_count": comment.reply_count,
        "like_count": comment.like_count,
        "status": comment.status.value,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
        "updated_at": comment.updated_at.isoformat() if comment.updated_at else None
    }
