"""
Educational Institution Data Analysis Guide
===========================================

This dataset contains information about educational institutions (colleges) 
from the Dhaka Education Board. It includes 3,290 records with the following structure:

Columns:
- BOARD_NAME: Education board name (DHAKA)
- DIST_NAME: District name (14 districts)
- THANA_NAME: Thana/sub-district name (121 thanas)
- EIIN: Educational Institute Identification Number (unique identifier)
- COLLEGE_NA: College name
- SHIFT: Shift timing (Day, Morning)
- VERSION: Medium of instruction (Bangla, English)
- GROUP: Academic group/Stream (Science, Humanities, Business Studies)

Data Summary:
- Total Records: 3,290
- Total Colleges: 1,118 unique institutions
- Total Districts: 14
- Total Thanas: 121
- Groups: Science (1,049), Humanities (1,074), Business Studies (1,164)
- Shifts: Day (2,886), Morning (400)
- Versions: Bangla (3,189), English (101)
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load the cleaned data
df = pd.read_csv("20240507113426600593_cleaned.csv")

# =============================================================================
# BASIC DATA EXPLORATION
# =============================================================================

def basic_overview():
    """Get basic overview of the dataset"""
    print("=== BASIC OVERVIEW ===")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nData shape: {df.shape}")
    print(f"\nFirst few rows:")
    print(df.head())
    return df

def check_data_quality():
    """Check for data quality issues"""
    print("=== DATA QUALITY CHECK ===")
    print(f"Missing values per column:")
    print(df.isnull().sum())
    print(f"\nDuplicate rows: {df.duplicated().sum()}")
    print(f"Data types:\n{df.dtypes}")

# =============================================================================
# FILTERING AND SELECTION EXAMPLES
# =============================================================================

def filter_by_district(district_name):
    """Filter colleges by district"""
    return df[df['DIST_NAME'] == district_name]

def filter_by_thana(thana_name):
    """Filter colleges by thana"""
    return df[df['THANA_NAME'] == thana_name]

def filter_by_group(group_name):
    """Filter colleges by academic group"""
    valid_groups = ['Science', 'Humanities', 'Business Studies']
    if group_name not in valid_groups:
        raise ValueError(f"Group must be one of {valid_groups}")
    return df[df['GROUP'] == group_name]

def filter_by_shift(shift_name):
    """Filter colleges by shift"""
    valid_shifts = ['Day', 'Morning']
    if shift_name not in valid_shifts:
        raise ValueError(f"Shift must be one of {valid_shifts}")
    return df[df['SHIFT'] == shift_name]

def filter_by_version(version_name):
    """Filter colleges by version (medium)"""
    valid_versions = ['Bangla', 'English']
    if version_name not in valid_versions:
        raise ValueError(f"Version must be one of {valid_versions}")
    return df[df['VERSION'] == version_name]

def complex_filter_example():
    """Example of complex filtering: Science colleges in English version with Day shift"""
    return df[
        (df['GROUP'] == 'Science') & 
        (df['VERSION'] == 'English') & 
        (df['SHIFT'] == 'Day')
    ]

def search_by_college_name(name_pattern):
    """Search colleges by name pattern (case-insensitive)"""
    return df[df['COLLEGE_NA'].str.contains(name_pattern, case=False, na=False)]

def get_college_by_eiin(eiin_code):
    """Get specific college by EIIN code"""
    return df[df['EIIN'] == str(eiin_code)]

# =============================================================================
# ANALYSIS EXAMPLES
# =============================================================================

def analyze_by_district():
    """Analyze college distribution by district"""
    print("=== COLLEGE DISTRIBUTION BY DISTRICT ===")
    district_counts = df.groupby('DIST_NAME').agg({
        'EIIN': 'nunique',
        'COLLEGE_NA': 'count'
    }).rename(columns={'EIIN': 'Unique_Colleges', 'COLLEGE_NA': 'Total_Programs'})
    print(district_counts.sort_values('Unique_Colleges', ascending=False))
    return district_counts

def analyze_by_thana():
    """Analyze college distribution by thana"""
    print("=== TOP 10 THANAS BY COLLEGE COUNT ===")
    thana_counts = df.groupby('THANA_NAME')['EIIN'].nunique()
    print(thana_counts.sort_values(ascending=False).head(10))
    return thana_counts

def analyze_group_distribution():
    """Analyze distribution of academic groups"""
    print("=== ACADEMIC GROUP DISTRIBUTION ===")
    group_dist = df['GROUP'].value_counts()
    print(group_dist)
    print(f"\nPercentages:")
    print(df['GROUP'].value_counts(normalize=True) * 100)
    return group_dist

def analyze_shift_distribution():
    """Analyze shift distribution"""
    print("=== SHIFT DISTRIBUTION ===")
    shift_dist = df['SHIFT'].value_counts()
    print(shift_dist)
    return shift_dist

def analyze_version_distribution():
    """Analyze version (medium) distribution"""
    print("=== VERSION DISTRIBUTION ===")
    version_dist = df['VERSION'].value_counts()
    print(version_dist)
    return version_dist

def analyze_group_by_district():
    """Analyze group distribution by district"""
    print("=== GROUP DISTRIBUTION BY DISTRICT ===")
    group_district = pd.crosstab(df['DIST_NAME'], df['GROUP'])
    print(group_district)
    return group_district

def analyze_shift_by_group():
    """Analyze shift distribution by group"""
    print("=== SHIFT DISTRIBUTION BY GROUP ===")
    shift_group = pd.crosstab(df['GROUP'], df['SHIFT'])
    print(shift_group)
    return shift_group

def find_colleges_with_multiple_groups():
    """Find colleges offering multiple academic groups"""
    college_groups = df.groupby('EIIN')['GROUP'].nunique()
    multi_group_colleges = college_groups[college_groups > 1]
    print(f"=== COLLEGES OFFERING MULTIPLE GROUPS ===")
    print(f"Total such colleges: {len(multi_group_colleges)}")
    
    # Get details of these colleges
    multi_group_details = df[df['EIIN'].isin(multi_group_colleges.index)]
    print(multi_group_details[['EIIN', 'COLLEGE_NA', 'GROUP']].sort_values(['EIIN', 'GROUP']))
    return multi_group_details

def find_english_version_colleges():
    """Find all English version colleges"""
    print("=== ENGLISH VERSION COLLEGES ===")
    english_colleges = df[df['VERSION'] == 'English']
    print(f"Total English version programs: {len(english_colleges)}")
    print(f"Unique English version colleges: {english_colleges['EIIN'].nunique()}")
    print(english_colleges[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP']].head(20))
    return english_colleges

def find_morning_shift_colleges():
    """Find all morning shift colleges"""
    print("=== MORNING SHIFT COLLEGES ===")
    morning_colleges = df[df['SHIFT'] == 'Morning']
    print(f"Total morning shift programs: {len(morning_colleges)}")
    print(f"Unique morning shift colleges: {morning_colleges['EIIN'].nunique()}")
    print(morning_colleges[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP']].head(20))
    return morning_colleges

# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

def find_science_colleges_in_district(district_name):
    """Find all Science colleges in a specific district"""
    result = df[
        (df['DIST_NAME'] == district_name) & 
        (df['GROUP'] == 'Science')
    ]
    print(f"=== SCIENCE COLLEGES IN {district_name.upper()} ===")
    print(f"Total found: {len(result)}")
    print(result[['COLLEGE_NA', 'THANA_NAME', 'SHIFT', 'VERSION']])
    return result

def find_business_studies_colleges_in_thana(thana_name):
    """Find all Business Studies colleges in a specific thana"""
    result = df[
        (df['THANA_NAME'] == thana_name) & 
        (df['GROUP'] == 'Business Studies')
    ]
    print(f"=== BUSINESS STUDIES COLLEGES IN {thana_name.upper()} ===")
    print(f"Total found: {len(result)}")
    print(result[['COLLEGE_NA', 'SHIFT', 'VERSION']])
    return result

def search_colleges_by_criteria(district=None, thana=None, group=None, shift=None, version=None):
    """
    Search colleges by multiple criteria
    Parameters:
    - district: District name
    - thana: Thana name  
    - group: Academic group (Science, Humanities, Business Studies)
    - shift: Shift (Day, Morning)
    - version: Version (Bangla, English)
    """
    result = df.copy()
    
    if district:
        result = result[result['DIST_NAME'] == district]
    if thana:
        result = result[result['THANA_NAME'] == thana]
    if group:
        result = result[result['GROUP'] == group]
    if shift:
        result = result[result['SHIFT'] == shift]
    if version:
        result = result[result['VERSION'] == version]
    
    print(f"=== SEARCH RESULTS ===")
    print(f"Total records found: {len(result)}")
    if len(result) > 0:
        print(result[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP', 'SHIFT', 'VERSION']])
    else:
        print("No records found matching the criteria.")
    
    return result

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_filtered_data(filtered_df, filename):
    """Export filtered data to CSV"""
    filtered_df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")

def export_district_summary(filename="district_summary.csv"):
    """Export district-wise summary"""
    summary = df.groupby('DIST_NAME').agg({
        'EIIN': 'nunique',
        'COLLEGE_NA': ['count', 'nunique']
    }).round(2)
    summary.to_csv(filename)
    print(f"District summary exported to {filename}")

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Basic exploration
    basic_overview()
    check_data_quality()
    
    # Analysis examples
    analyze_by_district()
    analyze_by_thana()
    analyze_group_distribution()
    analyze_shift_distribution()
    analyze_version_distribution()
    
    # Search examples
    # find_science_colleges_in_district("DHAKA MAHANAGARI")
    # search_colleges_by_criteria(district="DHAKA MAHANAGARI", group="Science", shift="Morning")
    # search_by_college_name("IMPERIAL")
    
    # Complex filters
    # science_english_morning = complex_filter_example()
    # print(f"Science + English + Morning: {len(science_english_morning)} colleges")
    
    # Find special cases
    # find_colleges_with_multiple_groups()
    # find_english_version_colleges()
    # find_morning_shift_colleges()
