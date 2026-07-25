"""
Base scraper class for ShikkhaHub data collection.
Provides common HTTP handling, retry logic, SSL workarounds, and data validation.
"""

import logging
import time
import random
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime
from abc import ABC, abstractmethod
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
from fake_useragent import UserAgent
import urllib3

# Suppress SSL warnings for problematic government sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapedInstitution:
    """Standardized data structure for scraped institutions."""
    # Identification
    name_en: str
    name_bn: Optional[str] = None
    short_name: Optional[str] = None
    
    # Type & Classification
    institution_type: str = "unknown"  # university, college, polytechnic, school, madrasa
    
    # Location
    division: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None
    address: Optional[str] = None
    
    # Contact
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    # Academic
    established_year: Optional[int] = None
    education_level: Optional[str] = None  # primary, secondary, higher_secondary, undergraduate, graduate
    
    # Affiliations
    education_board: Optional[str] = None
    university_affiliation: Optional[str] = None
    ugc_approved: bool = False
    
    # Metadata
    data_source: str = ""
    source_url: Optional[str] = None
    raw_data: Optional[Dict] = None
    
    # Quality tracking
    confidence_score: float = 0.0  # 0-1 based on data completeness
    scraped_at: str = ""
    
    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.utcnow().isoformat()
        self._calculate_confidence()
    
    def _calculate_confidence(self):
        """Calculate confidence score based on data completeness."""
        required_fields = [self.name_en, self.institution_type, self.division]
        optional_fields = [
            self.district, self.upazila, self.address,
            self.phone, self.email, self.website,
            self.established_year
        ]
        
        score = sum(1 for f in required_fields if f) * 0.4  # 40% weight
        score += sum(0.5 for f in optional_fields if f) * 0.075  # 60% weight distributed
        self.confidence_score = min(score, 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ScraperHealth:
    """Health status for scraper monitoring."""
    
    def __init__(self):
        self.is_healthy: bool = True
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.error_count: int = 0
        self.consecutive_errors: int = 0
        self.total_errors: int = 0
        
    def record_success(self):
        self.is_healthy = True
        self.last_success = datetime.utcnow()
        self.consecutive_errors = 0
        
    def record_error(self, error: str):
        self.last_error = error
        self.error_count += 1
        self.consecutive_errors += 1
        self.total_errors += 1
        # Mark unhealthy after 3 consecutive errors
        if self.consecutive_errors >= 3:
            self.is_healthy = False
            
    def get_status(self) -> Dict[str, Any]:
        return {
            'is_healthy': self.is_healthy,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_error': self.last_error,
            'consecutive_errors': self.consecutive_errors,
            'total_errors': self.total_errors,
        }


class BaseScraper(ABC):
    """Abstract base class for all education data scrapers.
    
    Features:
    - SSL certificate bypass for problematic government sites
    - Adaptive retry logic with exponential backoff
    - Health monitoring and status tracking
    - 404 detection and graceful handling
    - Rate limiting and polite crawling
    """
    
    def __init__(
        self, 
        source_name: str, 
        delay_range: tuple = (1, 3),
        verify_ssl: bool = True,
        max_retries: int = 5,
        timeout: int = 30
    ):
        self.source_name = source_name
        self.delay_range = delay_range
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.timeout = timeout
        self.ua = UserAgent()
        self.health = ScraperHealth()
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
        })
        self.stats = {
            'requests': 0,
            'success': 0,
            'failed': 0,
            'items_scraped': 0,
            'ssl_bypassed': 0,
            'errors_404': 0,
            'errors_timeout': 0,
        }
    
    def _get_headers(self) -> Dict[str, str]:
        """Get randomized headers for each request."""
        return {
            'User-Agent': self.ua.random,
            'Referer': 'https://www.google.com/'
        }
    
    def _fetch(
        self, 
        url: str, 
        bypass_ssl: bool = False,
        allow_404: bool = False,
        **kwargs
    ) -> requests.Response:
        """Fetch URL with SSL bypass, 404 handling, and retry logic.
        
        Args:
            url: URL to fetch
            bypass_ssl: If True, skip SSL verification (for problematic government sites)
            allow_404: If True, don't raise error on 404 (return None instead)
            **kwargs: Additional requests parameters
        
        Returns:
            Response object or None if 404 and allow_404=True
        """
        # Rate limiting
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        
        headers = {**self._get_headers(), **kwargs.pop('headers', {})}
        verify = kwargs.pop('verify', self.verify_ssl and not bypass_ssl)
        
        self.stats['requests'] += 1
        logger.info(f"[{self.source_name}] Fetching: {url} (SSL verify: {verify})")
        
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(
                    url, 
                    headers=headers, 
                    timeout=self.timeout, 
                    verify=verify,
                    **kwargs
                )
                
                # Handle 404
                if response.status_code == 404:
                    self.stats['errors_404'] += 1
                    self.health.record_error(f"404 Not Found: {url}")
                    if allow_404:
                        logger.warning(f"[{self.source_name}] 404 (allowed): {url}")
                        return response
                    raise requests.HTTPError(f"404 Not Found: {url}")
                
                # Handle other errors
                response.raise_for_status()
                
                # Success
                self.stats['success'] += 1
                self.health.record_success()
                
                if not verify:
                    self.stats['ssl_bypassed'] += 1
                    
                return response
                
            except requests.exceptions.SSLError as e:
                last_error = f"SSL Error: {str(e)}"
                if not verify:
                    # Already bypassing SSL, this shouldn't happen
                    logger.error(f"[{self.source_name}] SSL error even with bypass: {url}")
                    raise
                    
                # Try with SSL bypass on next attempt
                logger.warning(f"[{self.source_name}] SSL error, will retry with bypass: {url}")
                verify = False
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.Timeout as e:
                last_error = f"Timeout: {str(e)}"
                self.stats['errors_timeout'] += 1
                logger.warning(f"[{self.source_name}] Timeout (attempt {attempt}): {url}")
                time.sleep(2 ** attempt)
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection Error: {str(e)}"
                logger.warning(f"[{self.source_name}] Connection error (attempt {attempt}): {url}")
                time.sleep(2 ** attempt)
                
            except requests.HTTPError as e:
                if response.status_code in [429, 500, 502, 503, 504]:
                    last_error = f"HTTP {response.status_code}: {str(e)}"
                    logger.warning(f"[{self.source_name}] HTTP {response.status_code} (attempt {attempt}): {url}")
                    time.sleep(2 ** attempt)
                else:
                    raise
                    
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(f"[{self.source_name}] Unexpected error: {url} - {e}")
                raise
        
        # All retries exhausted
        self.stats['failed'] += 1
        self.health.record_error(last_error or "Max retries exceeded")
        raise requests.RequestError(f"Max retries exceeded for {url}: {last_error}")
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup."""
        return BeautifulSoup(html, 'lxml')
    
    def _normalize_phone(self, phone: Optional[str]) -> Optional[str]:
        """Normalize Bangladesh phone numbers."""
        if not phone:
            return None
        # Remove all non-digit characters
        digits = ''.join(c for c in phone if c.isdigit())
        # Add country code if missing
        if digits.startswith('0'):
            digits = '+880' + digits[1:]
        elif digits.startswith('1'):
            digits = '+880' + digits
        return digits if len(digits) >= 13 else phone
    
    def _extract_year(self, text: Optional[str]) -> Optional[int]:
        """Extract 4-digit year from text."""
        if not text:
            return None
        import re
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group()) if match else None
    
    def _slugify_name(self, name: str) -> str:
        """Create URL-friendly slug from institution name."""
        from slugify import slugify
        return slugify(name, max_length=100)
    
    @abstractmethod
    def scrape(self) -> List[ScrapedInstitution]:
        """Main scraping method - must be implemented by subclasses."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraping statistics with health status."""
        return {
            **self.stats,
            'health': self.health.get_status(),
            'success_rate': self._calculate_success_rate(),
        }
    
    def _calculate_success_rate(self) -> float:
        """Calculate request success rate."""
        if self.stats['requests'] == 0:
            return 0.0
        return round(self.stats['success'] / self.stats['requests'], 4)
    
    def check_health(self) -> bool:
        """Check if scraper is healthy."""
        return self.health.is_healthy
    
    def save_raw(self, data: Any, filename: str):
        """Save raw scraped data to file."""
        import os
        filepath = f"data/raw/{self.source_name}_{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"[{self.source_name}] Raw data saved: {filepath}")
