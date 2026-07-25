"""Institution service layer for business logic."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status

from app.models.institution import Institution, InstitutionType
from app.models.location import Division, District, Upazila
from app.core.redis import cache_get, cache_set, generate_cache_key
from app.core.elasticsearch import search_institutions as es_search_institutions


class InstitutionService:
    """Service layer for institution operations."""
    
    @staticmethod
    def get_institution_by_slug(db: Session, slug: str) -> Optional[Institution]:
        """Get institution by slug with caching."""
        cache_key = generate_cache_key("institution", slug)
        
        # Try cache first
        cached = cache_get(cache_key)
        if cached:
            return Institution(**cached)
        
        # Query database
        institution = db.query(Institution).filter(Institution.slug == slug).first()
        
        if institution:
            # Cache for 5 minutes
            cache_set(cache_key, institution.to_dict(), ttl=300)
        
        return institution
    
    @staticmethod
    def list_institutions(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        type_id: Optional[int] = None,
        division_id: Optional[int] = None,
        district_id: Optional[int] = None,
        verified_only: bool = True,
        featured_only: bool = False,
        search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """List institutions with filters and pagination."""
        
        # Build query
        query = db.query(Institution)
        
        # Apply filters
        if type_id:
            query = query.filter(Institution.type_id == type_id)
        
        if division_id:
            query = query.join(Upazila).join(District).filter(
                District.division_id == division_id
            )
        
        if district_id:
            query = query.join(Upazila).filter(Upazila.district_id == district_id)
        
        if verified_only:
            query = query.filter(Institution.verification_status == "verified")
        
        if featured_only:
            query = query.filter(Institution.is_featured == True)
        
        if search_query:
            query = query.filter(
                Institution.name_en.ilike(f"%{search_query}%") |
                Institution.name_bn.ilike(f"%{search_query}%") |
                Institution.short_name.ilike(f"%{search_query}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        institutions = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "items": [inst.to_dict() for inst in institutions],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def get_institution_stats(db: Session) -> Dict[str, Any]:
        """Get institution statistics for dashboard."""
        total = db.query(Institution).count()
        verified = db.query(Institution).filter(
            Institution.verification_status == "verified"
        ).count()
        pending = db.query(Institution).filter(
            Institution.verification_status == "pending"
        ).count()
        flagged = db.query(Institution).filter(
            Institution.verification_status == "flagged"
        ).count()
        
        # By type
        by_type = db.query(
            InstitutionType.name,
            func.count(Institution.id)
        ).join(Institution).group_by(InstitutionType.name).all()
        
        return {
            "total": total,
            "verified": verified,
            "pending": pending,
            "flagged": flagged,
            "by_type": [{"name": name, "count": count} for name, count in by_type]
        }
    
    @staticmethod
    def get_top_institutions(db: Session, limit: int = 10) -> List[Institution]:
        """Get top institutions by view count."""
        return db.query(Institution).order_by(
            desc(Institution.view_count)
        ).limit(limit).all()
    
    @staticmethod
    def increment_view_count(db: Session, institution_id: int) -> None:
        """Increment institution view count."""
        institution = db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if institution:
            institution.view_count += 1
            db.commit()
    
    @staticmethod
    def verify_institution(
        db: Session,
        institution_id: int,
        verification_notes: Optional[str] = None
    ) -> Institution:
        """Verify an institution."""
        institution = db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Institution not found"
            )
        
        institution.verification_status = "verified"
        db.commit()
        db.refresh(institution)
        
        return institution
    
    @staticmethod
    def reject_institution(
        db: Session,
        institution_id: int,
        reason: str
    ) -> Institution:
        """Reject an institution."""
        institution = db.query(Institution).filter(
            Institution.id == institution_id
        ).first()
        
        if not institution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Institution not found"
            )
        
        institution.verification_status = "rejected"
        db.commit()
        db.refresh(institution)
        
        return institution


# Export service functions for easy access
get_institution_by_slug = InstitutionService.get_institution_by_slug
list_institutions = InstitutionService.list_institutions
get_institution_stats = InstitutionService.get_institution_stats
get_top_institutions = InstitutionService.get_top_institutions
increment_view_count = InstitutionService.increment_view_count
verify_institution = InstitutionService.verify_institution
reject_institution = InstitutionService.reject_institution
