"""Q&A (Question and Answer) API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.core.rate_limit import standard_limit
from app.models.qa import Question, Answer, QuestionVote, AnswerVote, QuestionStatus, AnswerStatus
from app.models.user import User

router = APIRouter()


# Schemas
class QuestionCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=255)
    content: str = Field(..., min_length=20, max_length=5000)
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    institution_id: Optional[int] = None


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class AnswerCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)


class AnswerUpdate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)


class AnswerResponse(BaseModel):
    id: int
    question_id: int
    user_id: int
    user_name: str
    content: str
    upvote_count: int
    downvote_count: int
    status: str
    is_official: bool
    is_accepted: bool  # Best answer
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    title: str
    content: str
    category: Optional[str]
    tags: List[str]
    institution_id: Optional[int]
    view_count: int
    answer_count: int
    status: str
    best_answer_id: Optional[int]
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class QuestionDetailResponse(QuestionResponse):
    answers: List[AnswerResponse]


# Endpoints
@router.post("/questions", response_model=QuestionResponse)
@standard_limit()
def create_question(
    question: QuestionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new question."""
    db_question = Question(
        user_id=current_user.id,
        title=question.title,
        content=question.content,
        category=question.category,
        tags=question.tags or [],
        institution_id=question.institution_id,
        status=QuestionStatus.OPEN
    )
    
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    return _question_to_response(db_question)


@router.get("/questions", response_model=List[QuestionResponse])
def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    institution_id: Optional[int] = None,
    status: Optional[str] = Query(None, enum=["open", "answered", "closed"]),
    sort_by: str = Query("newest", enum=["newest", "popular", "unanswered"]),
    db: Session = Depends(get_db)
):
    """List all questions."""
    query = db.query(Question)
    
    # Filters
    if category:
        query = query.filter(Question.category == category)
    if institution_id:
        query = query.filter(Question.institution_id == institution_id)
    if status:
        query = query.filter(Question.status == status)
    
    # Sorting
    if sort_by == "newest":
        query = query.order_by(desc(Question.created_at))
    elif sort_by == "popular":
        query = query.order_by(desc(Question.view_count))
    elif sort_by == "unanswered":
        query = query.filter(Question.status == QuestionStatus.OPEN).order_by(desc(Question.created_at))
    
    questions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return [_question_to_response(q) for q in questions]


@router.get("/questions/{question_id}", response_model=QuestionDetailResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """Get question details with answers."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Increment view count
    question.view_count += 1
    db.commit()
    
    return _question_to_detail_response(question)


@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update own question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this question")
    
    if question_update.title:
        question.title = question_update.title
    if question_update.content:
        question.content = question_update.content
    if question_update.category:
        question.category = question_update.category
    if question_update.tags is not None:
        question.tags = question_update.tags
    
    db.commit()
    db.refresh(question)
    
    return _question_to_response(question)


@router.delete("/questions/{question_id}")
def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete own question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Not authorized to delete this question")
    
    db.delete(question)
    db.commit()
    
    return {"message": "Question deleted successfully"}


@router.post("/questions/{question_id}/answers", response_model=AnswerResponse)
@standard_limit()
def create_answer(
    question_id: int,
    answer: AnswerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Answer a question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.status == QuestionStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Question is closed")
    
    db_answer = Answer(
        question_id=question_id,
        user_id=current_user.id,
        content=answer.content,
        status=AnswerStatus.APPROVED  # Auto-approve for now
    )
    
    db.add(db_answer)
    
    # Update question
    question.answer_count += 1
    question.status = QuestionStatus.ANSWERED
    
    db.commit()
    db.refresh(db_answer)
    
    return _answer_to_response(db_answer)


@router.put("/answers/{answer_id}", response_model=AnswerResponse)
def update_answer(
    answer_id: int,
    answer_update: AnswerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update own answer."""
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    if answer.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this answer")
    
    answer.content = answer_update.content
    db.commit()
    db.refresh(answer)
    
    return _answer_to_response(answer)


@router.delete("/answers/{answer_id}")
def delete_answer(
    answer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete own answer."""
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    if answer.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Not authorized to delete this answer")
    
    question_id = answer.question_id
    
    db.delete(answer)
    
    # Update question answer count
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        question.answer_count -= 1
        if question.answer_count <= 0:
            question.status = QuestionStatus.OPEN
    
    db.commit()
    
    return {"message": "Answer deleted successfully"}


@router.post("/answers/{answer_id}/accept")
def accept_answer(
    answer_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark answer as best/accepted (question owner only)."""
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    question = db.query(Question).filter(Question.id == answer.question_id).first()
    
    # Only question owner or admin can accept answer
    if question.user_id != current_user.id and not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Only question owner can accept answers")
    
    # Unaccept previous best answer if exists
    if question.best_answer_id:
        prev_best = db.query(Answer).filter(Answer.id == question.best_answer_id).first()
        if prev_best:
            prev_best.status = AnswerStatus.APPROVED
    
    # Accept new answer
    question.best_answer_id = answer_id
    answer.status = AnswerStatus.ACCEPTED
    
    db.commit()
    
    return {"message": "Answer accepted as best answer"}


@router.post("/questions/{question_id}/vote")
def vote_question(
    question_id: int,
    is_upvote: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upvote or downvote a question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Check existing vote
    existing = db.query(QuestionVote).filter(
        QuestionVote.question_id == question_id,
        QuestionVote.user_id == current_user.id
    ).first()
    
    if existing:
        # Update vote
        if existing.is_upvote != is_upvote:
            if is_upvote:
                # Changed from downvote to upvote
                pass  # No counters on question for now
            else:
                pass
        existing.is_upvote = is_upvote
    else:
        # New vote
        new_vote = QuestionVote(
            question_id=question_id,
            user_id=current_user.id,
            is_upvote=is_upvote
        )
        db.add(new_vote)
    
    db.commit()
    
    return {"message": "Vote recorded"}


@router.post("/answers/{answer_id}/vote")
def vote_answer(
    answer_id: int,
    is_upvote: bool,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upvote or downvote an answer."""
    answer = db.query(Answer).filter(Answer.id == answer_id).first()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")
    
    existing = db.query(AnswerVote).filter(
        AnswerVote.answer_id == answer_id,
        AnswerVote.user_id == current_user.id
    ).first()
    
    if existing:
        if existing.is_upvote != is_upvote:
            if is_upvote:
                answer.upvote_count += 1
                answer.downvote_count -= 1
            else:
                answer.upvote_count -= 1
                answer.downvote_count += 1
        existing.is_upvote = is_upvote
    else:
        new_vote = AnswerVote(
            answer_id=answer_id,
            user_id=current_user.id,
            is_upvote=is_upvote
        )
        db.add(new_vote)
        
        if is_upvote:
            answer.upvote_count += 1
        else:
            answer.downvote_count += 1
    
    db.commit()
    
    return {
        "upvote_count": answer.upvote_count,
        "downvote_count": answer.downvote_count
    }


# Helper functions
def _question_to_response(question: Question) -> dict:
    """Convert question model to response dict."""
    return {
        "id": question.id,
        "user_id": question.user_id,
        "user_name": question.user.full_name if question.user else "Anonymous",
        "title": question.title,
        "content": question.content[:500] + "..." if len(question.content) > 500 else question.content,
        "category": question.category,
        "tags": question.tags or [],
        "institution_id": question.institution_id,
        "view_count": question.view_count,
        "answer_count": question.answer_count,
        "status": question.status.value,
        "best_answer_id": question.best_answer_id,
        "created_at": question.created_at.isoformat() if question.created_at else None,
        "updated_at": question.updated_at.isoformat() if question.updated_at else None
    }


def _question_to_detail_response(question: Question) -> dict:
    """Convert question model to detailed response with answers."""
    result = _question_to_response(question)
    result["content"] = question.content  # Full content
    result["answers"] = [_answer_to_response(a) for a in question.answers]
    return result


def _answer_to_response(answer: Answer) -> dict:
    """Convert answer model to response dict."""
    return {
        "id": answer.id,
        "question_id": answer.question_id,
        "user_id": answer.user_id,
        "user_name": answer.user.full_name if answer.user else "Anonymous",
        "content": answer.content,
        "upvote_count": answer.upvote_count,
        "downvote_count": answer.downvote_count,
        "status": answer.status.value,
        "is_official": answer.is_official,
        "is_accepted": answer.status == AnswerStatus.ACCEPTED,
        "created_at": answer.created_at.isoformat() if answer.created_at else None,
        "updated_at": answer.updated_at.isoformat() if answer.updated_at else None
    }
