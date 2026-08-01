"""
UGC (University Grants Commission) Spider
Scrapes list of recognized universities in Bangladesh
Tier 1 source - HIGHEST TRUST
"""

import scrapy
from .base_spider import GovernmentSourceSpider
from typing import Generator


class UGCSpider(GovernmentSourceSpider):
    """
    Scrapes UGC approved universities.
    Source: https://ugc.gov.bd
    """
    
    name = 'ugc_spider'
    allowed_domains = ['ugc.gov.bd']
    
    # Start with static list of UGC URLs (we'll update this based on actual website structure)
    start_urls = [
        'https://ugc.gov.bd/en/public-universities',
        'https://ugc.gov.bd/en/private-universities',
    ]
    
    def parse(self, response: scrapy.http.HtmlResponse) -> Generator:
        """Parse UGC university listings"""
        
        # Extract university links from listing page
        if 'public-universities' in response.url:
            university_type = 'public'
            list_selector = 'div.university-list > div.university-item'
        else:
            university_type = 'private'
            list_selector = 'div.university-list > div.university-item'
        
        # Get all university items
        for university in response.css(list_selector):
            name = self.extract_text(university, './/h3/text()')
            detail_url = university.css('a::attr(href)').get()
            
            if detail_url:
                detail_url = response.urljoin(detail_url)
                yield scrapy.Request(
                    detail_url,
                    callback=self.parse_university_detail,
                    meta={
                        'university_name': name,
                        'university_type': university_type,
                    }
                )
    
    def parse_university_detail(self, response: scrapy.http.HtmlResponse) -> Generator:
        """Parse individual university details"""
        
        try:
            university_name = response.meta.get('university_name', '')
            university_type = response.meta.get('university_type', '')
            
            # Extract information from detail page
            data = {
                'name': university_name or self.extract_text(response, '//h1/text()'),
                'type': 'University',
                'category': university_type.capitalize(),
                
                # Contact information
                'phone': self.extract_text(response, '//span[contains(text(), "Phone")]/following-sibling::span/text()'),
                'email': response.css('a[href*="mailto:"]::attr(href)').get(''),
                'email': self.extract_text(response, '//a[contains(@href, "mailto:")]::text()'),
                'website': response.css('a[contains(@href, "http")]::attr(href)').get(''),
                
                # Location information
                'address': self.extract_text(response, '//span[contains(text(), "Address")]/following-sibling::span/text()'),
                'district': '',  # Will be extracted from address if available
                'upazila': '',
                'division': '',
                
                # Additional information
                'established_year': self.extract_year(response),
                'description': self.extract_text(response, '//div[@class="description"]//text()'),
                
                # Source tracking
                'source_url': response.url,
            }
            
            # Extract coordinates if available
            coordinates_text = response.xpath('//script[contains(text(), "coordinates")]/text()').get()
            if coordinates_text:
                coords = self.extract_coordinates(coordinates_text)
                data['coordinates'] = coords
            
            # Extract district from address if present
            data['district'] = self.extract_district_from_address(data['address'])
            
            # Create item
            item = self.create_institution_item(data)
            
            self.logger.info(f'Scraped university: {data["name"]}')
            self.stats['total_items'] += 1
            
            yield item
            
        except Exception as e:
            self.log_error(f'Error parsing university detail: {response.url}', e)
    
    def extract_year(self, response) -> int:
        """Extract establishment year from response"""
        year_text = self.extract_text(response, '//span[contains(text(), "Established")]/following-sibling::span/text()')
        import re
        match = re.search(r'\b(19|20)\d{2}\b', year_text)
        if match:
            return int(match.group(0))
        return None
    
    def extract_coordinates(self, text: str) -> dict:
        """Extract latitude and longitude from text"""
        import re
        coords = {}
        lat_match = re.search(r'latitude["\s:]+([0-9.]+)', text, re.IGNORECASE)
        lon_match = re.search(r'longitude["\s:]+([0-9.]+)', text, re.IGNORECASE)
        
        if lat_match:
            coords['latitude'] = float(lat_match.group(1))
        if lon_match:
            coords['longitude'] = float(lon_match.group(1))
        
        return coords
    
    def extract_district_from_address(self, address: str) -> str:
        """Extract district name from address"""
        # Common districts in Bangladesh
        districts = [
            'Dhaka', 'Chattogram', 'Khulna', 'Rajshahi', 'Barisal', 'Sylhet',
            'Rangpur', 'Mymensingh', 'Bogra', 'Dinajpur', 'Naogaon', 'Natore',
            'Chapainawabganj', 'Pabna', 'Jashore', 'Magura', 'Narail', 'Satkhira',
            'Jhenaidah', 'Pirojpur', 'Jhalokati', 'Patuakhali', 'Barisal',
            'Bhola', 'Noakhali', 'Lakshmipur', 'Feni', 'Comilla', 'Chandpur',
            'Habiganj', 'Maulvibazar', 'Sunamganj', 'Kurigram', 'Gaibandha',
            'Thakurgaon', 'Panchagarh', 'Kishoreganj', 'Jamalpur', 'Sherpur',
            'Netrokona', 'Tangail', 'Manikganj', 'Munshiganj', 'Faridpur', 'Rajbari',
            'Gopalganj', 'Shariatpur', 'Madaripur'
        ]
        
        for district in districts:
            if district.lower() in address.lower():
                return district
        
        return ''
