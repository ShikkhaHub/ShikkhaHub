# ShikkhaHub Data Scraper

Automated data collection system for Bangladesh education institutions.

## Overview

This scraper extracts institution data from official Bangladesh education sources:
- **UGC** (ugc.gov.bd) - Universities
- **BMEB** (bmeb.gov.bd) - Madrasahs  
- **BTEB** (bteb.gov.bd) - Technical institutes, polytechnics
- **Education Boards** - Colleges and schools

## Quick Start

### 1. Install Dependencies

```bash
cd backend/scraper
pip install -r requirements.txt
```

### 2. Run Scrapers

```bash
# Scrape UGC universities
python -m scraper.run --source ugc --import-to-db

# Scrape all sources
python -m scraper.run --source all --import-to-db

# Scrape specific education board
python -m scraper.run --source board --board-name dhaka
```

### 3. CSV Upload (Alternative)

```bash
# Generate template
python -m scraper.run --generate-csv-template > institutions.csv

# Fill in data, then import
python -m scraper.run --csv-file institutions.csv
```

Or use the API:
```bash
curl -X POST -F "file=@institutions.csv" http://localhost:8000/api/v1/admin/import/csv
```

## Architecture

```
scraper/
├── base.py              # BaseScraper class with HTTP/retry logic
├── validators.py      # Data quality validators
├── scrapers/            # Source-specific scrapers
│   ├── ugc_scraper.py
│   ├── education_board_scraper.py
│   └── ...
├── importers/           # Database importers
│   ├── postgres_importer.py
│   └── csv_importer.py
└── data/
    ├── raw/            # Raw scraped JSON
    └── processed/      # Cleaned data
```

## Data Quality System

Each scraped institution gets:
- **Confidence Score** (0-1) based on data completeness
- **Validation Report** - errors, warnings, suggestions
- **Deduplication Check** - against existing database

### Validation Rules

| Field | Required | Validation |
|-------|----------|------------|
| name_en | Yes | Min 3 chars, max 300 |
| institution_type | Yes | Must be known type |
| division | No | Must be valid BD division |
| phone | No | BD format: +8801XXXXXXXXX |
| email | No | Valid email format |
| established_year | No | 1800-current |

## Scraped Data Structure

```python
@dataclass
class ScrapedInstitution:
    name_en: str                    # Required
    institution_type: str           # Required
    division: str?                  # Location
    district: str?
    phone: str?                     # Normalized BD format
    email: str?
    website: str?
    established_year: int?
    data_source: str                # ugc.gov.bd, bmeb.gov.bd, etc.
    confidence_score: float         # Auto-calculated 0-1
```

## Adding New Scrapers

```python
from scraper.base import BaseScraper, ScrapedInstitution

class NewSourceScraper(BaseScraper):
    def __init__(self):
        super().__init__(source_name="new_source")
    
    def scrape(self) -> List[ScrapedInstitution]:
        # 1. Fetch listing page
        response = self._fetch("https://source.gov.bd/institutions")
        
        # 2. Parse list
        institutions = self._parse_list(response.text)
        
        # 3. Fetch details for each
        for inst in institutions:
            detail = self._fetch(inst['url'])
            # Extract and yield ScrapedInstitution
            
        return results
```

## Rate Limiting & Ethics

- **Delay**: 2-4 seconds between requests
- **Retry**: 3 attempts with exponential backoff
- **Respect robots.txt**: Checked automatically
- **User-Agent**: Rotated to avoid blocking

## Production Deployment

### Docker

```bash
docker-compose up -d
```

Includes:
- PostgreSQL database
- Redis cache (future use)
- Scraper as background job

### Environment Variables

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/shikkhahub
SCRAPER_DELAY_MIN=2
SCRAPER_DELAY_MAX=4
```

### Scheduling (Cron)

```bash
# Weekly full refresh
0 2 * * 0 cd /app && python -m scraper.run --source all --import-to-db

# Daily incremental
0 6 * * * cd /app && python -m scraper.run --source ugc --import-to-db
```

## Monitoring

Scraper outputs statistics:
```json
{
  "requests": 150,
  "success": 145,
  "failed": 5,
  "items_scraped": 45
}
```

Import outputs:
```json
{
  "created": 30,
  "updated": 10,
  "skipped": 5,
  "failed": 0
}
```

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Connection timeout | Increase delay: `--delay 5` |
| Blocked by website | Check robots.txt, use different User-Agent |
| Empty results | Website structure changed, update parser |
| Import failures | Check validation report, fix data quality |

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

After data collection:
1. **Manual Review**: Flagged institutions need verification
2. **Data Enrichment**: Add missing fields (descriptions, images)
3. **Sync to Search**: Index in ElasticSearch for search
4. **AI Training**: Use verified data for recommendation system
