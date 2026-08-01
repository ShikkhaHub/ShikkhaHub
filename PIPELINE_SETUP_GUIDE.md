# ShikkhaHub Data Pipeline - Setup & Execution Guide

## Overview

This is a **production-grade data collection and verification system** for building a verified database of Bangladesh educational institutions (10,000+).

**Goal:** Collect 2,000+ verified institutions in Month 1 from government sources only.

---

## Architecture

```
Tier 1 Sources (High Trust)  → Scraper → Raw Data → Processor → Deduplicator
↓ (UGC, Boards, BTEB)          Engine    Table      (Clean)      (Find Dupes)
                                                          ↓
                                                    Admin Review
                                                          ↓
                                                    Verification
                                                          ↓
                                                    Main DB + Search Index
```

---

## Directory Structure

```
data-pipeline/
├── db/models.py                 # Database models for raw data, sources, verification
├── scraper/
│   ├── settings.py              # Scrapy configuration
│   └── spiders/
│       ├── base_spider.py       # Base spider class (normalization utilities)
│       ├── ugc_spider.py        # UGC universities scraper
│       ├── board_spider.py      # Education boards scraper (TODO)
│       └── bteb_spider.py       # Technical education board (TODO)
├── processor/
│   └── processor.py             # Data cleaning + deduplication engine
├── pipeline/
│   └── tasks.py                 # Celery scheduled tasks
└── admin/
    └── admin_routes.py          # FastAPI endpoints for verification dashboard
```

---

## Phase 1: First 14 Days

### Week 1: Scraper Deployment

**Goal:** Get 500 UGC universities into system

**Steps:**

1. **Deploy Database Models**
   ```bash
   cd backend
   alembic upgrade head
   ```
   Creates tables:
   - `raw_data` - Stores scraped data
   - `data_sources` - Metadata about sources
   - `verification_records` - Track verification status
   - `duplicate_candidates` - Potential duplicates
   - `scraping_jobs` - Job history

2. **Test UGC Spider**
   ```bash
   cd data-pipeline
   scrapy crawl ugc_spider
   ```
   Expected output:
   - ~42 public universities
   - ~30 private universities (initial)
   - Data stored in `raw_data` table with status='pending'

3. **Verify Raw Data**
   - Query: `SELECT COUNT(*) FROM raw_data WHERE status='pending'`
   - Expected: 500+ institutions

### Week 2: Processing & Admin Panel

**Goal:** Verify 350+ institutions (70%), launch admin dashboard

**Steps:**

1. **Process Pending Data**
   ```python
   from data_pipeline.processor.processor import DataProcessor
   processor = DataProcessor()
   
   # Process 100 items
   result = processor.process(raw_item)
   # result = cleaned + normalized data
   ```

2. **Admin Dashboard Integration**
   ```
   Admin Panel Features:
   ✓ View raw scraped data
   ✓ Approve/reject/edit
   ✓ Compare potential duplicates
   ✓ Verify institutions
   ✓ View stats
   ```

3. **Verification Workflow**
   ```
   Raw Scraped Data
         ↓
   Admin Reviews
   - Check completeness
   - Verify against official sources
   - Mark verification_level = 3 (confirmed)
         ↓
   Verified Data → institutions table
   ```

---

## Data Collection Strategy (Tier System)

### Tier 1: Government Sources (95% Trust)
**Start HERE - Month 1**

Sources:
- UGC (University Grants Commission) - 100+ universities
- BTEB (Bangladesh Technical Education Board) - 50+ polytechnics
- Government colleges (Ministry of Education) - 1,000+
- Education boards (7 regional boards) - 10,000+ schools/colleges

**Strategy:**
- Scrape official listings
- Verify with official contacts
- 100% trust in data accuracy
- Daily updates possible

### Tier 2: Medium Trust (70-80%)
**Start Month 2**

Sources:
- Educational directories
- Wikipedia
- School finder websites
- Government portals (secondary)

**Strategy:**
- Cross-reference with Tier 1
- Require manual verification
- Update weekly

### Tier 3: Community (50-60%)
**Start Month 3+**

Sources:
- Facebook pages
- User submissions
- Alumni reports
- Social media

**Strategy:**
- Requires 3+ corroborations
- Manual admin review required
- Update monthly

---

## Usage Examples

### 1. Run Scraper

```python
# Manually trigger UGC scraper
from scrapy.crawler import CrawlerProcess
from data_pipeline.scraper.spiders.ugc_spider import UGCSpider

process = CrawlerProcess({
    'USER_AGENT': 'ShikkhaHub +https://shikkhahub.com',
    'DOWNLOAD_DELAY': 2,
})
process.crawl(UGCSpider)
process.start()
```

**Output:**
- Raw data in `raw_data` table
- Status: 'pending'
- Each record has:
  - `raw_json`: Complete scraped data
  - `source_type`: 'government'
  - `tier`: 1
  - `trust_score`: 0.95

### 2. Process Data

```python
from data_pipeline.processor.processor import DataProcessor

processor = DataProcessor()

# Get pending items
raw_items = session.query(RawData).filter(
    RawData.status == 'pending'
).limit(100).all()

# Process each
for item in raw_items:
    cleaned = processor.process(item.raw_json)
    # cleaned = {
    #   'name': 'University Name',
    #   'type': 'university',
    #   'email': 'contact@uni.edu.bd',
    #   'phone': '+880123456789',
    #   ...
    # }
```

### 3. Find Duplicates

```python
from data_pipeline.processor.processor import Deduplicator

dedup = Deduplicator(similarity_threshold=0.85)

# Get all processed items
items = session.query(Institution).all()

# Find duplicates
duplicates = dedup.find_duplicates([
    {
        'name': i.name_en,
        'name_normalized': i.name_en.lower(),
        'phone': i.phone,
        'email': i.email,
        'district': i.district,
    }
    for i in items
])

# Results: [(idx1, idx2, similarity_score), ...]
# Example: [(5, 12, 0.92), (8, 15, 0.88), ...]
```

### 4. Verify Institution

```python
# Admin verifies an institution
from fastapi import APIRouter

@app.post('/api/v2/admin/pipeline/verify-institution')
async def verify(req: InstitutionVerificationRequest):
    # req.institution_id = 123
    # req.verification_level = 3  # confirmed
    # req.verified_sources = [1, 2]  # source IDs
    
    # Update verification_level
    verification = VerificationRecord(
        institution_id=req.institution_id,
        verification_level=req.verification_level,
        verified_sources=req.verified_sources,
        verified_by_admin='admin@shikkhahub.com',
        verified_at=datetime.utcnow(),
    )
    session.add(verification)
    session.commit()
```

### 5. View Admin Dashboard

```
GET /api/v2/admin/pipeline/stats
{
  "total_raw_data": 2000,
  "pending_raw_data": 500,
  "processed_raw_data": 1400,
  "error_raw_data": 100,
  "institutions_verified": 1400,
  "verification_rate": 0.70,
  "duplicates_found": 45,
  "duplicates_resolved": 30,
  "last_scrape_time": "2024-08-01T01:00:00Z",
  "next_scheduled_scrape": "2024-08-02T01:00:00Z"
}
```

---

## Celery Scheduled Tasks

### Schedule

```python
# Daily at 1 AM UTC
scrape_tier1_sources()
  → Scrapes: UGC, BTEB, Boards, Government colleges
  → Creates: 500-1000 raw_data entries
  → Time: ~30 minutes

# Every 30 minutes
process_pending_data()
  → Processes: 100 pending items
  → Cleans: Names, phones, emails, locations
  → Updates: status='processed'

# Every 6 hours
check_duplicates()
  → Finds: Potential duplicates
  → Scores: 0-1.0 similarity
  → Creates: DuplicateCandidate entries

# Daily at 3 AM UTC
refresh_search_index()
  → Syncs verified data to Elasticsearch
  → Updates: Search index
  → Clears: Stale entries
```

### Manual Triggers

```bash
# Manually trigger scraping
POST /api/v2/admin/pipeline/trigger-scrape/government

# Manually process pending data
POST /api/v2/admin/pipeline/process-pending-data

# Get duplicate candidates for review
GET /api/v2/admin/pipeline/duplicate-candidates

# Merge two institutions
POST /api/v2/admin/pipeline/merge-duplicates
{
  "institution_id_1": 123,
  "institution_id_2": 456,
  "keep_id": 123,
  "reason": "Same institution, different data sources"
}
```

---

## Data Quality

### Completeness Scoring

Each processed institution gets a `completeness_score` (0-1.0):

```python
# Example
institution = {
    'name': 'Dhaka University',  ✓
    'type': 'university',         ✓
    'email': 'contact@du.ac.bd',  ✓
    'phone': '+880123456789',     ✓
    'address': 'Dhaka',           ✓
    'website': 'www.du.ac.bd',    ✓
    'district': 'Dhaka',          ✓
    'established_year': 1921,     ✓
}

# Score = 8/10 = 0.80 (80% complete)
```

### Deduplication Scoring

When comparing two institutions:

```
Similarity = (
  name_match * 0.40 +          # 40% weight
  phone_match * 0.30 +         # 30% weight
  email_match * 0.20 +         # 20% weight
  location_match * 0.10        # 10% weight
)

Example:
- Names similar: 0.92
- Phones match: 1.0
- Emails don't match: 0.0
- Same district: 1.0

Score = (0.92 * 0.4) + (1.0 * 0.3) + (0 * 0.2) + (1.0 * 0.1)
      = 0.368 + 0.3 + 0 + 0.1
      = 0.768 (77% similar - likely duplicate!)
```

---

## Troubleshooting

### Scraper Issues

**Problem:** Scraper returns 0 institutions

**Solutions:**
- Check if website structure changed (manually inspect)
- Verify network access (curl test_url)
- Check User-Agent header
- Review scraper logs

**Command:**
```bash
scrapy crawl ugc_spider -o output.json -L DEBUG
```

### Deduplication Not Working

**Problem:** Same institution appearing multiple times

**Solutions:**
- Lower similarity_threshold (default 0.85)
- Add more matching rules (website URL, establishment year)
- Manual merge in admin panel

### Verification Stuck

**Problem:** Admin can't approve institutions

**Solutions:**
- Check admin permissions
- Verify database connectivity
- Clear Redis cache

```bash
redis-cli FLUSHALL
```

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Scraping | 500-1000 items/day | Ready |
| Processing | 100 items/30min | Ready |
| Deduplication | <1ms per pair | Ready |
| Admin Review | <2sec per item | Ready |
| Search Response | <200ms | TBD |

---

## Month 1 Roadmap

### Week 1 ✓
- [ ] Deploy database models
- [ ] Test UGC spider
- [ ] Collect 500 UGC universities
- [ ] Raw data in system

### Week 2
- [ ] Deploy processor
- [ ] Process 1,000+ items
- [ ] Admin panel basic UI
- [ ] Manual verification workflow

### Week 3
- [ ] Deploy BTEB spider
- [ ] Collect polytechnics
- [ ] Implement deduplication
- [ ] Add duplicate resolution

### Week 4
- [ ] Deploy board spiders
- [ ] Collect 2,000+ institutions
- [ ] 70%+ verified
- [ ] Search indexing live

---

## Success Metrics (30 Days)

- ✓ 2,000+ institutions collected
- ✓ 70%+ verified
- ✓ <5% duplicates
- ✓ 80%+ completeness
- ✓ Admin dashboard operational
- ✓ Scraping jobs running on schedule

---

## Next Steps

1. **Deploy Phase 1**
   - Database models
   - UGC spider

2. **Start Data Collection**
   - Run spider daily
   - Monitor progress

3. **Build Admin Panel**
   - Verification UI
   - Duplicate resolution

4. **Scale to Tier 2**
   - Board spiders
   - Educational directories

5. **Launch Public Search**
   - Index verified data
   - Public API

---

This is the **data backbone of ShikkhaHub**.
Data quality is the product. Everything else is UI.

Execute with discipline.
