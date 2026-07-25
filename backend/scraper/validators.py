"""
Data Quality Validators for Scraped Content.
Ensures data accuracy and completeness before import.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from scraper.base import ScrapedInstitution


class ValidationSeverity(Enum):
    ERROR = "error"  # Must fix before import
    WARNING = "warning"  # Should fix, but can import
    INFO = "info"  # Suggestion for improvement


@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: ValidationSeverity
    value: Any = None


class InstitutionValidator:
    """Validates scraped institution data for quality."""
    
    # Valid Bangladesh divisions
    VALID_DIVISIONS = {
        'dhaka', 'chittagong', 'rajshahi', 'khulna', 
        'barisal', 'sylhet', 'rangpur', 'mymensingh',
        'চট্টগ্রাম', 'ঢাকা', 'রাজশাহী', 'খুলনা',
        'বরিশাল', 'সিলেট', 'রংপুর', 'ময়মনসিংহ'
    }
    
    # Valid institution types
    VALID_TYPES = {
        'university', 'public_university', 'private_university', 
        'international_university', 'specialized_university',
        'college', 'school', 'polytechnic', 'madrasa', 
        'institute', 'technical_institute', 'vocational_institute',
        'qawmi_madrasa', 'alia_madrasa', 'hifz_madrasa',
        'textile_institute', 'marine_institute', 'agricultural_institute',
        'technical_school', 'general_madrasa', 'unknown'
    }
    
    def validate(self, institution: ScrapedInstitution) -> List[ValidationIssue]:
        """Run all validations on an institution."""
        issues = []
        
        issues.extend(self._validate_name(institution))
        issues.extend(self._validate_type(institution))
        issues.extend(self._validate_location(institution))
        issues.extend(self._validate_contact(institution))
        issues.extend(self._validate_year(institution))
        
        return issues
    
    def _validate_name(self, inst: ScrapedInstitution) -> List[ValidationIssue]:
        """Validate institution name."""
        issues = []
        
        if not inst.name_en or len(inst.name_en.strip()) < 3:
            issues.append(ValidationIssue(
                field='name_en',
                message='Institution name is too short (min 3 characters)',
                severity=ValidationSeverity.ERROR,
                value=inst.name_en
            ))
        
        if inst.name_en and len(inst.name_en) > 300:
            issues.append(ValidationIssue(
                field='name_en',
                message='Institution name is too long (max 300 characters)',
                severity=ValidationSeverity.WARNING,
                value=inst.name_en[:50] + '...'
            ))
        
        # Check for suspicious patterns
        if inst.name_en:
            suspicious = ['test', 'demo', 'sample', 'example', 'xxx', 'temp']
            if any(s in inst.name_en.lower() for s in suspicious):
                issues.append(ValidationIssue(
                    field='name_en',
                    message='Name contains suspicious/test keywords',
                    severity=ValidationSeverity.WARNING,
                    value=inst.name_en
                ))
        
        return issues
    
    def _validate_type(self, inst: ScrapedInstitution) -> List[ValidationIssue]:
        """Validate institution type."""
        issues = []
        
        if not inst.institution_type:
            issues.append(ValidationIssue(
                field='institution_type',
                message='Institution type is required',
                severity=ValidationSeverity.ERROR
            ))
        elif inst.institution_type.lower() not in self.VALID_TYPES:
            issues.append(ValidationIssue(
                field='institution_type',
                message=f'Unknown institution type: {inst.institution_type}',
                severity=ValidationSeverity.WARNING,
                value=inst.institution_type
            ))
        
        return issues
    
    def _validate_location(self, inst: ScrapedInstitution) -> List[ValidationIssue]:
        """Validate location data."""
        issues = []
        
        if not inst.division:
            issues.append(ValidationIssue(
                field='division',
                message='Division is missing - will default to Dhaka',
                severity=ValidationSeverity.WARNING
            ))
        elif inst.division.lower() not in self.VALID_DIVISIONS:
            issues.append(ValidationIssue(
                field='division',
                message=f'Potentially invalid division: {inst.division}',
                severity=ValidationSeverity.WARNING,
                value=inst.division
            ))
        
        # Check address quality
        if inst.address and len(inst.address) < 10:
            issues.append(ValidationIssue(
                field='address',
                message='Address seems too short to be useful',
                severity=ValidationSeverity.INFO,
                value=inst.address
            ))
        
        return issues
    
    def _validate_contact(self, inst: ScrapedInstitution) -> List[ValidationIssue]:
        """Validate contact information."""
        issues = []
        
        # Validate phone format
        if inst.phone:
            # Bangladesh phone pattern
            bd_pattern = r'^(\+?880|0)1[3-9]\d{8}$'
            clean_phone = inst.phone.replace(' ', '').replace('-', '')
            if not re.match(bd_pattern, clean_phone):
                issues.append(ValidationIssue(
                    field='phone',
                    message='Phone number format may be invalid for Bangladesh',
                    severity=ValidationSeverity.WARNING,
                    value=inst.phone
                ))
        
        # Validate email format
        if inst.email:
            email_pattern = r'^[\w.-]+@[\w.-]+\.\w+$'
            if not re.match(email_pattern, inst.email):
                issues.append(ValidationIssue(
                    field='email',
                    message='Email format appears invalid',
                    severity=ValidationSeverity.WARNING,
                    value=inst.email
                ))
        
        # Check website
        if inst.website:
            if not inst.website.startswith(('http://', 'https://')):
                issues.append(ValidationIssue(
                    field='website',
                    message='Website URL should include http:// or https://',
                    severity=ValidationSeverity.INFO,
                    value=inst.website
                ))
        
        # Warn if no contact info
        if not inst.phone and not inst.email and not inst.website:
            issues.append(ValidationIssue(
                field='contact',
                message='No contact information provided',
                severity=ValidationSeverity.WARNING
            ))
        
        return issues
    
    def _validate_year(self, inst: ScrapedInstitution) -> List[ValidationIssue]:
        """Validate established year."""
        issues = []
        
        if inst.established_year:
            current_year = 2024
            
            if inst.established_year < 1800:
                issues.append(ValidationIssue(
                    field='established_year',
                    message='Established year seems too old (before 1800)',
                    severity=ValidationSeverity.WARNING,
                    value=inst.established_year
                ))
            elif inst.established_year > current_year:
                issues.append(ValidationIssue(
                    field='established_year',
                    message=f'Established year is in the future (after {current_year})',
                    severity=ValidationSeverity.ERROR,
                    value=inst.established_year
                ))
        
        return issues
    
    def validate_batch(self, institutions: List[ScrapedInstitution]) -> Dict[str, Any]:
        """Validate a batch of institutions and return summary."""
        results = {
            'total': len(institutions),
            'valid': 0,
            'with_warnings': 0,
            'invalid': 0,
            'issues_by_field': {},
            'details': []
        }
        
        for inst in institutions:
            issues = self.validate(inst)
            
            has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
            has_warnings = any(i.severity == ValidationSeverity.WARNING for i in issues)
            
            if has_errors:
                results['invalid'] += 1
            elif has_warnings:
                results['with_warnings'] += 1
            else:
                results['valid'] += 1
            
            # Track issues by field
            for issue in issues:
                field = issue.field
                if field not in results['issues_by_field']:
                    results['issues_by_field'][field] = {'errors': 0, 'warnings': 0, 'info': 0}
                results['issues_by_field'][field][issue.severity.value] += 1
            
            # Store details for first 10
            if len(results['details']) < 10:
                results['details'].append({
                    'name': inst.name_en,
                    'issues': [
                        {
                            'field': i.field,
                            'message': i.message,
                            'severity': i.severity.value
                        }
                        for i in issues
                    ]
                })
        
        return results


class DuplicateDetector:
    """Detect potential duplicates in scraped data."""
    
    def find_duplicates(self, institutions: List[ScrapedInstitution]) -> List[Dict[str, Any]]:
        """Find potential duplicate institutions."""
        seen_names: Dict[str, List[ScrapedInstitution]] = {}
        duplicates = []
        
        # Group by normalized name
        for inst in institutions:
            # Normalize name for comparison
            normalized = self._normalize_name(inst.name_en)
            
            if normalized in seen_names:
                seen_names[normalized].append(inst)
            else:
                seen_names[normalized] = [inst]
        
        # Find duplicates
        for normalized, group in seen_names.items():
            if len(group) > 1:
                duplicates.append({
                    'normalized_name': normalized,
                    'count': len(group),
                    'institutions': [
                        {
                            'name': i.name_en,
                            'district': i.district,
                            'source': i.data_source
                        }
                        for i in group
                    ],
                    'suggestion': 'Review and merge if same institution'
                })
        
        return duplicates
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for duplicate detection."""
        # Lowercase, remove common suffixes, normalize whitespace
        name = name.lower()
        
        # Remove common suffixes/prefixes
        suffixes = [
            ' college', ' university', ' school', ' institute',
            ' polytechnic', ' madrasa', ' academy'
        ]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        # Remove special characters and normalize
        import re
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())  # Normalize whitespace
        
        return name.strip()
