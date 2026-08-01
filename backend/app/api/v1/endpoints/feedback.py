"""
User Feedback API Endpoints
Handles feedback collection, management, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.feedback import (
    Feedback,
    FeedbackComment,
    FeedbackVote,
    FeedbackTemplate,
    FeedbackAnalytic,
    FeedbackType,
    FeedbackStatus,
    FeedbackRating,
)
from app.models.user import User
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackCommentCreate,
    FeedbackCommentResponse,
    FeedbackAnalyticsResponse,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def create_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create new feedback/bug report/feature request
    
    Args:
        feedback: Feedback details
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created feedback object
    """
    new_feedback = Feedback(
        id=str(uuid4()),
        user_id=current_user.id,
        type=feedback.type,
        title=feedback.title,
        description=feedback.description,
        rating=feedback.rating,
        section=feedback.section,
        page_url=feedback.page_url,
        user_agent=feedback.user_agent,
        metadata=feedback.metadata,
        is_public=feedback.is_public,
    )
    
    db.add(new_feedback)
    
    # Send notification to team
    from app.core.notifications import NotificationService
    notification_service = NotificationService(db)
    await notification_service.notify_new_feedback(new_feedback)
    
    db.commit()
    db.refresh(new_feedback)
    
    return new_feedback


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    type: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    List feedback items (user's own or public feedback if admin)
    
    Args:
        current_user: Current authenticated user
        skip: Number of results to skip
        limit: Number of results to return
        type: Filter by feedback type
        status: Filter by status
        db: Database session
        
    Returns:
        List of feedback items
    """
    query = db.query(Feedback)
    
    # Regular users only see their own feedback or public feedback
    if not current_user.is_admin:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Feedback.user_id == current_user.id,
                Feedback.is_public == True,
            )
        )
    
    # Apply filters
    if type:
        query = query.filter(Feedback.type == type)
    if status:
        query = query.filter(Feedback.status == status)
    
    total = query.count()
    items = query.order_by(Feedback.created_at.desc()).offset(skip).limit(limit).all()
    
    return FeedbackListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get specific feedback item
    
    Args:
        feedback_id: ID of feedback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Feedback object
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Check access (user's own feedback or public or admin)
    if (feedback.user_id != current_user.id and 
        not feedback.is_public and 
        not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return feedback


@router.post("/{feedback_id}/comments", response_model=FeedbackCommentResponse)
async def add_comment(
    feedback_id: str,
    comment: FeedbackCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add comment to feedback item
    
    Args:
        feedback_id: ID of feedback
        comment: Comment text
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created comment object
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    new_comment = FeedbackComment(
        id=str(uuid4()),
        feedback_id=feedback_id,
        user_id=current_user.id,
        comment=comment.comment,
        is_internal=comment.is_internal and current_user.is_admin,  # Only admins can make internal
    )
    
    db.add(new_comment)
    feedback.comment_count += 1
    
    db.commit()
    db.refresh(new_comment)
    
    return new_comment


@router.get("/{feedback_id}/comments")
async def get_feedback_comments(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get comments on feedback item
    
    Args:
        feedback_id: ID of feedback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of comments
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Check access
    if (feedback.user_id != current_user.id and 
        not feedback.is_public and 
        not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get comments (hide internal if not admin/owner)
    query = db.query(FeedbackComment).filter(FeedbackComment.feedback_id == feedback_id)
    
    if not current_user.is_admin:
        query = query.filter(FeedbackComment.is_internal == False)
    
    comments = query.order_by(FeedbackComment.created_at.asc()).all()
    
    return [comment.to_dict() for comment in comments]


@router.post("/{feedback_id}/upvote")
async def upvote_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upvote a feedback item
    
    Args:
        feedback_id: ID of feedback
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated upvote count
    """
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Check if already voted
    existing_vote = db.query(FeedbackVote).filter(
        FeedbackVote.feedback_id == feedback_id,
        FeedbackVote.user_id == current_user.id,
    ).first()
    
    if existing_vote and existing_vote.vote_type == "upvote":
        raise HTTPException(status_code=400, detail="Already upvoted")
    
    # Remove downvote if exists
    if existing_vote and existing_vote.vote_type == "downvote":
        db.delete(existing_vote)
        feedback.upvote_count += 1  # Net +2 (remove -1, add +1)
    else:
        feedback.upvote_count += 1
    
    # Create new vote
    new_vote = FeedbackVote(
        id=str(uuid4()),
        feedback_id=feedback_id,
        user_id=current_user.id,
        vote_type="upvote",
    )
    
    db.add(new_vote)
    db.commit()
    
    return {"upvote_count": feedback.upvote_count}


@router.get("/analytics/summary")
async def get_feedback_analytics(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get feedback analytics and insights
    Requires admin access
    
    Args:
        days: Number of days to include
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Analytics summary
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    start_date = (datetime.utcnow() - timedelta(days=days)).date()
    
    analytics = db.query(FeedbackAnalytic).filter(
        FeedbackAnalytic.date >= start_date.isoformat()
    ).order_by(FeedbackAnalytic.date.desc()).all()
    
    # Calculate aggregates
    total_feedback = sum(a.total_feedback for a in analytics)
    avg_rating = sum(a.avg_rating for a in analytics) // len(analytics) if analytics else 0
    avg_response_rate = sum(a.response_rate for a in analytics) // len(analytics) if analytics else 0
    
    return {
        "period_days": days,
        "total_feedback": total_feedback,
        "average_rating": avg_rating / 100 if avg_rating else None,
        "average_response_rate": avg_response_rate,
        "daily_analytics": [a.to_dict() for a in analytics],
    }


@router.patch("/{feedback_id}/status", dependencies=[Depends(get_current_user)])
async def update_feedback_status(
    feedback_id: str,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update feedback status (admin only)
    
    Args:
        feedback_id: ID of feedback
        new_status: New status value
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated feedback object
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # Validate status
    try:
        status_enum = FeedbackStatus[new_status.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    feedback.status = status_enum
    
    if status_enum in [FeedbackStatus.COMPLETED, FeedbackStatus.WONT_FIX, FeedbackStatus.CLOSED]:
        feedback.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(feedback)
    
    return feedback


@router.get("/templates/all")
async def get_feedback_templates(
    db: Session = Depends(get_db),
):
    """
    Get all feedback templates
    
    Args:
        db: Database session
        
    Returns:
        List of templates
    """
    templates = db.query(FeedbackTemplate).filter(
        FeedbackTemplate.enabled == True
    ).all()
    
    return [t.to_dict() for t in templates]
