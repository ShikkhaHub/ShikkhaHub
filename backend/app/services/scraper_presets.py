"""Ready-made scrape configurations for common Bangladeshi education sources.

These presets encode the DOM structure conventions used across the country's
public portals (education boards, UGC, BMED, BTEB). Because every live portal
evolves, the presets are best treated as starting templates: the
``POST /scraping/extract`` endpoint lets an admin validate and tune selectors
against a live page before scheduling a full job.
"""

from typing import Dict

from app.services.scraper import FieldSelector, ScrapeConfig

PRESETS: Dict[str, ScrapeConfig] = {
    "education_board": ScrapeConfig(
        record_type="institution",
        item_selector=".institution, .school-list-item, table.institution-table tbody tr",
        fields=[
            FieldSelector("name_en", ".institution-name, h2, .name"),
            FieldSelector("eiin", ".eiin, [data-eiin]"),
            FieldSelector("education_board", ".board, .board-name", transform="lower"),
            FieldSelector("education_level", ".level, .institution-type", transform="lower"),
            FieldSelector("upazila", ".upazila, .thana"),
            FieldSelector("district", ".district, .zilla"),
            FieldSelector("address", ".address"),
            FieldSelector("established_year", ".established, .year", transform="year"),
        ],
        pagination_selector="a.next, .pagination .next",
        max_pages=1,
    ),
    "ugc_university": ScrapeConfig(
        record_type="institution",
        item_selector=".university-item, .uni-list li, table tbody tr",
        fields=[
            FieldSelector("name_en", ".uni-name, h3, .name"),
            FieldSelector("short_name", ".short-name, .abbr"),
            FieldSelector("university_affiliation", ".affiliation"),
            FieldSelector("district", ".district, .location"),
            FieldSelector("established_year", ".established", transform="year"),
            FieldSelector("website", "a.website", attribute="href", transform="url"),
            FieldSelector("ugc_approved", ".ugc-approved, .approved", transform="lower"),
        ],
        link_selector="a.uni-link, .uni-name a, h3 a",
        detail_fields=[
            FieldSelector("address", ".address"),
            FieldSelector("phone", ".phone", transform="phone"),
            FieldSelector("email", ".email", transform="email"),
            FieldSelector("description", ".about, .description"),
            FieldSelector("website", "a.website, .official-site", attribute="href"),
        ],
        pagination_selector=".pagination a.next, a.next-page",
        max_pages=1,
    ),
    "bmed_madrasa": ScrapeConfig(
        record_type="institution",
        item_selector=".madrasa-item, table tbody tr",
        fields=[
            FieldSelector("name_en", ".madrasa-name, h2"),
            FieldSelector("eiin", ".eiin"),
            FieldSelector("education_board", ".board", transform="lower"),
            FieldSelector("upazila", ".upazila"),
            FieldSelector("district", ".district"),
            FieldSelector("address", ".address"),
        ],
        pagination_selector=".pagination .next",
        max_pages=1,
    ),
    "bteb_polytechnic": ScrapeConfig(
        record_type="institution",
        item_selector=".institute-item, table tbody tr",
        fields=[
            FieldSelector("name_en", ".institute-name, h2"),
            FieldSelector("code", ".code, .institute-code"),
            FieldSelector("district", ".district"),
            FieldSelector("upazila", ".upazila"),
            FieldSelector("address", ".address"),
            FieldSelector("established_year", ".established", transform="year"),
        ],
        pagination_selector=".pagination .next",
        max_pages=1,
    ),
}


def get_preset(name: str) -> ScrapeConfig:
    """Look up a named preset, raising KeyError if unknown."""
    if name not in PRESETS:
        raise KeyError(f"unknown preset: {name}")
    return PRESETS[name]


def list_presets() -> Dict[str, Dict]:
    """Return preset metadata for discovery."""
    return {
        name: config.to_dict() for name, config in PRESETS.items()
    }
