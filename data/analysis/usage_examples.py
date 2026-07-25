"""
Usage Examples for Educational Data Analysis
============================================

This file demonstrates how to use the data analysis functions
with the Dhaka Education Board college data.
"""

from data_analysis_guide import (
    df, filter_by_district, filter_by_group, filter_by_shift, filter_by_version,
    search_by_college_name, get_college_by_eiin, search_colleges_by_criteria,
    find_science_colleges_in_district, analyze_by_district, analyze_group_distribution
)

# =============================================================================
# EXAMPLE 1: Basic Filtering
# =============================================================================

print("EXAMPLE 1: Find all colleges in DHAKA MAHANAGARI district")
print("=" * 60)
dhaka_mahanagari = filter_by_district("DHAKA MAHANAGARI")
print(f"Found {len(dhaka_mahanagari)} records")
print(dhaka_mahanagari[['COLLEGE_NA', 'THANA_NAME', 'GROUP']].head(10))
print()

# =============================================================================
# EXAMPLE 2: Filter by Academic Group
# =============================================================================

print("EXAMPLE 2: Find all Science colleges")
print("=" * 60)
science_colleges = filter_by_group("Science")
print(f"Found {len(science_colleges)} Science programs")
print(f"Unique colleges offering Science: {science_colleges['EIIN'].nunique()}")
print(science_colleges[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME']].head(10))
print()

# =============================================================================
# EXAMPLE 3: Filter by Shift
# =============================================================================

print("EXAMPLE 3: Find all Morning shift colleges")
print("=" * 60)
morning_colleges = filter_by_shift("Morning")
print(f"Found {len(morning_colleges)} Morning shift programs")
print(morning_colleges[['COLLEGE_NA', 'DIST_NAME', 'GROUP']].head(10))
print()

# =============================================================================
# EXAMPLE 4: Filter by Version (Medium)
# =============================================================================

print("EXAMPLE 4: Find all English version colleges")
print("=" * 60)
english_colleges = filter_by_version("English")
print(f"Found {len(english_colleges)} English version programs")
print(english_colleges[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP']].head(10))
print()

# =============================================================================
# EXAMPLE 5: Search by College Name
# =============================================================================

print("EXAMPLE 5: Search for colleges containing 'CANTONMENT'")
print("=" * 60)
cantonment_colleges = search_by_college_name("CANTONMENT")
print(f"Found {len(cantonment_colleges)} colleges")
print(cantonment_colleges[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP', 'SHIFT']])
print()

# =============================================================================
# EXAMPLE 6: Get College by EIIN
# =============================================================================

print("EXAMPLE 6: Get college by EIIN 107825")
print("=" * 60)
college_107825 = get_college_by_eiin("107825")
print(college_107825[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'GROUP', 'SHIFT', 'VERSION']])
print()

# =============================================================================
# EXAMPLE 7: Complex Search with Multiple Criteria
# =============================================================================

print("EXAMPLE 7: Find Science colleges in DHAKA MAHANAGARI with Day shift")
print("=" * 60)
result = search_colleges_by_criteria(
    district="DHAKA MAHANAGARI",
    group="Science", 
    shift="Day"
)
print()

# =============================================================================
# EXAMPLE 8: District-wise Analysis
# =============================================================================

print("EXAMPLE 8: Analyze college distribution by district")
print("=" * 60)
district_summary = analyze_by_district()
print()

# =============================================================================
# EXAMPLE 9: Group Distribution Analysis
# =============================================================================

print("EXAMPLE 9: Analyze academic group distribution")
print("=" * 60)
group_summary = analyze_group_distribution()
print()

# =============================================================================
# EXAMPLE 10: Find Science Colleges in Specific District
# =============================================================================

print("EXAMPLE 10: Find Science colleges in DHAKA MAHANAGARI district")
print("=" * 60)
science_in_dhaka = find_science_colleges_in_district("DHAKA MAHANAGARI")
print()

# =============================================================================
# EXAMPLE 11: Custom Analysis - Colleges offering all three groups
# =============================================================================

print("EXAMPLE 11: Find colleges offering all three academic groups")
print("=" * 60)
college_group_counts = df.groupby('EIIN')['GROUP'].nunique()
colleges_all_groups = college_group_counts[college_group_counts == 3]
print(f"Colleges offering all 3 groups: {len(colleges_all_groups)}")

if len(colleges_all_groups) > 0:
    # Get details of these colleges
    all_group_colleges = df[df['EIIN'].isin(colleges_all_groups.index)]
    college_info = all_group_colleges[['EIIN', 'COLLEGE_NA', 'DIST_NAME', 'THANA_NAME']].drop_duplicates()
    print(college_info.head(10))
print()

# =============================================================================
# EXAMPLE 12: English version Science colleges
# =============================================================================

print("EXAMPLE 12: Find English version Science colleges")
print("=" * 60)
english_science = df[
    (df['VERSION'] == 'English') & 
    (df['GROUP'] == 'Science')
]
print(f"Found {len(english_science)} English version Science programs")
print(f"Unique colleges: {english_science['EIIN'].nunique()}")
print(english_science[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME', 'SHIFT']].head(10))
print()

# =============================================================================
# EXAMPLE 13: Morning shift Business Studies colleges
# =============================================================================

print("EXAMPLE 13: Find Morning shift Business Studies colleges")
print("=" * 60)
morning_business = df[
    (df['SHIFT'] == 'Morning') & 
    (df['GROUP'] == 'Business Studies')
]
print(f"Found {len(morning_business)} Morning shift Business Studies programs")
print(morning_business[['COLLEGE_NA', 'DIST_NAME', 'THANA_NAME']].head(10))
print()

# =============================================================================
# EXAMPLE 14: Top 10 Thanas by number of colleges
# =============================================================================

print("EXAMPLE 14: Top 10 Thanas by number of colleges")
print("=" * 60)
thana_counts = df.groupby('THANA_NAME')['EIIN'].nunique().sort_values(ascending=False)
print(thana_counts.head(10))
print()

# =============================================================================
# EXAMPLE 15: Export filtered data
# =============================================================================

print("EXAMPLE 15: Export Science colleges to separate file")
print("=" * 60)
from data_analysis_guide import export_filtered_data
science_colleges = filter_by_group("Science")
export_filtered_data(science_colleges, "science_colleges_only.csv")
print()
