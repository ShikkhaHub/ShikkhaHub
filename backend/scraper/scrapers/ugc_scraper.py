"""
University Grants Commission of Bangladesh Scraper.
Extracts university data from ugc.gov.bd
"""

import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from scraper.base import BaseScraper, ScrapedInstitution

logger = logging.getLogger(__name__)


class UGCScraper(BaseScraper):
    """Scraper for UGC Bangladesh university listings."""
    
    BASE_URL = "https://www.ugc.gov.bd"
    UNIVERSITY_LIST_URL = "https://www.ugc.gov.bd/en/home/universityDetails/public"
    
    # Known university types on UGC site
    UNIVERSITY_TYPES = {
        'public': 'public_university',
        'private': 'private_university',
        'international': 'international_university',
        'specialized': 'specialized_university'
    }
    
    def __init__(self):
        super().__init__(source_name="ugc_gov_bd", delay_range=(2, 4))
    
    def _extract_university_list(self, html: str) -> List[dict]:
        """Extract university list from UGC page."""
        soup = self._parse_html(html)
        universities = []
        
        # Look for university links/tables
        # UGC typically has tables or lists with university names
        tables = soup.find_all('table', class_='table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name_cell = cells[0]
                    link = name_cell.find('a')
                    
                    uni_data = {
                        'name': name_cell.get_text(strip=True),
                        'url': self.BASE_URL + link['href'] if link and link.get('href') else None,
                        'type': self._detect_university_type(name_cell.get_text())
                    }
                    universities.append(uni_data)
        
        # Also check for list items
        if not universities:
            list_items = soup.select('.university-list li, .content-area li')
            for item in list_items:
                link = item.find('a')
                if link:
                    universities.append({
                        'name': link.get_text(strip=True),
                        'url': self.BASE_URL + link['href'] if link.get('href').startswith('/') else link['href'],
                        'type': 'unknown'
                    })
        
        return universities
    
    def _detect_university_type(self, name: str) -> str:
        """Detect university type from name."""
        name_lower = name.lower()
        if 'private' in name_lower:
            return 'private_university'
        elif any(x in name_lower for x in ['medical', 'agricultural', 'engineering']):
            return 'specialized_university'
        elif 'international' in name_lower:
            return 'international_university'
        return 'public_university'
    
    def _extract_university_details(self, html: str, url: str) -> Optional[ScrapedInstitution]:
        """Extract detailed information from a university page."""
        soup = self._parse_html(html)
        
        # Try to find university name
        name = None
        title_elem = soup.find('h1') or soup.find('h2') or soup.find('h3', class_='title')
        if title_elem:
            name = title_elem.get_text(strip=True)
        
        if not name:
            return None
        
        # Extract contact info from page text
        text = soup.get_text()
        
        # Find phone patterns
        import re
        phone_match = re.search(r'(?:\+?880|0)1[3-9]\d{8}', text)
        phone = phone_match.group() if phone_match else None
        
        # Find email
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        email = email_match.group() if email_match else None
        
        # Find website
        website_match = re.search(r'https?://(?:www\.)?[\w.-]+\.(?:edu\.bd|ac\.bd|com|org)', text)
        website = website_match.group() if website_match else None
        
        # Find address indicators
        address_indicators = ['address', 'location', 'campus', 'road', 'dhaka', 'chittagong']
        address = None
        for p in soup.find_all('p'):
            p_text = p.get_text().lower()
            if any(ind in p_text for ind in address_indicators):
                address = p.get_text(strip=True)
                break
        
        # Extract year
        year = self._extract_year(text)
        
        # Detect location
        division = self._detect_division(text)
        district = self._detect_district(text, division)
        
        return ScrapedInstitution(
            name_en=name,
            institution_type='university',
            division=division,
            district=district,
            address=address,
            phone=self._normalize_phone(phone),
            email=email,
            website=website,
            established_year=year,
            ugc_approved=True,
            data_source='ugc.gov.bd',
            source_url=url
        )
    
    def _detect_division(self, text: str) -> Optional[str]:
        """Detect division from address text."""
        divisions = ['dhaka', 'chittagong', 'rajshahi', 'khulna', 'barisal', 'sylhet', 'rangpur', 'mymensingh']
        text_lower = text.lower()
        for div in divisions:
            if div in text_lower:
                return div.title()
        return 'Dhaka'  # Default
    
    def _detect_district(self, text: str, division: Optional[str]) -> Optional[str]:
        """Detect district from text based on known districts."""
        # Major districts by division
        districts_map = {
            'Dhaka': ['dhaka', 'gazipur', 'narayanganj', 'tangail', 'manikganj', 'munshiganj'],
            'Chittagong': ['chittagong', 'cox\'s bazar', 'comilla', 'feni', 'noakhali'],
            'Rajshahi': ['rajshahi', 'bogura', 'pabna', 'natore', 'naogaon'],
            'Khulna': ['khulna', 'jessore', 'satkhira', 'bagerhat', 'kushtia'],
        }
        
        text_lower = text.lower()
        districts = districts_map.get(division, [])
        for dist in districts:
            if dist in text_lower:
                return dist.title()
        return None
    
    def scrape(self) -> List[ScrapedInstitution]:
        """Main scraping method for UGC universities."""
        institutions = []
        
        try:
            logger.info(f"[{self.source_name}] Starting UGC university scrape...")
            
            # Fetch public universities list
            response = self._fetch(self.UNIVERSITY_LIST_URL)
            uni_list = self._extract_university_list(response.text)
            
            logger.info(f"[{self.source_name}] Found {len(uni_list)} universities in list")
            
            # Fetch details for each university (limit to avoid overwhelming server)
            for i, uni in enumerate(uni_list[:50]):  # Limit to 50 for initial run
                try:
                    if uni.get('url'):
                        detail_response = self._fetch(uni['url'])
                        institution = self._extract_university_details(
                            detail_response.text, 
                            uni['url']
                        )
                        if institution:
                            institution.name_en = uni['name']  # Override with official name
                            institutions.append(institution)
                            self.stats['items_scraped'] += 1
                            
                            if (i + 1) % 10 == 0:
                                logger.info(f"[{self.source_name}] Processed {i+1}/{len(uni_list)} universities")
                except Exception as e:
                    logger.error(f"[{self.source_name}] Error scraping {uni.get('name')}: {e}")
                    continue
            
            # Save raw data
            self.save_raw([i.to_dict() for i in institutions], "universities")
            
            logger.info(f"[{self.source_name}] Scraped {len(institutions)} universities")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
        
        return institutions
