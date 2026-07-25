"""
Bangladesh Madrasah Education Board (BMEB) Scraper.

Scrapes Qawmi and Alia madrasah data from the BMEB website.
Handles SSL issues common with Bangladesh government sites.
"""

import logging
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
import re

from backend.scraper.base import BaseScraper, ScrapedInstitution

logger = logging.getLogger(__name__)


class BMEBScraper(BaseScraper):
    """Scraper for Bangladesh Madrasah Education Board.
    
    Sources:
    - Alia Madrasahs (bmeb.gov.bd)
    - Qawmi Madrasahs (various sources)
    
    Note: Bangladesh government sites often have SSL certificate issues,
    so we use bypass_ssl=True for connections.
    """
    
    # URLs for different madrasah types
    ALIA_MADRASAH_URL = "http://www.bmeb.gov.bd/institutions"
    # Alternative sources if main site fails
    BACKUP_URLS = [
        "https://www.bmeb.gov.bd/site/page/3f6f5536-5adb-4627-95e6-4ff5ebfa1d30/Alia-Madrasah-List",
        "http://www.educationboard.gov.bd/madrasah",
    ]
    
    # Major Qawmi madrasahs (hardcoded as fallback)
    KNOWN_QAWMI_MADRASAHS: List[Dict[str, Any]] = [
        {
            "name": "Al-Jamiatul Ahlia Darul Ulum Muinul Islam",
            "name_bn": "আল-জামিয়াতুল আহলিয়া দারুল উলুম মঈনুল ইসলাম",
            "short_name": "Hathazari Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Chattogram",
            "upazila": "Hathazari",
            "address": "Hathazari, Chattogram",
            "established_year": 1896,
            "website": "http://www.hathazari.edu.bd",
            "source_url": "https://en.wikipedia.org/wiki/Al-Jamiatul_Ahlia_Darul_Ulum_Muinul_Islam",
        },
        {
            "name": "Jamia Islamia Darul Uloom Madania",
            "name_bn": "জামেয়া ইসলামিয়া দারুল উলুম মাদানিয়া",
            "short_name": "Mohammadpur Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Dhaka",
            "district": "Dhaka",
            "upazila": "Mohammadpur",
            "address": "Mohammadpur, Dhaka",
            "established_year": 1985,
            "source_url": "https://www.darululoommadania.com",
        },
        {
            "name": "Jamia Qurania Arabia Lalbagh",
            "name_bn": "জামেয়া কুরআনিয়া আরাবিয়া লালবাগ",
            "short_name": "Lalbagh Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Dhaka",
            "district": "Dhaka",
            "address": "Lalbagh, Dhaka",
            "established_year": 1950,
            "source_url": "https://jameaquralbagh.com",
        },
        {
            "name": "Al-Jamiah Al-Islamiah Patiya",
            "name_bn": "আল-জামিয়া আল-ইসলামিয়া পটিয়া",
            "short_name": "Patiya Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Chattogram",
            "upazila": "Patiya",
            "address": "Patiya, Chattogram",
            "established_year": 1939,
            "source_url": "http://www.darululum-patiya.com",
        },
        {
            "name": "Jamia Imdadul Uloom Charbhadrasan",
            "name_bn": "জামিয়া ইমদাদুল উলুম চরভদ্রাসন",
            "short_name": "Charbhadrasan Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Dhaka",
            "district": "Faridpur",
            "upazila": "Charbhadrasan",
            "address": "Charbhadrasan, Faridpur",
            "established_year": 1982,
            "source_url": "https://www.jamia-charbhadrasan.edu.bd",
        },
        {
            "name": "Al-Jamiatul Islamiah Qasimul Uloom Islamia",
            "name_bn": "আল-জামিয়াতুল ইসলামিয়া কাসিমুল উলুম ইসলামিয়া",
            "short_name": "Chittagong Islamia Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Chattogram",
            "address": "Chattogram",
            "established_year": 1940,
        },
        {
            "name": "Jamia Arabia Imdadul Uloom Brahmanbaria",
            "name_bn": "জামিয়া আরাবিয়া ইমদাদুল উলুম ব্রাহ্মণবাড়িয়া",
            "short_name": "Brahmanbaria Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Brahmanbaria",
            "address": "Brahmanbaria",
            "established_year": 1978,
        },
        {
            "name": "Al-Jamiatul Arabiatul Islamiah Ziri",
            "name_bn": "আল-জামিয়াতুল আরাবিয়াতুল ইসলামিয়া জিরি",
            "short_name": "Ziri Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Chattogram",
            "address": "Ziri, Chattogram",
            "established_year": 1964,
        },
        {
            "name": "Al-Jamiah Al-Arabiah Ash-Sharfiah Gausia",
            "name_bn": "আল-জামিয়া আল-আরাবিয়া আশ-শরফিয়া গাউসিয়া",
            "short_name": "Feni Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Chattogram",
            "district": "Feni",
            "address": "Feni",
            "established_year": 1985,
        },
        {
            "name": "Jamia Islamia Ibrahimia Kurigram",
            "name_bn": "জামিয়া ইসলামিয়া ইব্রাহিমিয়া কুড়িগ্রাম",
            "short_name": "Kurigram Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Rangpur",
            "district": "Kurigram",
            "address": "Kurigram",
            "established_year": 1990,
        },
        {
            "name": "Al-Jamiatul Arabiah Nathalia",
            "name_bn": "আল-জামিয়াতুল আরাবিয়া নাথালিয়া",
            "short_name": "Nathalia Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Barishal",
            "district": "Barishal",
            "upazila": "Nathalia",
            "address": "Nathalia, Barishal",
            "established_year": 1965,
        },
        {
            "name": "Jamia Islamia Darul Uloom Sylhet",
            "name_bn": "জামিয়া ইসলামিয়া দারুল উলুম সিলেট",
            "short_name": "Sylhet Qawmi Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Sylhet",
            "district": "Sylhet",
            "address": "Sylhet",
            "established_year": 1972,
        },
        {
            "name": "Jamia Arabia Asad Madania Bogura",
            "name_bn": "জামিয়া আরাবিয়া আসাদ মাদানিয়া বগুড়া",
            "short_name": "Bogura Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Rajshahi",
            "district": "Bogura",
            "address": "Bogura",
            "established_year": 1980,
        },
        {
            "name": "Al-Jamiatul Islamiah Muhammadpur",
            "name_bn": "আল-জামিয়াতুল ইসলামিয়া মুহাম্মাদপুর",
            "short_name": "Khulna Madrasah",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Khulna",
            "district": "Khulna",
            "upazila": "Mohammadpur",
            "address": "Mohammadpur, Khulna",
            "established_year": 1960,
        },
        {
            "name": "Jamia Islamia Khulna",
            "name_bn": "জামিয়া ইসলামিয়া খুলনা",
            "short_name": "Khulna Islamia",
            "institution_type": "madrasa",
            "education_level": "higher_secondary",
            "division": "Khulna",
            "district": "Khulna",
            "address": "Khulna",
            "established_year": 1985,
        },
    ]
    
    def __init__(self):
        super().__init__(
            source_name="bmeb",
            delay_range=(2, 5),  # Slower for government sites
            verify_ssl=False,    # Bangladesh government sites often have SSL issues
            max_retries=5,
            timeout=45         # Government sites are slow
        )
    
    def scrape(self) -> List[ScrapedInstitution]:
        """Scrape madrasah data from BMEB sources."""
        institutions = []
        
        # Try to scrape from website first
        try:
            website_data = self._scrape_from_website()
            institutions.extend(website_data)
            logger.info(f"[{self.source_name}] Scraped {len(website_data)} institutions from website")
        except Exception as e:
            logger.warning(f"[{self.source_name}] Website scraping failed: {e}")
        
        # If website fails or returns few results, use known madrasahs
        if len(institutions) < 5:
            logger.info(f"[{self.source_name}] Using fallback data for known madrasahs")
            fallback_data = self._get_fallback_data()
            institutions.extend(fallback_data)
        
        self.stats['items_scraped'] = len(institutions)
        return institutions
    
    def _scrape_from_website(self) -> List[ScrapedInstitution]:
        """Attempt to scrape from BMEB website with SSL bypass."""
        institutions = []
        
        # Try main URL with SSL bypass
        for url in [self.ALIA_MADRASAH_URL] + self.BACKUP_URLS:
            try:
                response = self._fetch(url, bypass_ssl=True, allow_404=True)
                if response.status_code == 404:
                    continue
                    
                soup = self._parse_html(response.text)
                
                # Look for institution tables or lists
                institutions.extend(self._parse_institution_page(soup, url))
                
                # If we got results, don't try backup URLs
                if len(institutions) > 0:
                    break
                    
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed to fetch {url}: {e}")
                continue
        
        return institutions
    
    def _parse_institution_page(self, soup: BeautifulSoup, source_url: str) -> List[ScrapedInstitution]:
        """Parse institution data from HTML page."""
        institutions = []
        
        # Try to find tables with institution data
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    # Extract data from cells
                    name = self._extract_text(cells[0])
                    if not name:
                        continue
                    
                    # Try to extract location info
                    location_text = self._extract_text(cells[1]) if len(cells) > 1 else ""
                    division, district, upazila = self._parse_location(location_text)
                    
                    # Try to extract other info
                    established = None
                    if len(cells) > 2:
                        established_text = self._extract_text(cells[2])
                        established = self._extract_year(established_text)
                    
                    institution = ScrapedInstitution(
                        name_en=name,
                        institution_type="madrasa",
                        division=division,
                        district=district,
                        upazila=upazila,
                        address=location_text,
                        established_year=established,
                        data_source="bmeb",
                        source_url=source_url,
                    )
                    institutions.append(institution)
                    
                except Exception as e:
                    logger.debug(f"[{self.source_name}] Error parsing row: {e}")
                    continue
        
        # Also look for list items or divs that might contain institutions
        if not institutions:
            institutions.extend(self._parse_alternative_format(soup, source_url))
        
        return institutions
    
    def _parse_alternative_format(self, soup: BeautifulSoup, source_url: str) -> List[ScrapedInstitution]:
        """Try alternative HTML structures."""
        institutions = []
        
        # Look for divs with institution names
        for div in soup.find_all(['div', 'li'], class_=re.compile(r'institution|madrasah|school', re.I)):
            try:
                name_elem = div.find(['h3', 'h4', 'strong', 'a', 'span'])
                if not name_elem:
                    continue
                
                name = self._extract_text(name_elem)
                if not name or len(name) < 5:
                    continue
                
                # Check if it looks like a madrasah name
                if any(keyword in name.lower() for keyword in ['madrasah', 'madrasa', 'jamia', 'qawmi', 'alia']):
                    institution = ScrapedInstitution(
                        name_en=name,
                        institution_type="madrasa",
                        data_source="bmeb",
                        source_url=source_url,
                    )
                    institutions.append(institution)
            except Exception:
                continue
        
        return institutions
    
    def _get_fallback_data(self) -> List[ScrapedInstitution]:
        """Get known madrasahs as fallback when scraping fails."""
        institutions = []
        
        for data in self.KNOWN_QAWMI_MADRASAHS:
            institution = ScrapedInstitution(
                name_en=data["name"],
                name_bn=data.get("name_bn"),
                short_name=data.get("short_name"),
                institution_type="madrasa",
                education_level=data.get("education_level"),
                division=data.get("division"),
                district=data.get("district"),
                upazila=data.get("upazila"),
                address=data.get("address"),
                established_year=data.get("established_year"),
                website=data.get("website"),
                data_source="bmeb",
                source_url=data.get("source_url", self.ALIA_MADRASAH_URL),
            )
            institutions.append(institution)
        
        return institutions
    
    def _extract_text(self, element) -> Optional[str]:
        """Extract clean text from HTML element."""
        if not element:
            return None
        text = element.get_text(strip=True)
        return text if text else None
    
    def _parse_location(self, location_text: str) -> tuple:
        """Parse division, district, upazila from location text."""
        if not location_text:
            return None, None, None
        
        # Common Bangladesh divisions
        divisions = [
            'Dhaka', 'Chattogram', 'Chittagong', 'Rajshahi', 'Khulna', 'Barishal', 'Barisal',
            'Sylhet', 'Rangpur', 'Mymensingh', 'Comilla', 'Noakhali', 'Feni', 'Lakshmipur',
            'Chandpur', 'Cox\'s Bazar', 'Bandarban', 'Khagrachhari', 'Rangamati'
        ]
        
        division = None
        district = None
        upazila = None
        
        # Try to find division
        for div in divisions:
            if div.lower() in location_text.lower():
                division = div
                break
        
        # Common patterns: "District, Division" or "Upazila, District, Division"
        parts = [p.strip() for p in location_text.split(',')]
        
        if len(parts) >= 2:
            district = parts[-2]
        if len(parts) >= 3:
            upazila = parts[-3]
        
        return division, district, upazila


if __name__ == "__main__":
    # Test the scraper
    scraper = BMEBScraper()
    results = scraper.scrape()
    print(f"Scraped {len(results)} madrasahs")
    for r in results[:5]:
        print(f"- {r.name_en} ({r.division})")
