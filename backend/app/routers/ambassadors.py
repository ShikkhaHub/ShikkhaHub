"""
Ambassador Program API
Manages campus ambassadors for growth and referrals
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ambassadors", tags=["ambassadors"])

# Models
class AmbassadorCreate(BaseModel):
    """Create ambassador request"""
    name: str
    email: EmailStr
    institution_id: str
    phone: str
    college_year: int  # 1-4 for undergrad, 1-5 for grad
    bio: str
    motivation: str
    
class AmbassadorUpdate(BaseModel):
    """Update ambassador profile"""
    bio: str | None = None
    phone: str | None = None
    motivation: str | None = None

class AmbassadorResponse(BaseModel):
    """Ambassador profile response"""
    id: str
    user_id: str
    institution_id: str
    status: str  # pending, approved, rejected, active, inactive
    referral_count: int
    total_referrals: int
    join_date: datetime
    performance_tier: str  # bronze, silver, gold, platinum
    bio: str
    phone: str
    
    class Config:
        from_attributes = True

class ReferralResponse(BaseModel):
    """Referral tracking response"""
    id: str
    ambassador_id: str
    referred_user_id: str | None
    status: str  # pending, registered, active
    created_at: datetime
    signup_date: datetime | None = None

# Routes

@router.post("/apply", response_model=AmbassadorResponse)
async def apply_as_ambassador(
    data: AmbassadorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply to become a campus ambassador"""
    
    # Check if already an ambassador
    existing = db.query(Ambassador).filter(
        Ambassador.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered as an ambassador"
        )
    
    # Create ambassador record
    ambassador = Ambassador(
        user_id=current_user.id,
        institution_id=data.institution_id,
        status="pending",
        referral_count=0,
        total_referrals=0,
        performance_tier="bronze",
        bio=data.bio,
        phone=data.phone,
        motivation=data.motivation,
        join_date=datetime.utcnow()
    )
    
    db.add(ambassador)
    db.commit()
    db.refresh(ambassador)
    
    return ambassador

@router.get("/me", response_model=AmbassadorResponse)
async def get_my_ambassador_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's ambassador profile"""
    
    ambassador = db.query(Ambassador).filter(
        Ambassador.user_id == current_user.id
    ).first()
    
    if not ambassador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not an ambassador"
        )
    
    return ambassador

@router.patch("/me", response_model=AmbassadorResponse)
async def update_ambassador_profile(
    data: AmbassadorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ambassador profile"""
    
    ambassador = db.query(Ambassador).filter(
        Ambassador.user_id == current_user.id
    ).first()
    
    if not ambassador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not an ambassador"
        )
    
    if data.bio is not None:
        ambassador.bio = data.bio
    if data.phone is not None:
        ambassador.phone = data.phone
    if data.motivation is not None:
        ambassador.motivation = data.motivation
    
    db.commit()
    db.refresh(ambassador)
    
    return ambassador

@router.get("/referrals", response_model=list[ReferralResponse])
async def get_my_referrals(
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referrals made by current ambassador"""
    
    ambassador = db.query(Ambassador).filter(
        Ambassador.user_id == current_user.id
    ).first()
    
    if not ambassador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not an ambassador"
        )
    
    referrals = db.query(Referral).filter(
        Referral.ambassador_id == ambassador.id
    ).offset(skip).limit(limit).all()
    
    return referrals

@router.post("/referrals/generate", response_model=dict)
async def generate_referral_link(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a unique referral link for ambassador"""
    
    ambassador = db.query(Ambassador).filter(
        Ambassador.user_id == current_user.id
    ).first()
    
    if not ambassador or ambassador.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must be an active ambassador"
        )
    
    # Generate unique code
    import secrets
    referral_code = secrets.token_urlsafe(12)[:12]
    
    referral_link = f"https://shikkhahub.app/ref/{referral_code}?ambassador={ambassador.id}"
    
    return {
        "code": referral_code,
        "link": referral_link,
        "stats": {
            "total_referrals": ambassador.total_referrals,
            "active_referrals": ambassador.referral_count,
            "performance_tier": ambassador.performance_tier
        }
    }

@router.get("/top", response_model=list[dict])
async def get_top_ambassadors(
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get top performing ambassadors leaderboard"""
    
    ambassadors = db.query(Ambassador).filter(
        Ambassador.status == "active"
    ).order_by(
        Ambassador.referral_count.desc()
    ).limit(limit).all()
    
    result = []
    for amb in ambassadors:
        user = db.query(User).filter(User.id == amb.user_id).first()
        result.append({
            "ambassador_id": amb.id,
            "name": user.name if user else "Anonymous",
            "institution_id": amb.institution_id,
            "referral_count": amb.referral_count,
            "performance_tier": amb.performance_tier
        })
    
    return result

@router.get("/leaderboard")
async def get_ambassador_leaderboard(
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db)
):
    """Get full ambassador leaderboard with rankings"""
    
    ambassadors = db.query(Ambassador).filter(
        Ambassador.status == "active"
    ).order_by(
        Ambassador.referral_count.desc()
    ).offset(skip).limit(limit).all()
    
    leaderboard = []
    for rank, amb in enumerate(ambassadors, 1):
        user = db.query(User).filter(User.id == amb.user_id).first()
        leaderboard.append({
            "rank": rank,
            "name": user.name if user else "Anonymous",
            "institution": amb.institution_id,
            "referrals": amb.referral_count,
            "tier": amb.performance_tier,
            "badge": "🥇" if rank <= 3 else "🥈" if rank <= 10 else "⭐"
        })
    
    return {
        "leaderboard": leaderboard,
        "total_count": db.query(Ambassador).filter(
            Ambassador.status == "active"
        ).count()
    }

@router.get("/stats")
async def get_ambassador_program_stats(
    db: Session = Depends(get_db)
):
    """Get overall ambassador program statistics"""
    
    total_ambassadors = db.query(Ambassador).count()
    active_ambassadors = db.query(Ambassador).filter(
        Ambassador.status == "active"
    ).count()
    pending_ambassadors = db.query(Ambassador).filter(
        Ambassador.status == "pending"
    ).count()
    
    total_referrals = db.query(Referral).count()
    completed_signups = db.query(Referral).filter(
        Referral.status == "registered"
    ).count()
    
    return {
        "total_ambassadors": total_ambassadors,
        "active_ambassadors": active_ambassadors,
        "pending_ambassadors": pending_ambassadors,
        "total_referrals": total_referrals,
        "completed_signups": completed_signups,
        "conversion_rate": (
            f"{(completed_signups / total_referrals * 100):.1f}%" 
            if total_referrals > 0 else "0%"
        )
    }
