# ShikkhaHub Data Pipeline Documentation

## Overview
This document describes the data processing pipeline for educational institution data.

## Data Sources
- Bangladesh Education Board PDFs
- Government websites  
- Manual data entry
- CSV imports

## Directory Structure

```
data/
├── raw/              # Original, unprocessed data
│   └── 20240507113426600593.pdf
├── processed/        # Cleaned and validated data
│   ├── 20240507113426600593.csv
│   ├── 20240507113426600593_cleaned.csv
│   └── 20240507113426600593_filtered.csv
└── analysis/         # Data analysis tools and documentation
    ├── data_analysis_guide.py
    ├── usage_examples.py
    └── QUICK_REFERENCE.md
```

## Processing Steps

### 1. Data Collection
- Raw data stored in `data/raw/` 
- Original PDFs and source files
- Automated scraping tools in `backend/scraper/` 

### 2. Data Cleaning
- Scripts in `data/analysis/` process raw data
- Remove duplicates and normalize formats
- Validate data quality

### 3. Data Storage
- Cleaned data in `data/processed/` 
- Import to PostgreSQL database
- Index in Elasticsearch for search

## Data Analysis Tools

### data_analysis_guide.py
Comprehensive Python library with:
- Data loading and cleaning functions
- Filtering functions (by district, thana, group, shift, version)
- Search functions (by name, EIIN, multiple criteria)
- Analysis functions (distribution, cross-tabulation)
- Export functions

### usage_examples.py
Practical examples showing:
- Basic filtering operations
- Complex searches with multiple criteria
- District and group analysis
- Special cases (colleges offering all groups, English version, etc.)

### QUICK_REFERENCE.md
Quick reference guide with:
- Dataset overview and structure
- Common code patterns
- Statistics and distributions
- Usage tips

## Data Quality Assurance

### Validation Rules
- Required fields validation
- Format checks (EIIN codes, phone numbers)
- Geographic data validation
- Duplicate detection

### Quality Metrics
- Data completeness score
- Freshness indicators
- Consistency checks
- Accuracy validation

## Usage Examples

### Load Cleaned Data
```python
import pandas as pd
df = pd.read_csv("data/processed/20240507113426600593_cleaned.csv")
```

### Filter by District
```python
dhaka_colleges = df[df['DIST_NAME'] == 'DHAKA MAHANAGARI']
```

### Search by College Name
```python
result = df[df['COLLEGE_NA'].str.contains('CANTONMENT', case=False)]
```

## Data Updates and Maintenance

### Automated Processes
- Daily data validation checks
- Weekly duplicate detection
- Monthly data quality reports
- Automated backup procedures

### Manual Processes
- New data source integration
- Data quality investigations
- Schema updates
- Performance optimization

## Backup and Recovery

### Backup Strategy
- Daily automated backups at 2 AM
- 30-day retention policy
- Point-in-time recovery capability
- Backup integrity verification

### Recovery Procedures
- Database restore from backup
- Data re-import from processed files
- Rollback procedures for data issues

## Integration Points

### Backend Integration
- CSV import scripts in `backend/scraper/importers/`
- Database models in `backend/app/models/`
- API endpoints for data access

### Search Integration
- Elasticsearch indexing pipeline
- Search service integration
- Real-time data synchronization

## Troubleshooting

### Common Issues
- Import errors: Check file paths and data formats
- Duplicate data: Run duplicate detection scripts
- Missing fields: Validate data source quality
- Performance issues: Check indexing and query optimization

### Support
- See `data/analysis/usage_examples.py` for code examples
- Check `data/analysis/QUICK_REFERENCE.md` for quick help
- Review backend logs for data processing errors