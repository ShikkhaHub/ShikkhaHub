"""
ShikkhaHub API V2 - National Education Platform
Strategic endpoints for data, AI, and verification systems
"""

from fastapi import APIRouter, Query, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import logging

from app.services.data_collection import InstitutionDataCollector, SourceType
from app.services.ai_engine import (
    EducationDecisionEngine,
    StudentProfile,
)
from app.models.institution_v2 import (
    InstitutionV2,
    ProgramV2,
    VerificationStatus,
)
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2", tags=["v2"])


# ============================================================================
# DATA & INSTITUTION ENDPOINTS
# ============================================================================

@router.get("/institutions")
async def list_institutions(
    division: Optional[str] = None,
    district: Optional[str] = None,
    institution_type: Optional[str] = None,
    verified_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    List institutions with filters
    Sorted by verification status, then by trust score
    
    Args:
    - division: Filter by division (e.g., "Dhaka")
    - district: Filter by district (e.g., "Dhaka Sadar")
    - institution_type: Filter by type
    - verified_only: Return only verified institutions
    - skip/limit: Pagination
    """
    from sqlalchemy import select, and_

    query = select(InstitutionV2)

    if division:
        query = query.where(InstitutionV2.division == division)
    if district:
        query = query.where(InstitutionV2.district == district)
    if institution_type:
        query = query.where(InstitutionV2.type == institution_type)
    if verified_only:
        query = query.where(
            InstitutionV2.verification_status.in_([
                VerificationStatus.VERIFIED,
                VerificationStatus.OFFICIAL,
            ])
        )

    # Sort by verification status, then trust score
    query = query.order_by(
        InstitutionV2.verification_status.desc(),
        InstitutionV2.trust_score.desc(),
    ).offset(skip).limit(limit)

    result = await db.execute(query)
    institutions = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": str(inst.id),
                "name": inst.name,
                "type": inst.type,
                "location": f"{inst.district}, {inst.division}",
                "verification_status": inst.verification_status,
                "data_completeness": inst.data_completeness_score,
                "trust_score": inst.trust_score,
                "last_updated": inst.last_updated,
                "program_count": len(inst.programs) if inst.programs else 0,
            }
            for inst in institutions
        ],
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total_returned": len(institutions),
        },
    }


@router.get("/institutions/{institution_id}")
async def get_institution_detail(
    institution_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get complete institution details with verification info
    """
    institution = await db.get(InstitutionV2, institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Get programs
    programs = institution.programs or []
    data_sources = institution.data_sources or []
    verifications = institution.verifications or []

    return {
        "success": True,
        "data": {
            "id": str(institution.id),
            "name": institution.name,
            "name_bengali": institution.name_bengali,
            "type": institution.type,
            "description": institution.description,
            "location": {
                "division": institution.division,
                "district": institution.district,
                "upazila": institution.upazila,
                "address": institution.address,
                "coordinates": {
                    "lat": institution.latitude,
                    "lng": institution.longitude,
                },
            },
            "contact": {
                "phone": institution.phone_numbers,
                "email": institution.email,
                "website": institution.website_url,
                "admission_email": institution.admission_email,
                "admission_phone": institution.admission_phone,
            },
            "authority": {
                "name": institution.affiliation_authority,
                "id": institution.affiliation_id,
                "registration_number": institution.registration_number,
            },
            "statistics": {
                "students": institution.student_count,
                "faculty": institution.faculty_count,
                "founded": institution.founded_year,
                "established": institution.establishment_year,
            },
            "ratings": {
                "score": institution.user_rating,
                "reviews": institution.review_count,
                "ranking": institution.ranking_score,
            },
            "verification": {
                "status": institution.verification_status,
                "trust_score": institution.trust_score,
                "data_completeness": institution.data_completeness_score,
                "verified_by": institution.verified_by,
                "last_verified": institution.last_verified,
                "official_sources": institution.official_source_count,
                "alumni_verifications": institution.alumni_verification_count,
            },
            "programs": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "level": p.level,
                    "category": p.category,
                    "duration_years": p.duration_years,
                    "seats": p.seats,
                    "admission_requirements": p.admission_requirements,
                    "career_paths": p.career_paths,
                    "fees": {
                        "semester": p.semester_fee,
                        "total": p.total_fee,
                    },
                }
                for p in programs
            ],
            "data_sources": [
                {
                    "type": source.source_type,
                    "url": source.source_url,
                    "collected_date": source.collection_date,
                    "confidence": source.confidence_score,
                    "is_official": source.is_official,
                }
                for source in data_sources
            ],
            "verification_history": [
                {
                    "type": v.verification_type,
                    "verified_by": v.verified_by,
                    "date": v.verified_date,
                    "fields": v.fields_verified,
                }
                for v in verifications[-5:]  # Last 5 verifications
            ],
            "metadata": {
                "created_at": institution.created_at,
                "updated_at": institution.updated_at,
                "is_active": institution.is_active,
            },
        },
    }


@router.get("/search")
async def search_institutions(
    query: str = Query(..., min_length=2),
    division: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Full-text search with filters
    Response time target: <200ms
    
    Examples:
    - /search?query=Dhaka%20University
    - /search?query=engineering&division=Dhaka
    - /search?query=polytechnic&category=engineering
    """
    from sqlalchemy import select, or_, and_

    # Build search query
    search_query = select(InstitutionV2).where(
        and_(
            or_(
                InstitutionV2.name.ilike(f"%{query}%"),
                InstitutionV2.name_bengali.ilike(f"%{query}%"),
                InstitutionV2.description.ilike(f"%{query}%"),
            ),
            InstitutionV2.verification_status.in_([
                VerificationStatus.VERIFIED,
                VerificationStatus.OFFICIAL,
            ]),
        )
    )

    if division:
        search_query = search_query.where(InstitutionV2.division == division)

    # Order by relevance: name match > trust score > data completeness
    search_query = search_query.order_by(
        InstitutionV2.trust_score.desc(),
        InstitutionV2.data_completeness_score.desc(),
    ).limit(limit)

    result = await db.execute(search_query)
    institutions = result.scalars().all()

    # Filter by program category if specified
    if category:
        institutions = [
            inst for inst in institutions
            if any(p.category == category for p in (inst.programs or []))
        ]

    return {
        "success": True,
        "query": query,
        "results": [
            {
                "id": str(inst.id),
                "name": inst.name,
                "type": inst.type,
                "location": f"{inst.district}, {inst.division}",
                "relevance_score": 100,  # Could be enhanced with actual scoring
                "verification_status": inst.verification_status,
                "programs": len(inst.programs) if inst.programs else 0,
                "trust_score": inst.trust_score,
            }
            for inst in institutions
        ],
        "total_found": len(institutions),
    }


# ============================================================================
# AI DECISION ENGINE ENDPOINTS
# ============================================================================

@router.post("/ai/recommend")
async def get_ai_recommendations(
    query: str,
    gpa: float,
    interests: List[str] = [],
    location_preference: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    AI-powered institution recommendations
    
    Example:
    POST /ai/recommend
    {
        "query": "I got 3.8 GPA and love Computer Science. Best options in Dhaka?",
        "gpa": 3.8,
        "interests": ["engineering", "computer_science"],
        "location_preference": "Dhaka"
    }
    """
    try:
        engine = EducationDecisionEngine(db)

        profile = StudentProfile(
            gpa=gpa,
            interests=interests,
            location_preference=location_preference,
        )

        recommendations = await engine.recommend_institutions(query, profile)

        return recommendations

    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations",
        )


@router.post("/ai/careers")
async def get_career_recommendations(
    interests: List[str],
    gpa: float,
    db: AsyncSession = Depends(get_db),
):
    """
    Career recommendations based on interests and GPA
    """
    try:
        engine = EducationDecisionEngine(db)

        profile = StudentProfile(
            gpa=gpa,
            interests=interests,
        )

        result = await engine.recommend_careers(profile)
        return result

    except Exception as e:
        logger.error(f"Career recommendation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to recommend careers",
        )


@router.post("/ai/compare")
async def compare_institutions(
    institution_ids: List[str],
    db: AsyncSession = Depends(get_db),
):
    """
    Compare multiple institutions
    """
    try:
        engine = EducationDecisionEngine(db)
        result = await engine.compare_institutions(institution_ids)
        return result

    except Exception as e:
        logger.error(f"Comparison error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to compare institutions",
        )


# ============================================================================
# DATA COLLECTION & VERIFICATION ENDPOINTS
# ============================================================================

@router.post("/admin/data/collect")
async def trigger_data_collection(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger full data collection cycle
    WARNING: This can take hours
    """
    async def collect_data():
        collector = InstitutionDataCollector(db)
        result = await collector.collect_all()
        logger.info(f"Collection complete: {result}")

    background_tasks.add_task(collect_data)

    return {
        "success": True,
        "message": "Data collection started in background",
        "task": "data_collection",
    }


@router.post("/verify/alumni-report")
async def submit_alumni_verification(
    institution_id: str,
    report: dict,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Accept alumni verification reports
    
    Report format:
    {
        "fields_verified": {"name": true, "programs": true, "contact": false},
        "notes": "All information is current as of 2024",
        "graduation_year": 2020
    }
    """
    collector = InstitutionDataCollector(db)
    success = await collector.collect_from_alumni(institution_id, report)

    if success:
        return {
            "success": True,
            "message": "Alumni verification report submitted",
            "institution_id": institution_id,
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="Failed to submit alumni report",
        )


# ============================================================================
# STATISTICS & ANALYTICS ENDPOINTS
# ============================================================================

@router.get("/stats/overview")
async def get_platform_statistics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get platform-wide statistics
    """
    from sqlalchemy import func, select

    # Count institutions by status
    total_query = select(func.count(InstitutionV2.id))
    verified_query = select(func.count(InstitutionV2.id)).where(
        InstitutionV2.verification_status.in_([
            VerificationStatus.VERIFIED,
            VerificationStatus.OFFICIAL,
        ])
    )

    total_result = await db.execute(total_query)
    verified_result = await db.execute(verified_query)

    total_count = total_result.scalar() or 0
    verified_count = verified_result.scalar() or 0

    return {
        "success": True,
        "statistics": {
            "total_institutions": total_count,
            "verified_institutions": verified_count,
            "verification_rate": (verified_count / total_count * 100) if total_count > 0 else 0,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Platform health check"""
    return {
        "status": "healthy",
        "service": "ShikkhaHub API V2",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
