# Educational Data Analysis - Quick Reference Guide

## Dataset Overview
- **Source**: Dhaka Education Board College Data
- **Total Records**: 3,290 (after cleaning)
- **Unique Colleges**: 1,118 institutions
- **Geographic Coverage**: 14 districts, 121 thanas
- **Data File**: `20240507113426600593_cleaned.csv`

## Data Structure

| Column | Description | Values |
|--------|-------------|---------|
| BOARD_NAME | Education board | DHAKA |
| DIST_NAME | District name | 14 districts |
| THANA_NAME | Thana/sub-district | 121 thanas |
| EIIN | Institute ID (unique) | 1,121 unique codes |
| COLLEGE_NA | College name | 1,118 unique names |
| SHIFT | Shift timing | Day, Morning |
| VERSION | Medium of instruction | Bangla, English |
| GROUP | Academic stream | Science, Humanities, Business Studies |

## Quick Start Commands

### 1. Load Data
```python
import pandas as pd
df = pd.read_csv("20240507113426600593_cleaned.csv")
```

### 2. Basic Filtering
```python
# By district
dhaka_colleges = df[df['DIST_NAME'] == 'DHAKA MAHANAGARI']

# By academic group
science_colleges = df[df['GROUP'] == 'Science']

# By shift
morning_colleges = df[df['SHIFT'] == 'Morning']

# By version
english_colleges = df[df['VERSION'] == 'English']
```

### 3. Complex Filtering
```python
# Science + English + Morning
complex_filter = df[
    (df['GROUP'] == 'Science') & 
    (df['VERSION'] == 'English') & 
    (df['SHIFT'] == 'Morning')
]

# Specific district and group
district_science = df[
    (df['DIST_NAME'] == 'DHAKA MAHANAGARI') & 
    (df['GROUP'] == 'Science')
]
```

### 4. Search Operations
```python
# Search by college name
result = df[df['COLLEGE_NA'].str.contains('CANTONMENT', case=False)]

# Get specific college by EIIN
college = df[df['EIIN'] == '107825']
```

### 5. Analysis Examples
```python
# Count by district
district_counts = df.groupby('DIST_NAME')['EIIN'].nunique()

# Count by group
group_counts = df['GROUP'].value_counts()

# Cross-tabulation
district_group = pd.crosstab(df['DIST_NAME'], df['GROUP'])

# Colleges with multiple groups
multi_group = df.groupby('EIIN')['GROUP'].nunique()
multi_group_colleges = multi_group[multi_group > 1]
```

### 6. Export Results
```python
# Export filtered data
filtered_df.to_csv('output.csv', index=False)

# Export summary
summary.to_csv('summary.csv')
```

## Common Use Cases

### Find colleges in a specific area
```python
# By district
area_colleges = df[df['DIST_NAME'] == 'YOUR_DISTRICT']

# By thana
thana_colleges = df[df['THANA_NAME'] == 'YOUR_THANA']
```

### Find colleges by academic program
```python
# Science programs
science = df[df['GROUP'] == 'Science']

# Business Studies
business = df[df['GROUP'] == 'Business Studies']

# Humanities
humanities = df[df['GROUP'] == 'Humanities']
```

### Find colleges by timing
```python
# Day shift
day_shift = df[df['SHIFT'] == 'Day']

# Morning shift
morning_shift = df[df['SHIFT'] == 'Morning']
```

### Find English medium institutions
```python
english_medium = df[df['VERSION'] == 'English']
```

### Combined searches
```python
# English version Science colleges
english_science = df[
    (df['VERSION'] == 'English') & 
    (df['GROUP'] == 'Science')
]

# Morning shift Business Studies in specific district
morning_business_dhaka = df[
    (df['SHIFT'] == 'Morning') & 
    (df['GROUP'] == 'Business Studies') &
    (df['DIST_NAME'] == 'DHAKA MAHANAGARI')
]
```

## Key Statistics

### Academic Groups Distribution
- Business Studies: 1,164 programs (35.4%)
- Humanities: 1,074 programs (32.6%)
- Science: 1,049 programs (31.9%)

### Shift Distribution
- Day shift: 2,886 programs (87.7%)
- Morning shift: 400 programs (12.2%)

### Version Distribution
- Bangla medium: 3,189 programs (96.9%)
- English medium: 101 programs (3.1%)

## Files Available

1. **20240507113426600593.pdf** - Original PDF document
2. **20240507113426600593.csv** - Full converted CSV (with all columns)
3. **20240507113426600593_filtered.csv** - Filtered CSV (8 columns only)
4. **20240507113426600593_cleaned.csv** - Cleaned data ready for analysis
5. **data_analysis_guide.py** - Comprehensive analysis functions
6. **usage_examples.py** - Practical usage examples

## Running the Analysis

### Run comprehensive analysis
```bash
python3 data_analysis_guide.py
```

### Run usage examples
```bash
python3 usage_examples.py
```

### Custom analysis
```python
import pandas as pd
from data_analysis_guide import *

# Load data
df = pd.read_csv("20240507113426600593_cleaned.csv")

# Use any function from the guide
result = find_science_colleges_in_district("DHAKA MAHANAGARI")
print(result)
```

## Tips

1. **Always use the cleaned data** (`20240507113426600593_cleaned.csv`) for analysis
2. **EIIN is the unique identifier** for colleges
3. **College names may vary** slightly in spelling - use string search for partial matches
4. **Group by EIIN** when you want to analyze at the college level (not program level)
5. **Export results** frequently to CSV for further analysis in Excel or other tools

## Data Quality Notes

- 71 invalid rows were removed during cleaning (header rows mixed in data)
- All 3,290 remaining records have valid EIIN and college names
- Data is from Dhaka Education Board only
- English version institutions are relatively rare (3.1%)
- Morning shift programs are less common (12.2%)
