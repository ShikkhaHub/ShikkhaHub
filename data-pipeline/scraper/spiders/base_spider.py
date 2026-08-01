"""
Base spider class for all ShikkhaHub scrapers
Handles common functionality: logging, error handling, data normalization
"""

import scrapy
import logging
from datetime import datetime
from typing import Dict, Any, List
import re
from urllib.parse import urljoin


class BaseInstitutionSpider(scrapy.Spider):
    """
    Base class for institution scraping.
    All institution scrapers should inherit from this.
    """
    
    # Override in subclasses
    name = 'base_spider'
    allowed_domains = []
    start_urls = []
    source_type = 'web'  # government, board, directory, social, etc
    tier = 2  # 1 (high trust), 2 (medium), 3 (low)
    trust_score = 0.5  # 0-1.0
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.name)
        self.scrape_start_time = datetime.utcnow()
        self.stats = {
            'total_items': 0,
            'valid_items': 0,
            'skipped': 0,
            'errors': 0,
        }
    
    def start_requests(self):
        """Generate initial requests"""
        for url in self.start_urls:
            self.logger.info(f'Starting scrape: {url}')
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    'source_type': self.source_type,
                    'tier': self.tier,
                    'trust_score': self.trust_score,
                    'source_url': url,
                }
            )
    
    def parse(self, response):
        """Override in subclass"""
        raise NotImplementedError('Subclasses must implement parse()')
    
    def closed(self, reason):
        """Called when spider is closed"""
        elapsed = (datetime.utcnow() - self.scrape_start_time).total_seconds()
        self.logger.info(f'Spider closed: {reason}')
        self.logger.info(f'Stats: {self.stats}')
        self.logger.info(f'Time elapsed: {elapsed} seconds')
    
    # ============ UTILITY METHODS ============
    
    def normalize_institution_name(self, name: str) -> str:
        """
        Normalize institution name.
        Example: "Dhaka Govt College" -> "Dhaka Government College"
        """
        if not name:
            return ''
        
        name = name.strip()
        # Remove extra whitespace
        name = ' '.join(name.split())
        # Normalize common abbreviations
        replacements = {
            r'\bGovt\.?\b': 'Government',
            r'\bUniv\.?\b': 'University',
            r'\bColl\.?\b': 'College',
            r'\bInst\.?\b': 'Institute',
            r'\bTech\.?\b': 'Technical',
            r'\bPolytech\.?\b': 'Polytechnic',
        }
        for pattern, replacement in replacements.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        
        return name.title()
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to +880 format"""
        if not phone:
            return ''
        
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:  # Local format (0XXXXXXXXX)
            digits = '880' + digits[1:]
        elif len(digits) == 11 and digits.startswith('0'):
            digits = '880' + digits[1:]
        elif len(digits) == 11 and digits.startswith('88'):
            # Already in 880 format
            pass
        elif len(digits) == 12 and digits.startswith('880'):
            # Already in +880 format
            pass
        
        return f'+{digits}' if digits else ''
    
    def normalize_email(self, email: str) -> str:
        """Validate and normalize email"""
        if not email:
            return ''
        
        email = email.strip().lower()
        # Simple email validation
        if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return email
        
        return ''
    
    def normalize_address(self, address: str) -> str:
        """Clean and normalize address"""
        if not address:
            return ''
        
        address = address.strip()
        address = ' '.join(address.split())  # Remove extra whitespace
        return address
    
    def extract_text(self, selector, xpath: str, default: str = '') -> str:
        """
        Extract text from selector using XPath.
        Handles multiple elements and joins them.
        """
        texts = selector.xpath(xpath).getall()
        if texts:
            return ' '.join(text.strip() for text in texts if text.strip())
        return default
    
    def create_raw_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a raw data item for storage.
        This gets stored in raw_data table.
        """
        return {
            'source_type': self.source_type,
            'tier': self.tier,
            'trust_score': self.trust_score,
            'raw_json': data,
            'scrape_timestamp': datetime.utcnow().isoformat(),
            'status': 'pending',
        }
    
    def create_institution_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a normalized institution item.
        Maps scraped data to institution model fields.
        """
        item = {
            'name_en': self.normalize_institution_name(data.get('name', '')),
            'name_bn': data.get('name_bn', ''),
            'type': data.get('type', ''),
            'address': self.normalize_address(data.get('address', '')),
            'phone': self.normalize_phone(data.get('phone', '')),
            'email': self.normalize_email(data.get('email', '')),
            'website': data.get('website', ''),
            'district': data.get('district', ''),
            'upazila': data.get('upazila', ''),
            'division': data.get('division', ''),
            'established_year': data.get('established_year'),
            'description': data.get('description', ''),
            'coordinates': data.get('coordinates', {}),
            'source_type': self.source_type,
            'source_url': data.get('source_url', ''),
            'metadata': {
                'tier': self.tier,
                'trust_score': self.trust_score,
                'scraped_at': datetime.utcnow().isoformat(),
            }
        }
        
        self.stats['valid_items'] += 1
        return item
    
    def log_error(self, message: str, error: Exception = None):
        """Log error with context"""
        self.stats['errors'] += 1
        if error:
            self.logger.error(f'{message}: {str(error)}')
        else:
            self.logger.error(message)


class GovernmentSourceSpider(BaseInstitutionSpider):
    """
    Base for government-sourced spiders (UGC, Boards, etc).
    These are Tier 1 (high trust) sources.
    """
    
    source_type = 'government'
    tier = 1
    trust_score = 0.95  # Very high trust for official sources
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.info(f'Government source spider initialized: {self.name}')
        self.logger.info(f'Trust score: {self.trust_score}')
