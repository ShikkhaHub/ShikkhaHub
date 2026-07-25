"""Review and rating API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.core.rate_limit import standard_limit
from app.models.review import InstitutionReview, ReviewHelpfulVote, ReviewReport, ReviewStatus
from app.models.institution import Institution
from app.models.user import User

router = APIRouter()


# Schemas
class ReviewCreate(BaseModel):
    institution_id: int
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    academics_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    facilities_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    faculty_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    campus_life_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    value_for_money_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=10, max_length=5000)
    pros: Optional[List[str]] = []
    cons: Optional[List[str]] = []
    study_program: Optional[str] = None
    graduation_year: Optional[int] = None
    is_alumni: bool = False


class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=1.0, le=5.0)


class ReviewResponse(BaseModel):
    id: int
    institution_id: int
    user_id: int
    user_name: str
    overall_rating: float
    academics_rating: Optional[float]
    facilities_rating: Optional[float]
    faculty_rating: Optional[float]
    campus_life_rating: Optional[float]
    value_for_money_rating: Optional[float]
    title: Optional[str]
    content: str
    pros: List[str]
    cons: List[str]
    study_program: Optional[str]
    graduation_year: Optional[int]
    is_alumni: bool
    helpful_count: int
    unhelpful_count: int
    status: str
    is_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    pages: int
    average_rating: Optional[float]


class HelpfulVoteCreate(BaseModel):
    is_helpful: bool


class ReportCreate(BaseModel):
    reason: str  # spam, inappropriate, fake, offensive, other
    description: Optional[str] = None


# Endpoints
@router.post("/reviews", response_model=ReviewResponse)
@standard_limit()
def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new review for an institution."""
    # Check institution exists
    institution = db.query(Institution).filter(Institution.id == review.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Check if user already reviewed this institution
    existing = db.query(InstitutionReview).filter(
        InstitutionReview.institution_id == review.institution_id,
        InstitutionReview.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this institution")
    
    # Create review
    db_review = InstitutionReview(
        institution_id=review.institution_id,
        user_id=current_user.id,
        overall_rating=review.overall_rating,
        academics_rating=review.academics_rating,
        facilities_rating=review.facilities_rating,
        faculty_rating=review.faculty_rating,
        campus_life_rating=review.campus_life_rating,
        value_for_money_rating=review.value_for_money_rating,
        title=review.title,
        content=review.content,
        pros=review.pros or [],
        cons=review.cons or [],
        study_program=review.study_program,
        graduation_year=review.graduation_year,
        is_alumni=review.is_alumni,
        status=ReviewStatus.PENDING  # Needs approval
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update institution rating (could be done async in production)
    update_institution_rating(db, review.institution_id)
    
    return _review_to_response(db_review)


@router.get("/institutions/{institution_id}/reviews", response_model=ReviewListResponse)
def list_reviews(
    institution_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    sort_by: str = Query("newest", enum=["newest", "highest", "lowest", "helpful"]),
    include_pending: bool = Query(False),  # Only admins can see pending
    db: Session = Depends(get_db)
):
    """Get reviews for an institution."""
    # Base query
    query = db.query(InstitutionReview).filter(
        InstitutionReview.institution_id == institution_id
    )
    
    # Filter by status (default only approved)
    if not include_pending:
        query = query.filter(InstitutionReview.status == ReviewStatus.APPROVED)
    
    # Sorting
    if sort_by == "newest":
        query = query.order_by(desc(InstitutionReview.created_at))
    elif sort_by == "highest":
        query = query.order_by(desc(InstitutionReview.overall_rating))
    elif sort_by == "lowest":
        query = query.order_by(InstitutionReview.overall_rating)
    elif sort_by == "helpful":
        query = query.order_by(desc(InstitutionReview.helpful_count))
    
    # Pagination
    total = query.count()
    reviews = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Calculate average rating
    avg_rating = db.query(func.avg(InstitutionReview.overall_rating)).filter(
        InstitutionReview.institution_id == institution_id,
        InstitutionReview.status == ReviewStatus.APPROVED
    ).scalar()
    
    return {
        "items": [_review_to_response(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "average_rating": round(avg_rating, 2) if avg_rating else None
    }


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review."""
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _review_to_response(review)


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update own review."""
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")
    
    # Update fields
    if review_update.title is not None:
        review.title = review_update.title
    if review_update.content is not None:
        review.content = review_update.content
    if review_update.overall_rating is not None:
        review.overall_rating = review_update.overall_rating
    
    db.commit()
    db.refresh(review)
    
    update_institution_rating(db, review.institution_id)
    
    return _review_to_response(review)


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete own review or admin can delete any."""
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check ownership or admin
    if review.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    
    institution_id = review.institution_id
    
    db.delete(review)
    db.commit()
    
    # Update institution rating
    update_institution_rating(db, institution_id)
    
    return {"message": "Review deleted successfully"}


@router.post("/reviews/{review_id}/helpful")
def mark_helpful(
    review_id: int,
    vote: HelpfulVoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a review as helpful or unhelpful."""
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user already voted
    existing = db.query(ReviewHelpfulVote).filter(
        ReviewHelpfulVote.review_id == review_id,
        ReviewHelpfulVote.user_id == current_user.id
    ).first()
    
    if existing:
        # Update existing vote
        if existing.is_helpful != vote.is_helpful:
            # Change vote
            if vote.is_helpful:
                review.helpful_count += 1
                review.unhelpful_count -= 1
            else:
                review.helpful_count -= 1
                review.unhelpful_count += 1
            existing.is_helpful = vote.is_helpful
    else:
        # New vote
        new_vote = ReviewHelpfulVote(
            review_id=review_id,
            user_id=current_user.id,
            is_helpful=vote.is_helpful
        )
        db.add(new_vote)
        
        if vote.is_helpful:
            review.helpful_count += 1
        else:
            review.unhelpful_count += 1
    
    db.commit()
    
    return {
        "helpful_count": review.helpful_count,
        "unhelpful_count": review.unhelpful_count,
        "user_vote": vote.is_helpful
    }


@router.post("/reviews/{review_id}/report")
def report_review(
    review_id: int,
    report: ReportCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Report a review for moderation."""
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Create report
    new_report = ReviewReport(
        review_id=review_id,
        reporter_id=current_user.id,
        reason=report.reason,
        description=report.description
    )
    
    db.add(new_report)
    
    # Flag review if not already
    if review.status != ReviewStatus.FLAGGED:
        review.status = ReviewStatus.FLAGGED
    
    db.commit()
    
    return {"message": "Review reported successfully"}


@router.get("/reviews/pending")
def list_pending_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List pending reviews (admin only)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(InstitutionReview).filter(
        InstitutionReview.status == ReviewStatus.PENDING
    ).order_by(desc(InstitutionReview.created_at))
    
    total = query.count()
    reviews = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_review_to_response(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.post("/reviews/{review_id}/approve")
def approve_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a pending review (admin only)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = ReviewStatus.APPROVED
    db.commit()
    
    return {"message": "Review approved"}


@router.post("/reviews/{review_id}/reject")
def reject_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a review (admin only)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")
    
    review = db.query(InstitutionReview).filter(InstitutionReview.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.status = ReviewStatus.REJECTED
    db.commit()
    
    return {"message": "Review rejected"}


# Helper functions
def _review_to_response(review: InstitutionReview) -> dict:
    """Convert review model to response dict."""
    return {
        "id": review.id,
        "institution_id": review.institution_id,
        "user_id": review.user_id,
        "user_name": review.user.full_name if review.user else "Anonymous",
        "overall_rating": review.overall_rating,
        "academics_rating": review.academics_rating,
        "facilities_rating": review.facilities_rating,
        "faculty_rating": review.faculty_rating,
        "campus_life_rating": review.campus_life_rating,
        "value_for_money_rating": review.value_for_money_rating,
        "title": review.title,
        "content": review.content,
        "pros": review.pros or [],
        "cons": review.cons or [],
        "study_program": review.study_program,
        "graduation_year": review.graduation_year,
        "is_alumni": review.is_alumni,
        "helpful_count": review.helpful_count,
        "unhelpful_count": review.unhelpful_count,
        "status": review.status.value,
        "is_verified": review.is_verified,
        "created_at": review.created_at.isoformat() if review.created_at else None
    }


def update_institution_rating(db: Session, institution_id: int):
    """Update institution's average rating."""
    from sqlalchemy import func
    
    avg_rating = db.query(func.avg(InstitutionReview.overall_rating)).filter(
        InstitutionReview.institution_id == institution_id,
        InstitutionReview.status == ReviewStatus.APPROVED
    ).scalar()
    
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if institution and avg_rating:
        # Could add a rating field to institution model
        # institution.rating = round(avg_rating, 2)
        db.commit()
