"""AI Chat endpoints for education assistant."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, get_current_active_user
from app.core.ai_service import get_education_assistant
from app.core.rate_limit import auth_limit, standard_limit
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User

router = APIRouter()


# Schemas
class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[str] = None  # If None, creates new session


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    context_used: int
    sources: List[dict]
    created_at: str
    
    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    title: Optional[str]
    context_type: Optional[str]
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    message_count: int


class ChatSessionDetail(ChatSessionResponse):
    messages: List[ChatMessageResponse]


class ChatFeedback(BaseModel):
    is_helpful: bool
    feedback_text: Optional[str] = None


# Helper functions
def generate_session_title(first_message: str) -> str:
    """Generate a title based on first message."""
    # Simple title generation - can be improved with AI
    words = first_message.split()[:6]
    title = ' '.join(words)
    if len(title) > 50:
        title = title[:47] + '...'
    return title or "New Chat"


# Endpoints
@router.post("/chat", response_model=dict)
@standard_limit()
async def chat(
    message: ChatMessageCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI assistant and get a response."""
    
    assistant = get_education_assistant()
    
    # Get or create session
    if message.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == message.session_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check ownership (if user is authenticated)
        if current_user and session.user_id and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this chat session"
            )
    else:
        # Create new session
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=current_user.id if current_user else None,
            title=generate_session_title(message.content),
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    # Get conversation history
    history = []
    if session:
        prev_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).limit(10).all()
        
        for msg in prev_messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # Store user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=message.content,
        context_used=0
    )
    db.add(user_msg)
    db.commit()
    
    # Get AI response
    result = await assistant.chat(message.content, history)
    
    # Store AI response
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["response"],
        context_used=result.get("context_used", 0),
        sources=result.get("sources", [])
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    
    # Update session timestamp
    session.updated_at = func.now()
    db.commit()
    
    return {
        "session_id": session.session_id,
        "message": {
            "id": ai_msg.id,
            "role": ai_msg.role,
            "content": ai_msg.content,
            "context_used": ai_msg.context_used,
            "sources": ai_msg.sources,
            "created_at": ai_msg.created_at.isoformat()
        },
        "user_message_id": user_msg.id
    }


@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all chat sessions for the current user."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).all()
    
    return [
        {
            "id": s.id,
            "session_id": s.session_id,
            "title": s.title,
            "context_type": s.context_type,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "message_count": len(s.messages)
        }
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session with all messages."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return {
        "id": session.id,
        "session_id": session.session_id,
        "title": session.title,
        "context_type": session.context_type,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "message_count": len(session.messages),
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "context_used": m.context_used,
                "sources": m.sources,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in session.messages
        ]
    }


@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session (soft delete)."""
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    session.is_active = False
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.post("/chat/messages/{message_id}/feedback")
async def add_feedback(
    message_id: int,
    feedback: ChatFeedback,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add feedback to an AI response."""
    message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Verify the message belongs to the user's session
    session = db.query(ChatSession).filter(ChatSession.id == message.session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add feedback to this message"
        )
    
    message.is_helpful = feedback.is_helpful
    message.feedback_text = feedback.feedback_text
    db.commit()
    
    return {"message": "Feedback added successfully"}


@router.post("/chat/suggestions")
async def get_suggestions(
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get suggested questions for the AI assistant."""
    return {
        "suggestions": [
            {
                "category": "Admissions",
                "questions": [
                    "What are the admission requirements for Dhaka University?",
                    "When is the HSC admission deadline for 2024?",
                    "How do I apply to medical colleges in Bangladesh?"
                ]
            },
            {
                "category": "Institutions",
                "questions": [
                    "What are the top engineering universities?",
                    "Compare BUET and DU",
                    "Which colleges have the best science programs?"
                ]
            },
            {
                "category": "Career",
                "questions": [
                    "What should I study to become a doctor?",
                    "Which universities offer good business programs?",
                    "What are the best subjects for software engineering?"
                ]
            }
        ]
    }
