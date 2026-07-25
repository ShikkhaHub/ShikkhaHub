"""
PostgreSQL Data Importer for ShikkhaHub.
Transforms scraped data and imports into the main database.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Add parent directory to path
import sys
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.models import (
    Institution, InstitutionType, InstitutionContact,
    Division, District, Upazila,
    EducationBoard
)

# Import ScrapedInstitution directly to avoid circular imports
import dataclasses
from typing import Optional

@dataclasses.dataclass
class ScrapedInstitution:
    """Standardized data structure for scraped institutions."""
    name_en: str
    name_bn: Optional[str] = None
    short_name: Optional[str] = None
    institution_type: str = "unknown"
    division: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    established_year: Optional[int] = None
    education_level: Optional[str] = None
    education_board: Optional[str] = None
    university_affiliation: Optional[str] = None
    ugc_approved: bool = False
    data_source: str = ""
    source_url: Optional[str] = None
    raw_data: Optional[dict] = None
    confidence_score: float = 0.0
    scraped_at: str = ""

logger = logging.getLogger(__name__)


class DataImporter:
    """Import scraped data into PostgreSQL with deduplication and validation."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or SessionLocal()
        self.stats = {
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0
        }
        # Cache for lookups
        self._type_cache: Dict[str, int] = {}
        self._location_cache: Dict[str, Any] = {}
        self._board_cache: Dict[str, int] = {}
    
    def _get_institution_type_id(self, type_name: str) -> Optional[int]:
        """Get or create institution type ID."""
        type_key = type_name.lower()
        
        if type_key not in self._type_cache:
            # Try to find existing
            inst_type = self.db.query(InstitutionType).filter(
                InstitutionType.name.ilike(type_name)
            ).first()
            
            if inst_type:
                self._type_cache[type_key] = inst_type.id
            else:
                # Create new type
                new_type = InstitutionType(
                    name=type_name.title(),
                    category=self._detect_category(type_name)
                )
                self.db.add(new_type)
                self.db.flush()
                self._type_cache[type_key] = new_type.id
        
        return self._type_cache.get(type_key)
    
    def _detect_category(self, type_name: str) -> str:
        """Detect institution category from type name."""
        type_lower = type_name.lower()
        if 'university' in type_lower:
            return 'higher_education'
        elif 'college' in type_lower:
            return 'higher_education'
        elif 'polytechnic' in type_lower or 'technical' in type_lower:
            return 'technical'
        elif 'madrasa' in type_lower:
            return 'secondary'
        elif 'school' in type_lower:
            return 'secondary'
        return 'other'
    
    def _resolve_location(self, division: Optional[str], district: Optional[str], 
                          upazila: Optional[str]) -> Dict[str, Optional[int]]:
        """Resolve location names to database IDs."""
        result = {'division_id': None, 'district_id': None, 'upazila_id': None}
        
        # Find upazila by name (most specific)
        if upazila:
            upazila_obj = self.db.query(Upazila).filter(
                Upazila.name_en.ilike(f"%{upazila}%")
            ).first()
            if upazila_obj:
                result['upazila_id'] = upazila_obj.id
                result['district_id'] = upazila_obj.district_id
                result['division_id'] = upazila_obj.district.division_id
                return result
        
        # Find district by name
        if district:
            district_obj = self.db.query(District).filter(
                District.name_en.ilike(f"%{district}%")
            ).first()
            if district_obj:
                result['district_id'] = district_obj.id
                result['division_id'] = district_obj.division_id
                return result
        
        # Find division by name
        if division:
            division_obj = self.db.query(Division).filter(
                Division.name_en.ilike(f"%{division}%")
            ).first()
            if division_obj:
                result['division_id'] = division_obj.id
        
        return result
    
    def _generate_slug(self, name: str) -> str:
        """Generate unique slug from name."""
        from slugify import slugify
        base_slug = slugify(name, max_length=100)
        
        # Check for existing
        existing = self.db.query(Institution).filter(
            Institution.slug.like(f"{base_slug}%")
        ).count()
        
        if existing > 0:
            return f"{base_slug}-{existing + 1}"
        return base_slug
    
    def _check_duplicate(self, scraped: ScrapedInstitution) -> Optional[Institution]:
        """Check if institution already exists."""
        # Try exact name match
        existing = self.db.query(Institution).filter(
            Institution.name_en.ilike(scraped.name_en)
        ).first()
        
        if existing:
            return existing
        
        # Try short name match
        if scraped.short_name:
            existing = self.db.query(Institution).filter(
                Institution.short_name.ilike(scraped.short_name)
            ).first()
            if existing:
                return existing
        
        # Try website match
        if scraped.website:
            existing = self.db.query(Institution).filter(
                Institution.website == scraped.website
            ).first()
            if existing:
                return existing
        
        return None
    
    def import_institution(self, scraped: ScrapedInstitution) -> Optional[Institution]:
        """Import a single scraped institution."""
        try:
            # Check for duplicates
            existing = self._check_duplicate(scraped)
            
            # Get institution type ID
            type_id = self._get_institution_type_id(scraped.institution_type)
            if not type_id:
                logger.warning(f"Unknown institution type: {scraped.institution_type}")
                self.stats['failed'] += 1
                return None
            
            # Resolve location
            location_ids = self._resolve_location(
                scraped.division, 
                scraped.district, 
                scraped.upazila
            )
            
            if existing:
                # Update existing institution
                existing.name_bn = existing.name_bn or scraped.name_bn
                existing.short_name = existing.short_name or scraped.short_name
                existing.upazila_id = existing.upazila_id or location_ids['upazila_id']
                existing.phone = existing.phone or scraped.phone
                existing.email = existing.email or scraped.email
                existing.website = existing.website or scraped.website
                existing.established_year = existing.established_year or scraped.established_year
                existing.data_source = f"{existing.data_source},{scraped.data_source}" if existing.data_source else scraped.data_source
                existing.last_updated = scraped.scraped_at
                
                self.db.commit()
                self.stats['updated'] += 1
                logger.debug(f"Updated institution: {existing.name_en}")
                return existing
            
            # Create new institution
            new_institution = Institution(
                name_en=scraped.name_en,
                name_bn=scraped.name_bn,
                short_name=scraped.short_name,
                slug=self._generate_slug(scraped.name_en),
                type_id=type_id,
                established_year=scraped.established_year,
                upazila_id=location_ids['upazila_id'],
                address=scraped.address,
                phone=scraped.phone,
                email=scraped.email,
                website=scraped.website,
                description=None,  # Would need separate scraping
                data_source=scraped.data_source,
                verification_status='pending',  # Requires manual review
                is_active=True
            )
            
            self.db.add(new_institution)
            self.db.flush()  # Get ID without committing
            
            # Add primary contact if available
            if scraped.phone or scraped.email:
                contact = InstitutionContact(
                    institution_id=new_institution.id,
                    contact_type='general',
                    phone=scraped.phone,
                    email=scraped.email,
                    is_primary=True
                )
                self.db.add(contact)
            
            self.db.commit()
            self.stats['created'] += 1
            logger.info(f"Created institution: {new_institution.name_en}")
            return new_institution
            
        except IntegrityError as e:
            self.db.rollback()
            self.stats['failed'] += 1
            logger.error(f"Database integrity error for {scraped.name_en}: {e}")
            return None
        except Exception as e:
            self.db.rollback()
            self.stats['failed'] += 1
            logger.error(f"Error importing {scraped.name_en}: {e}")
            return None
    
    def bulk_import(self, institutions: List[ScrapedInstitution]) -> Dict[str, int]:
        """Import multiple institutions."""
        logger.info(f"Starting bulk import of {len(institutions)} institutions...")
        
        for i, inst in enumerate(institutions):
            self.import_institution(inst)
            
            if (i + 1) % 50 == 0:
                logger.info(f"Processed {i+1}/{len(institutions)} institutions...")
        
        logger.info(f"Import complete. Stats: {self.stats}")
        return self.stats.copy()
    
    def close(self):
        """Close database session."""
        self.db.close()
