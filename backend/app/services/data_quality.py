"""Data Quality Service for ShikkhaHub.

This module provides:
- Data validation rules
- Duplicate detection algorithm
- Data freshness alerts
- Data quality scoring
"""
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
from collections import defaultdict

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.institution import Institution, InstitutionType
from app.models.location import Division, District, Upazila
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """A single validation issue."""
    field: str
    issue_type: str
    message: str
    severity: str  # error, warning, info


@dataclass
class DataQualityReport:
    """Complete data quality report for an institution."""
    institution_id: int
    institution_name: str
    overall_score: float  # 0-100
    issues: List[ValidationIssue]
    freshness_score: float
    completeness_score: float
    accuracy_score: float


@dataclass
class DuplicateMatch:
    """A potential duplicate match."""
    institution_id_1: int
    institution_name_1: str
    institution_id_2: int
    institution_name_2: str
    similarity_score: float
    matching_fields: List[str]
    confidence: str  # high, medium, low


class DataValidator:
    """Validate institution data against rules."""
    
    # Required fields for minimum viable data
    REQUIRED_FIELDS = ['name_en', 'type_id']
    
    # Recommended fields for good data quality
    RECOMMENDED_FIELDS = [
        'name_bn', 'short_name', 'established_year',
        'upazila_id', 'address', 'phone', 'email', 'website'
    ]
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^[\d\s\-\+\(\)]+$')
    URL_PATTERN = re.compile(r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+')
    YEAR_PATTERN = re.compile(r'^\d{4}$')
    
    @staticmethod
    def validate_email(email: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate email format."""
        if not email:
            return True, None  # Empty is allowed
        if len(email) > 100:
            return False, "Email too long (max 100 characters)"
        if not DataValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        return True, None
    
    @staticmethod
    def validate_phone(phone: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate phone number format."""
        if not phone:
            return True, None
        if len(phone) > 50:
            return False, "Phone number too long (max 50 characters)"
        if not DataValidator.PHONE_PATTERN.match(phone):
            return False, "Invalid phone format"
        return True, None
    
    @staticmethod
    def validate_website(url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """Validate website URL format."""
        if not url:
            return True, None
        if len(url) > 255:
            return False, "URL too long (max 255 characters)"
        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            return False, "URL should start with http:// or https://"
        return True, None
    
    @staticmethod
    def validate_year(year: Optional[int]) -> Tuple[bool, Optional[str]]:
        """Validate established year."""
        if year is None:
            return True, None
        current_year = datetime.now().year
        if year < 1800 or year > current_year:
            return False, f"Year must be between 1800 and {current_year}"
        return True, None
    
    @classmethod
    def validate_institution(cls, institution: Institution) -> List[ValidationIssue]:
        """Run all validation rules on an institution."""
        issues = []
        
        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            value = getattr(institution, field, None)
            if not value:
                issues.append(ValidationIssue(
                    field=field,
                    issue_type="missing_required",
                    message=f"Required field '{field}' is missing",
                    severity="error"
                ))
        
        # Check recommended fields
        for field in cls.RECOMMENDED_FIELDS:
            value = getattr(institution, field, None)
            if not value:
                issues.append(ValidationIssue(
                    field=field,
                    issue_type="missing_recommended",
                    message=f"Recommended field '{field}' is missing",
                    severity="warning"
                ))
        
        # Validate email
        valid, error = cls.validate_email(institution.email)
        if not valid:
            issues.append(ValidationIssue(
                field="email",
                issue_type="invalid_format",
                message=error or "Invalid email",
                severity="error"
            ))
        
        # Validate phone
        valid, error = cls.validate_phone(institution.phone)
        if not valid:
            issues.append(ValidationIssue(
                field="phone",
                issue_type="invalid_format",
                message=error or "Invalid phone",
                severity="error"
            ))
        
        # Validate website
        valid, error = cls.validate_website(institution.website)
        if not valid:
            issues.append(ValidationIssue(
                field="website",
                issue_type="invalid_format",
                message=error or "Invalid website URL",
                severity="warning"
            ))
        
        # Validate year
        valid, error = cls.validate_year(institution.established_year)
        if not valid:
            issues.append(ValidationIssue(
                field="established_year",
                issue_type="invalid_value",
                message=error or "Invalid year",
                severity="error"
            ))
        
        # Check for suspicious data
        if institution.name_en and len(institution.name_en) < 5:
            issues.append(ValidationIssue(
                field="name_en",
                issue_type="suspicious_data",
                message="Institution name seems too short",
                severity="warning"
            ))
        
        return issues


class DuplicateDetector:
    """Detect potential duplicate institutions."""
    
    def __init__(self, similarity_threshold: float = None):
        self.similarity_threshold = similarity_threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize institution name for comparison."""
        if not name:
            return ""
        # Convert to lowercase
        name = name.lower()
        # Remove common suffixes
        suffixes = [
            'university', 'college', 'school', 'institute', 'institution',
            'polytechnic', 'madrasa', 'academy', 'center', 'centre'
        ]
        for suffix in suffixes:
            name = name.replace(f' {suffix}', '')
            name = name.replace(f'{suffix} ', '')
        # Remove punctuation and extra spaces
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    @staticmethod
    def calculate_similarity(str1: str, str2: str) -> float:
        """Calculate string similarity using SequenceMatcher."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def find_duplicates(
        self,
        db: Session,
        institution_type_id: Optional[int] = None,
        location_id: Optional[int] = None
    ) -> List[DuplicateMatch]:
        """Find potential duplicate institutions."""
        # Query institutions
        query = db.query(Institution).filter(Institution.is_active == True)
        
        if institution_type_id:
            query = query.filter(Institution.type_id == institution_type_id)
        
        if location_id:
            query = query.filter(Institution.upazila_id == location_id)
        
        institutions = query.all()
        
        duplicates = []
        checked_pairs = set()
        
        for i, inst1 in enumerate(institutions):
            for inst2 in institutions[i + 1:]:
                # Skip if pair already checked
                pair_key = tuple(sorted([inst1.id, inst2.id]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                match = self._compare_institutions(inst1, inst2)
                if match:
                    duplicates.append(match)
        
        # Sort by similarity score
        duplicates.sort(key=lambda x: x.similarity_score, reverse=True)
        return duplicates
    
    def _compare_institutions(
        self,
        inst1: Institution,
        inst2: Institution
    ) -> Optional[DuplicateMatch]:
        """Compare two institutions for potential duplication."""
        matching_fields = []
        scores = []
        
        # Compare names
        name1_normalized = self.normalize_name(inst1.name_en or "")
        name2_normalized = self.normalize_name(inst2.name_en or "")
        name_similarity = self.calculate_similarity(name1_normalized, name2_normalized)
        
        if name_similarity >= self.similarity_threshold:
            matching_fields.append("name_en")
            scores.append(name_similarity)
        
        # Compare short names
        if inst1.short_name and inst2.short_name:
            short_similarity = self.calculate_similarity(
                inst1.short_name.lower(),
                inst2.short_name.lower()
            )
            if short_similarity >= self.similarity_threshold:
                matching_fields.append("short_name")
                scores.append(short_similarity)
        
        # Compare Bengali names
        if inst1.name_bn and inst2.name_bn:
            bn_similarity = self.calculate_similarity(inst1.name_bn, inst2.name_bn)
            if bn_similarity >= self.similarity_threshold:
                matching_fields.append("name_bn")
                scores.append(bn_similarity)
        
        # Check if same location
        if inst1.upazila_id and inst2.upazila_id and inst1.upazila_id == inst2.upazila_id:
            matching_fields.append("location")
            scores.append(1.0)
        
        # Check if same phone
        if inst1.phone and inst2.phone:
            phone1 = re.sub(r'\D', '', inst1.phone)
            phone2 = re.sub(r'\D', '', inst2.phone)
            if phone1 and phone2 and phone1 == phone2:
                matching_fields.append("phone")
                scores.append(1.0)
        
        # Determine if duplicate
        if not scores:
            return None
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score < self.similarity_threshold:
            return None
        
        # Determine confidence
        if avg_score >= 0.95 and len(matching_fields) >= 3:
            confidence = "high"
        elif avg_score >= 0.85 and len(matching_fields) >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        return DuplicateMatch(
            institution_id_1=inst1.id,
            institution_name_1=inst1.name_en,
            institution_id_2=inst2.id,
            institution_name_2=inst2.name_en,
            similarity_score=avg_score,
            matching_fields=matching_fields,
            confidence=confidence
        )


class FreshnessChecker:
    """Check data freshness and alert on stale data."""
    
    def __init__(self, freshness_days: int = None):
        self.freshness_days = freshness_days or settings.DATA_FRESHNESS_DAYS
    
    def check_institution_freshness(
        self,
        institution: Institution
    ) -> Dict[str, Any]:
        """Check freshness of institution data."""
        if not institution.last_updated:
            return {
                "is_fresh": False,
                "days_since_update": None,
                "status": "never_updated",
                "message": "Institution has never been updated"
            }
        
        days_since_update = (datetime.utcnow() - institution.last_updated).days
        threshold = self.freshness_days
        
        if days_since_update < threshold / 3:
            status = "fresh"
            is_fresh = True
        elif days_since_update < threshold:
            status = "aging"
            is_fresh = True
        elif days_since_update < threshold * 2:
            status = "stale"
            is_fresh = False
        else:
            status = "very_stale"
            is_fresh = False
        
        return {
            "is_fresh": is_fresh,
            "days_since_update": days_since_update,
            "threshold_days": threshold,
            "status": status,
            "last_updated": institution.last_updated.isoformat() if institution.last_updated else None
        }
    
    def find_stale_institutions(
        self,
        db: Session,
        institution_type_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find institutions with stale data."""
        cutoff = datetime.utcnow() - timedelta(days=self.freshness_days)
        
        query = db.query(Institution).filter(
            Institution.is_active == True
        ).filter(
            or_(
                Institution.last_updated < cutoff,
                Institution.last_updated == None
            )
        )
        
        if institution_type_id:
            query = query.filter(Institution.type_id == institution_type_id)
        
        institutions = query.all()
        
        stale_list = []
        for inst in institutions:
            freshness = self.check_institution_freshness(inst)
            if not freshness["is_fresh"]:
                stale_list.append({
                    "institution_id": inst.id,
                    "name": inst.name_en,
                    **freshness
                })
        
        # Sort by days since update (oldest first)
        stale_list.sort(key=lambda x: x.get("days_since_update") or 9999, reverse=True)
        return stale_list
    
    def get_freshness_summary(self, db: Session) -> Dict[str, Any]:
        """Get overall data freshness summary."""
        total = db.query(Institution).filter(Institution.is_active == True).count()
        
        cutoff_fresh = datetime.utcnow() - timedelta(days=self.freshness_days / 3)
        cutoff_aging = datetime.utcnow() - timedelta(days=self.freshness_days)
        cutoff_stale = datetime.utcnow() - timedelta(days=self.freshness_days * 2)
        
        fresh_count = db.query(Institution).filter(
            Institution.is_active == True,
            Institution.last_updated >= cutoff_fresh
        ).count()
        
        aging_count = db.query(Institution).filter(
            Institution.is_active == True,
            Institution.last_updated >= cutoff_aging,
            Institution.last_updated < cutoff_fresh
        ).count()
        
        stale_count = db.query(Institution).filter(
            Institution.is_active == True,
            Institution.last_updated >= cutoff_stale,
            Institution.last_updated < cutoff_aging
        ).count()
        
        very_stale_count = db.query(Institution).filter(
            Institution.is_active == True,
            or_(
                Institution.last_updated < cutoff_stale,
                Institution.last_updated == None
            )
        ).count()
        
        return {
            "total_institutions": total,
            "fresh": fresh_count,
            "aging": aging_count,
            "stale": stale_count,
            "very_stale": very_stale_count,
            "freshness_rate": (fresh_count / total * 100) if total > 0 else 0,
            "threshold_days": self.freshness_days,
            "timestamp": datetime.utcnow().isoformat()
        }


class DataQualityService:
    """Main service for data quality operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.validator = DataValidator()
        self.duplicate_detector = DuplicateDetector()
        self.freshness_checker = FreshnessChecker()
    
    def generate_institution_report(
        self,
        institution_id: int
    ) -> Optional[DataQualityReport]:
        """Generate quality report for a single institution."""
        institution = self.db.query(Institution).get(institution_id)
        if not institution:
            return None
        
        # Run validation
        issues = self.validator.validate_institution(institution)
        
        # Calculate freshness score
        freshness_info = self.freshness_checker.check_institution_freshness(institution)
        freshness_score = 100 if freshness_info["is_fresh"] else max(0, 100 - freshness_info.get("days_since_update", 0))
        
        # Calculate completeness score
        total_recommended = len(self.validator.RECOMMENDED_FIELDS)
        filled_recommended = sum(
            1 for f in self.validator.RECOMMENDED_FIELDS
            if getattr(institution, f, None)
        )
        completeness_score = (filled_recommended / total_recommended * 100) if total_recommended > 0 else 100
        
        # Calculate accuracy score
        error_count = sum(1 for i in issues if i.severity == "error")
        warning_count = sum(1 for i in issues if i.severity == "warning")
        accuracy_score = max(0, 100 - (error_count * 10) - (warning_count * 5))
        
        # Overall score (weighted average)
        overall_score = (
            freshness_score * 0.3 +
            completeness_score * 0.4 +
            accuracy_score * 0.3
        )
        
        return DataQualityReport(
            institution_id=institution.id,
            institution_name=institution.name_en,
            overall_score=round(overall_score, 2),
            issues=issues,
            freshness_score=round(freshness_score, 2),
            completeness_score=round(completeness_score, 2),
            accuracy_score=round(accuracy_score, 2)
        )
    
    def get_overall_quality_summary(self) -> Dict[str, Any]:
        """Get overall data quality summary."""
        total = self.db.query(Institution).filter(Institution.is_active == True).count()
        
        # Verified vs pending
        verified_count = self.db.query(Institution).filter(
            Institution.is_active == True,
            Institution.verification_status == "verified"
        ).count()
        
        pending_count = self.db.query(Institution).filter(
            Institution.is_active == True,
            Institution.verification_status == "pending"
        ).count()
        
        flagged_count = self.db.query(Institution).filter(
            Institution.is_active == True,
            Institution.verification_status == "flagged"
        ).count()
        
        # Data source breakdown
        sources = self.db.query(
            Institution.data_source,
            func.count(Institution.id)
        ).filter(
            Institution.is_active == True
        ).group_by(Institution.data_source).all()
        
        source_breakdown = {
            source or "unknown": count for source, count in sources
        }
        
        return {
            "total_institutions": total,
            "verified": verified_count,
            "pending": pending_count,
            "flagged": flagged_count,
            "verification_rate": (verified_count / total * 100) if total > 0 else 0,
            "source_breakdown": source_breakdown,
            "freshness": self.freshness_checker.get_freshness_summary(self.db),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def find_duplicates(
        self,
        institution_type_id: Optional[int] = None
    ) -> List[DuplicateMatch]:
        """Find potential duplicate institutions."""
        return self.duplicate_detector.find_duplicates(
            self.db, institution_type_id
        )
    
    def find_stale_data(
        self,
        institution_type_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find institutions with stale data."""
        return self.freshness_checker.find_stale_institutions(
            self.db, institution_type_id
        )
    
    def validate_all_institutions(
        self,
        institution_type_id: Optional[int] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Validate all institutions and return summary."""
        query = self.db.query(Institution).filter(Institution.is_active == True)
        
        if institution_type_id:
            query = query.filter(Institution.type_id == institution_type_id)
        
        institutions = query.limit(limit).all()
        
        reports = []
        total_issues = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for institution in institutions:
            report = self.generate_institution_report(institution.id)
            if report:
                reports.append(report)
                for issue in report.issues:
                    total_issues[issue.issue_type] += 1
                    severity_counts[issue.severity] += 1
        
        # Calculate average scores
        avg_scores = {
            "overall": sum(r.overall_score for r in reports) / len(reports) if reports else 0,
            "freshness": sum(r.freshness_score for r in reports) / len(reports) if reports else 0,
            "completeness": sum(r.completeness_score for r in reports) / len(reports) if reports else 0,
            "accuracy": sum(r.accuracy_score for r in reports) / len(reports) if reports else 0,
        }
        
        return {
            "institutions_checked": len(institutions),
            "average_scores": {k: round(v, 2) for k, v in avg_scores.items()},
            "total_issues_by_type": dict(total_issues),
            "severity_breakdown": dict(severity_counts),
            "institutions_with_errors": sum(1 for r in reports if any(i.severity == "error" for i in r.issues)),
            "institutions_with_warnings": sum(1 for r in reports if any(i.severity == "warning" for i in r.issues)),
            "timestamp": datetime.utcnow().isoformat()
        }
