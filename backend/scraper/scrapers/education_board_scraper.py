"""
Education Board Scrapers for Bangladesh.
Covers: BMEB (Madrasah), BTEB (Technical), and General Education Boards.
"""

import logging
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from scraper.base import BaseScraper, ScrapedInstitution

logger = logging.getLogger(__name__)


class BMEBScraper(BaseScraper):
    """
    Bangladesh Madrasah Education Board Scraper.
    Source: bmeb.gov.bd
    """
    
    BASE_URL = "https://bmeb.gov.bd"
    MADRASA_LIST_URL = "https://bmeb.gov.bd/site/page/f041f3d6-c5e8-4f6a-9f5a-8e9c5b5a5f2e/"
    
    def __init__(self):
        super().__init__(source_name="bmeb_gov_bd", delay_range=(2, 4))
    
    def _extract_madrasa_list(self, html: str) -> List[Dict]:
        """Extract madrasa list from BMEB page."""
        soup = self._parse_html(html)
        madrasas = []
        
        # Look for tables or lists containing institution names
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    madrasa = {
                        'name': cells[0].get_text(strip=True),
                        'eiin': cells[1].get_text(strip=True) if len(cells) > 1 else None,
                        'type': self._detect_madrasa_type(cells[0].get_text()),
                        'district': cells[2].get_text(strip=True) if len(cells) > 2 else None
                    }
                    madrasas.append(madrasa)
        
        # Also check for list elements
        if not madrasas:
            for li in soup.find_all('li'):
                text = li.get_text(strip=True)
                if any(keyword in text.lower() for keyword in ['madrasa', 'qawmi', 'alia']):
                    madrasas.append({
                        'name': text,
                        'eiin': None,
                        'type': 'unknown',
                        'district': None
                    })
        
        return madrasas
    
    def _detect_madrasa_type(self, name: str) -> str:
        """Detect madrasa type from name."""
        name_lower = name.lower()
        if 'qawmi' in name_lower:
            return 'qawmi_madrasa'
        elif 'alia' in name_lower or 'kamil' in name_lower or 'fazil' in name_lower:
            return 'alia_madrasa'
        elif 'hifz' in name_lower or 'tahfiz' in name_lower:
            return 'hifz_madrasa'
        return 'general_madrasa'
    
    def scrape(self) -> List[ScrapedInstitution]:
        """Scrape BMEB madrasa data."""
        institutions = []
        
        try:
            logger.info(f"[{self.source_name}] Starting BMEB madrasa scrape...")
            
            response = self._fetch(self.MADRASA_LIST_URL)
            madrasa_list = self._extract_madrasa_list(response.text)
            
            logger.info(f"[{self.source_name}] Found {len(madrasa_list)} madrasas")
            
            for madrasa_data in madrasa_list[:100]:  # Limit for initial run
                try:
                    institution = ScrapedInstitution(
                        name_en=madrasa_data['name'],
                        institution_type='madrasa',
                        district=madrasa_data.get('district'),
                        education_level='secondary',
                        education_board='BMEB',
                        data_source='bmeb.gov.bd',
                        source_url=self.MADRASA_LIST_URL
                    )
                    institutions.append(institution)
                    self.stats['items_scraped'] += 1
                    
                except Exception as e:
                    logger.error(f"[{self.source_name}] Error processing madrasa: {e}")
                    continue
            
            self.save_raw([i.to_dict() for i in institutions], "madrasas")
            logger.info(f"[{self.source_name}] Scraped {len(institutions)} madrasas")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
        
        return institutions


class BTEBScraper(BaseScraper):
    """
    Bangladesh Technical Education Board Scraper.
    Source: bteb.gov.bd
    """
    
    BASE_URL = "https://www.bteb.gov.bd"
    INSTITUTE_LIST_URL = "https://www.bteb.gov.bd/site/view/institutes/"
    
    def __init__(self):
        super().__init__(source_name="bteb_gov_bd", delay_range=(2, 4))
    
    def _extract_institute_list(self, html: str) -> List[Dict]:
        """Extract technical institute list from BTEB page."""
        soup = self._parse_html(html)
        institutes = []
        
        # Look for tables with institute data
        tables = soup.find_all('table', {'class': ['table', 'data-table']})
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    institute = {
                        'name': cells[0].get_text(strip=True),
                        'code': cells[1].get_text(strip=True) if len(cells) > 1 else None,
                        'district': cells[2].get_text(strip=True) if len(cells) > 2 else None,
                        'type': self._detect_institute_type(cells[0].get_text())
                    }
                    institutes.append(institute)
        
        return institutes
    
    def _detect_institute_type(self, name: str) -> str:
        """Detect institute type from name."""
        name_lower = name.lower()
        if 'polytechnic' in name_lower:
            return 'polytechnic'
        elif 'technical' in name_lower and 'school' in name_lower:
            return 'technical_school'
        elif 'vocational' in name_lower:
            return 'vocational_institute'
        elif 'textile' in name_lower:
            return 'textile_institute'
        elif 'marine' in name_lower:
            return 'marine_institute'
        elif 'agriculture' in name_lower:
            return 'agricultural_institute'
        return 'technical_institute'
    
    def scrape(self) -> List[ScrapedInstitution]:
        """Scrape BTEB institute data."""
        institutions = []
        
        try:
            logger.info(f"[{self.source_name}] Starting BTEB institute scrape...")
            
            response = self._fetch(self.INSTITUTE_LIST_URL)
            institute_list = self._extract_institute_list(response.text)
            
            logger.info(f"[{self.source_name}] Found {len(institute_list)} institutes")
            
            for inst_data in institute_list[:100]:
                try:
                    inst_type = inst_data.get('type', 'technical_institute')
                    
                    institution = ScrapedInstitution(
                        name_en=inst_data['name'],
                        institution_type=inst_type,
                        district=inst_data.get('district'),
                        education_level='technical',
                        education_board='BTEB',
                        data_source='bteb.gov.bd',
                        source_url=self.INSTITUTE_LIST_URL
                    )
                    institutions.append(institution)
                    self.stats['items_scraped'] += 1
                    
                except Exception as e:
                    logger.error(f"[{self.source_name}] Error processing institute: {e}")
                    continue
            
            self.save_raw([i.to_dict() for i in institutions], "institutes")
            logger.info(f"[{self.source_name}] Scraped {len(institutions)} institutes")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
        
        return institutions


class GeneralBoardScraper(BaseScraper):
    """
    General Education Board Scrapers (Dhaka, Chittagong, etc.).
    Scrapes college and school data from individual board websites.
    """
    
    BOARD_URLS = {
        'dhaka': 'https://dhakaeducationboard.gov.bd',
        'chittagong': 'https://bise-ctg.portal.gov.bd',
        'rajshahi': 'https://www.rajshahieducationboard.gov.bd',
        'comilla': 'https://comillaeducationboard.gov.bd',
        'jessore': 'https://www.jessoreboard.gov.bd',
        'sylhet': 'https://sylhetboard.gov.bd',
        'barisal': 'https://barisalboard.gov.bd',
        'dinajpur': 'https://dinajpurboard.gov.bd',
        'mymensingh': 'https://mymensingheducationboard.gov.bd',
    }
    
    def __init__(self, board_name: str = 'dhaka'):
        super().__init__(source_name=f"board_{board_name}", delay_range=(2, 4))
        self.board_name = board_name
        self.base_url = self.BOARD_URLS.get(board_name)
    
    def _extract_college_list(self, html: str) -> List[Dict]:
        """Extract college list from board page."""
        soup = self._parse_html(html)
        colleges = []
        
        # Common patterns for college lists on board sites
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    college = {
                        'name': cells[0].get_text(strip=True),
                        'eiin': cells[1].get_text(strip=True) if len(cells) > 1 else None,
                        'district': cells[2].get_text(strip=True) if len(cells) > 2 else None,
                        'type': self._detect_school_type(cells[0].get_text())
                    }
                    colleges.append(college)
        
        return colleges
    
    def _detect_school_type(self, name: str) -> str:
        """Detect if college or school."""
        name_lower = name.lower()
        if 'college' in name_lower or 'degree' in name_lower:
            return 'college'
        elif any(x in name_lower for x in ['academy', 'school', 'high school']):
            return 'school'
        elif 'madrasa' in name_lower:
            return 'madrasa'
        return 'school'
    
    def scrape(self) -> List[ScrapedInstitution]:
        """Scrape general board college/school data."""
        institutions = []
        
        if not self.base_url:
            logger.warning(f"[{self.source_name}] No URL configured for board: {self.board_name}")
            return institutions
        
        try:
            logger.info(f"[{self.source_name}] Starting {self.board_name} board scrape...")
            
            # Try to find institution list page
            response = self._fetch(self.base_url)
            
            # Look for links to institution lists
            soup = self._parse_html(response.text)
            list_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                text = link.get_text().lower()
                if any(keyword in href or keyword in text for keyword in 
                       ['college', 'school', 'institute', 'list', 'eiin', 'institution']):
                    full_url = href if href.startswith('http') else self.base_url + href
                    list_links.append((link.get_text(strip=True), full_url))
            
            # Process found institution list pages
            for link_text, list_url in list_links[:3]:  # Limit to first 3 links
                try:
                    list_response = self._fetch(list_url)
                    college_list = self._extract_college_list(list_response.text)
                    
                    for college_data in college_list[:50]:
                        institution = ScrapedInstitution(
                            name_en=college_data['name'],
                            institution_type=college_data.get('type', 'school'),
                            district=college_data.get('district'),
                            education_level='secondary' if college_data.get('type') == 'school' else 'higher_secondary',
                            education_board=self.board_name.title() + ' Board',
                            data_source=f'{self.board_name}educationboard.gov.bd',
                            source_url=list_url
                        )
                        institutions.append(institution)
                        self.stats['items_scraped'] += 1
                        
                except Exception as e:
                    logger.error(f"[{self.source_name}] Error processing list page: {e}")
                    continue
            
            self.save_raw([i.to_dict() for i in institutions], "institutions")
            logger.info(f"[{self.source_name}] Scraped {len(institutions)} institutions")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] Scraping failed: {e}")
        
        return institutions
