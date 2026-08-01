"""
Data Processor - Cleaner, Validator, and Deduplicator
Converts raw scraped data into clean, normalized, deduplicated institution records
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher
import re
from datetime import datetime


class DataProcessor:
    """
    Main data processor.
    Cleans, validates, and deduplicates institution data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processed_count = 0
        self.error_count = 0
    
    def process(self, raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Full processing pipeline for a raw scraped item.
        Returns cleaned item or None if invalid.
        """
        try:
            # Step 1: Clean and normalize
            cleaned = self.clean_item(raw_item)
            
            # Step 2: Validate
            if not self.validate_item(cleaned):
                self.logger.warning(f'Item failed validation: {raw_item.get("name")}')
                self.error_count += 1
                return None
            
            # Step 3: Enrich
            enriched = self.enrich_item(cleaned)
            
            self.processed_count += 1
            return enriched
            
        except Exception as e:
            self.logger.error(f'Error processing item: {str(e)}')
            self.error_count += 1
            return None
    
    def clean_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize all fields"""
        cleaned = {}
        
        # Essential fields
        cleaned['name'] = self.clean_text(item.get('name_en', ''))
        cleaned['name_bn'] = self.clean_text(item.get('name_bn', ''))
        cleaned['type'] = self.clean_institution_type(item.get('type', ''))
        
        # Contact info
        cleaned['email'] = self.clean_email(item.get('email', ''))
        cleaned['phone'] = self.clean_phone(item.get('phone', ''))
        cleaned['website'] = self.clean_url(item.get('website', ''))
        
        # Location
        cleaned['address'] = self.clean_text(item.get('address', ''))
        cleaned['district'] = self.clean_location(item.get('district', ''))
        cleaned['upazila'] = self.clean_location(item.get('upazila', ''))
        cleaned['division'] = self.clean_location(item.get('division', ''))
        
        # Coordinates
        if isinstance(item.get('coordinates'), dict):
            cleaned['latitude'] = self.clean_float(item['coordinates'].get('latitude'))
            cleaned['longitude'] = self.clean_float(item['coordinates'].get('longitude'))
        
        # Additional info
        cleaned['established_year'] = self.clean_year(item.get('established_year'))
        cleaned['description'] = self.clean_text(item.get('description', ''), max_length=1000)
        
        # Metadata
        cleaned['source_type'] = item.get('source_type', 'web')
        cleaned['source_url'] = item.get('source_url', '')
        cleaned['tier'] = item.get('tier', 2)
        cleaned['trust_score'] = item.get('trust_score', 0.5)
        cleaned['scraped_at'] = item.get('scrape_timestamp', datetime.utcnow().isoformat())
        
        return cleaned
    
    def validate_item(self, item: Dict[str, Any]) -> bool:
        """Validate that item has required fields"""
        required = ['name', 'type']
        
        for field in required:
            if not item.get(field):
                self.logger.warning(f'Missing required field: {field}')
                return False
        
        # Name must be reasonable length
        if len(item['name']) < 3:
            return False
        
        # Type must be recognized
        valid_types = ['school', 'college', 'university', 'polytechnic', 'institute', 'vocational']
        if item['type'].lower() not in valid_types:
            self.logger.warning(f'Invalid institution type: {item["type"]}')
            return False
        
        return True
    
    def enrich_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Add computed fields"""
        # Calculate completeness score
        total_fields = len([v for v in item.values() if v])
        item['completeness_score'] = total_fields / len(item)
        
        # Create slug for URL
        item['slug'] = self.create_slug(item['name'])
        
        # Normalize institution name for matching
        item['name_normalized'] = self.normalize_name_for_matching(item['name'])
        
        return item
    
    # ============ CLEANING METHODS ============
    
    def clean_text(self, text: str, max_length: int = None) -> str:
        """Clean and normalize text"""
        if not text:
            return ''
        
        text = str(text).strip()
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Remove special characters (keep alphanumeric, spaces, hyphens)
        text = re.sub(r'[^\w\s\-&(),.\'"]', '', text)
        
        if max_length and len(text) > max_length:
            text = text[:max_length].rstrip()
        
        return text
    
    def clean_email(self, email: str) -> str:
        """Clean and validate email"""
        if not email:
            return ''
        
        email = email.strip().lower()
        # Remove common noise
        email = email.replace('mailto:', '')
        
        # Basic email validation
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return email
        
        return ''
    
    def clean_phone(self, phone: str) -> str:
        """Clean and normalize phone number"""
        if not phone:
            return ''
        
        # Extract digits
        digits = re.sub(r'\D', '', str(phone))
        
        # Handle different formats
        if len(digits) == 10:  # Local (0XXXXXXXXX)
            digits = '880' + digits[1:]
        elif len(digits) == 11 and digits.startswith('0'):
            digits = '880' + digits[1:]
        elif len(digits) == 11:  # Might be 88XXXXXXXXX
            if not digits.startswith('88'):
                return ''
        elif len(digits) == 12 and digits.startswith('880'):
            pass
        else:
            return ''
        
        return f'+{digits}'
    
    def clean_url(self, url: str) -> str:
        """Clean and validate URL"""
        if not url:
            return ''
        
        url = url.strip()
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Basic URL validation
        if re.match(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', url):
            return url
        
        return ''
    
    def clean_location(self, location: str) -> str:
        """Clean location (district, upazila, division)"""
        if not location:
            return ''
        
        location = self.clean_text(location)
        
        # Normalize common variations
        location_map = {
            'dhaka': 'Dhaka',
            'chattogram': 'Chattogram',
            'khulna': 'Khulna',
            'rajshahi': 'Rajshahi',
            'barisal': 'Barisal',
            'sylhet': 'Sylhet',
            'rangpur': 'Rangpur',
            'mymensingh': 'Mymensingh',
        }
        
        return location_map.get(location.lower(), location)
    
    def clean_float(self, value) -> Optional[float]:
        """Clean and validate float (for coordinates)"""
        try:
            val = float(value)
            # Lat/long should be within reasonable Bangladesh bounds
            if -90 <= val <= 90:
                return round(val, 6)
        except (ValueError, TypeError):
            pass
        return None
    
    def clean_year(self, year) -> Optional[int]:
        """Clean and validate year"""
        try:
            year_int = int(year)
            if 1800 <= year_int <= datetime.now().year:
                return year_int
        except (ValueError, TypeError):
            pass
        return None
    
    def clean_institution_type(self, inst_type: str) -> str:
        """Normalize institution type"""
        if not inst_type:
            return 'institute'
        
        inst_type = inst_type.lower()
        
        type_map = {
            'university': 'university',
            'uni': 'university',
            'college': 'college',
            'govt college': 'college',
            'private college': 'college',
            'school': 'school',
            'high school': 'school',
            'secondary school': 'school',
            'polytechnic': 'polytechnic',
            'polytec': 'polytechnic',
            'institute': 'institute',
            'vocational': 'vocational',
            'training': 'vocational',
            'technical': 'polytechnic',
        }
        
        for key, val in type_map.items():
            if key in inst_type:
                return val
        
        return 'institute'
    
    def create_slug(self, name: str) -> str:
        """Create URL-friendly slug"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    def normalize_name_for_matching(self, name: str) -> str:
        """Normalize name for deduplication matching"""
        name = name.lower()
        # Remove common words
        stop_words = ['govt', 'government', 'college', 'university', 'institute', 'school', 'the']
        for word in stop_words:
            name = re.sub(f'\\b{word}\\b', '', name)
        # Remove special characters
        name = re.sub(r'[^a-z0-9\s]', '', name)
        # Remove extra whitespace
        name = ' '.join(name.split())
        return name


class Deduplicator:
    """
    Deduplication engine - identifies and merges duplicate institutions
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.logger = logging.getLogger(__name__)
        self.similarity_threshold = similarity_threshold
        self.candidates_found = 0
    
    def find_duplicates(self, items: List[Dict[str, Any]]) -> List[Tuple[int, int, float]]:
        """
        Find potential duplicate pairs in a list of items.
        Returns: [(idx1, idx2, similarity_score), ...]
        """
        duplicates = []
        
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                similarity = self.calculate_similarity(items[i], items[j])
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
                    self.candidates_found += 1
                    self.logger.info(
                        f'Duplicate candidate found: '
                        f'{items[i]["name"]} vs {items[j]["name"]} '
                        f'(score: {similarity:.2f})'
                    )
        
        return duplicates
    
    def calculate_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """Calculate similarity score between two items (0-1.0)"""
        scores = []
        
        # Name similarity (weighted 40%)
        name_sim = self.string_similarity(
            item1.get('name_normalized', ''),
            item2.get('name_normalized', '')
        )
        scores.append(('name', name_sim, 0.4))
        
        # Phone match (weighted 30%)
        phone_match = float(
            item1.get('phone') and 
            item1.get('phone') == item2.get('phone')
        )
        scores.append(('phone', phone_match, 0.3))
        
        # Email match (weighted 20%)
        email_match = float(
            item1.get('email') and 
            item1.get('email') == item2.get('email')
        )
        scores.append(('email', email_match, 0.2))
        
        # Location match (weighted 10%)
        location_match = float(
            item1.get('district') == item2.get('district') and
            item1.get('district')
        )
        scores.append(('location', location_match, 0.1))
        
        # Calculate weighted score
        total_score = sum(score * weight for _, score, weight in scores)
        
        return total_score
    
    def string_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity using SequenceMatcher"""
        if not s1 or not s2:
            return 0.0
        
        return SequenceMatcher(None, s1, s2).ratio()
