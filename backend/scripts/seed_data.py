#!/usr/bin/env python3
"""
Seed initial data for ShikkhaHub.
Run: python scripts/seed_data.py
"""

import sys
sys.path.append(".")

import json

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models import (
    Division, District, Upazila,
    InstitutionType, EducationBoard, UniversityGrantCommission,
    FacilityType, RawSource,
    Campus, CampusPOI, CampusTour, TourStop, ARAsset,
    Skill, MarketDemand,
)

# Bangladesh Divisions (8)
DIVISIONS = [
    {"name_en": "Dhaka", "name_bn": "ঢাকা", "code": "DHK"},
    {"name_en": "Chittagong", "name_bn": "চট্টগ্রাম", "code": "CTG"},
    {"name_en": "Rajshahi", "name_bn": "রাজশাহী", "code": "RAJ"},
    {"name_en": "Khulna", "name_bn": "খুলনা", "code": "KHL"},
    {"name_en": "Barisal", "name_bn": "বরিশাল", "code": "BAR"},
    {"name_en": "Sylhet", "name_bn": "সিলেট", "code": "SYL"},
    {"name_en": "Rangpur", "name_bn": "রংপুর", "code": "RAN"},
    {"name_en": "Mymensingh", "name_bn": "ময়মনসিংহ", "code": "MYM"},
]

# Sample Districts (key ones per division - full 64 can be added)
DISTRICTS = {
    "Dhaka": [
        {"name_en": "Dhaka", "name_bn": "ঢাকা", "code": "DHK01"},
        {"name_en": "Gazipur", "name_bn": "গাজীপুর", "code": "DHK02"},
        {"name_en": "Narayanganj", "name_bn": "নারায়ণগঞ্জ", "code": "DHK03"},
        {"name_en": "Tangail", "name_bn": "টাঙ্গাইল", "code": "DHK04"},
        {"name_en": "Manikganj", "name_bn": "মানিকগঞ্জ", "code": "DHK05"},
    ],
    "Chittagong": [
        {"name_en": "Chittagong", "name_bn": "চট্টগ্রাম", "code": "CTG01"},
        {"name_en": "Cox's Bazar", "name_bn": "কক্সবাজার", "code": "CTG02"},
        {"name_en": "Comilla", "name_bn": "কুমিল্লা", "code": "CTG03"},
        {"name_en": "Feni", "name_bn": "ফেনী", "code": "CTG04"},
    ],
    "Rajshahi": [
        {"name_en": "Rajshahi", "name_bn": "রাজশাহী", "code": "RAJ01"},
        {"name_en": "Bogura", "name_bn": "বগুড়া", "code": "RAJ02"},
        {"name_en": "Pabna", "name_bn": "পাবনা", "code": "RAJ03"},
        {"name_en": "Natore", "name_bn": "নাটোর", "code": "RAJ04"},
    ],
    "Khulna": [
        {"name_en": "Khulna", "name_bn": "খুলনা", "code": "KHL01"},
        {"name_en": "Jessore", "name_bn": "যশোর", "code": "KHL02"},
        {"name_en": "Satkhira", "name_bn": "সাতক্ষীরা", "code": "KHL03"},
        {"name_en": "Bagerhat", "name_bn": "বাগেরহাট", "code": "KHL04"},
    ],
}

# Institution Types
INSTITUTION_TYPES = [
    {"name": "University", "category": "higher_education", "display_order": 1},
    {"name": "College", "category": "higher_education", "display_order": 2},
    {"name": "Polytechnic", "category": "technical", "display_order": 3},
    {"name": "School", "category": "secondary", "display_order": 4},
    {"name": "Institute", "category": "vocational", "display_order": 5},
    {"name": "Madrasa", "category": "secondary", "display_order": 6},
]

# Education Boards
EDUCATION_BOARDS = [
    {"name_en": "Dhaka Education Board", "name_bn": "ঢাকা শিক্ষা বোর্ড", "short_code": "dhaka", "board_type": "general"},
    {"name_en": "Chittagong Education Board", "name_bn": "চট্টগ্রাম শিক্ষা বোর্ড", "short_code": "ctg", "board_type": "general"},
    {"name_en": "Rajshahi Education Board", "name_bn": "রাজশাহী শিক্ষা বোর্ড", "short_code": "rajshahi", "board_type": "general"},
    {"name_en": "Comilla Education Board", "name_bn": "কুমিল্লা শিক্ষা বোর্ড", "short_code": "comilla", "board_type": "general"},
    {"name_en": "Jessore Education Board", "name_bn": "যশোর শিক্ষা বোর্ড", "short_code": "jessore", "board_type": "general"},
    {"name_en": "Sylhet Education Board", "name_bn": "সিলেট শিক্ষা বোর্ড", "short_code": "sylhet", "board_type": "general"},
    {"name_en": "Barisal Education Board", "name_bn": "বরিশাল শিক্ষা বোর্ড", "short_code": "barisal", "board_type": "general"},
    {"name_en": "Dinajpur Education Board", "name_bn": "দিনাজপুর শিক্ষা বোর্ড", "short_code": "dinajpur", "board_type": "general"},
    {"name_en": "Mymensingh Education Board", "name_bn": "ময়মনসিংহ শিক্ষা বোর্ড", "short_code": "mymensingh", "board_type": "general"},
    {"name_en": "Bangladesh Madrasah Education Board", "name_bn": "বাংলাদেশ মাদ্রাসা শিক্ষা বোর্ড", "short_code": "bmeb", "board_type": "madrasa"},
    {"name_en": "Bangladesh Technical Education Board", "name_bn": "বাংলাদেশ কারিগরি শিক্ষা বোর্ড", "short_code": "bteb", "board_type": "technical"},
]

# UGC and Higher Education Authorities
UGC_AUTHORITIES = [
    {"name_en": "University Grants Commission of Bangladesh", "name_bn": "বাংলাদেশ বিশ্ববিদ্যালয় মঞ্জুরী কমিশন", "short_code": "ugc_bd", "commission_type": "ugc"},
    {"name_en": "Bangladesh Medical and Dental Council", "name_bn": "বাংলাদেশ মেডিকেল অ্যান্ড ডেন্টাল কাউন্সিল", "short_code": "bmdc", "commission_type": "medical"},
    {"name_en": "Institution of Engineers Bangladesh", "name_bn": "ইঞ্জিনিয়ার্স ইনস্টিটিউশন বাংলাদেশ", "short_code": "ieb", "commission_type": "engineering"},
]

# Facility Types
FACILITY_TYPES = [
    {"name": "Hostel", "name_bn": "হোস্টেল", "icon": "🏠", "display_order": 1},
    {"name": "Library", "name_bn": "লাইব্রেরি", "icon": "📚", "display_order": 2},
    {"name": "WiFi", "name_bn": "ওয়াইফাই", "icon": "📶", "display_order": 3},
    {"name": "Transport", "name_bn": "পরিবহন", "icon": "🚌", "display_order": 4},
    {"name": "Cafeteria", "name_bn": "ক্যান্টিন", "icon": "🍽️", "display_order": 5},
    {"name": "Medical", "name_bn": "মেডিকেল", "icon": "🏥", "display_order": 6},
    {"name": "Playground", "name_bn": "খেলার মাঠ", "icon": "⚽", "display_order": 7},
    {"name": "Laboratory", "name_bn": "ল্যাবরেটরি", "icon": "🔬", "display_order": 8},
    {"name": "Auditorium", "name_bn": "অডিটোরিয়াম", "icon": "🎭", "display_order": 9},
    {"name": "Prayer Hall", "name_bn": "জামে মসজিদ", "icon": "🕌", "display_order": 10},
]

# Raw Data Sources
RAW_SOURCES = [
    {"name": "UGC", "name_bn": "ইউজিসি", "source_type": "government", "reliability_score": 0.95},
    {"name": "BMED", "name_bn": "মাদ্রাসা শিক্ষা বোর্ড", "source_type": "government", "reliability_score": 0.9},
    {"name": "Education Ministry", "name_bn": "শিক্ষা মন্ত্রণালয়", "source_type": "government", "reliability_score": 0.9},
    {"name": "Education Boards", "name_bn": "শিক্ষা বোর্ডসমূহ", "source_type": "government", "reliability_score": 0.9},
    {"name": "BTEB", "name_bn": "কারিগরি শিক্ষা বোর্ড", "source_type": "government", "reliability_score": 0.9},
    {"name": "Manual Entry", "name_bn": "ম্যানুয়াল এন্ট্রি", "source_type": "manual", "reliability_score": 0.5},
]


def seed_divisions(db: Session) -> None:
    """Seed Bangladesh divisions."""
    print("Seeding divisions...")
    for div_data in DIVISIONS:
        existing = db.query(Division).filter(Division.name_en == div_data["name_en"]).first()
        if not existing:
            division = Division(**div_data)
            db.add(division)
    db.commit()
    print(f"  ✓ Seeded {len(DIVISIONS)} divisions")


def seed_districts(db: Session) -> None:
    """Seed key districts."""
    print("Seeding districts...")
    count = 0
    for division_name, districts in DISTRICTS.items():
        division = db.query(Division).filter(Division.name_en == division_name).first()
        if division:
            for dist_data in districts:
                existing = db.query(District).filter(District.name_en == dist_data["name_en"]).first()
                if not existing:
                    district = District(
                        **dist_data,
                        division_id=division.id
                    )
                    db.add(district)
                    count += 1
    db.commit()
    print(f"  ✓ Seeded {count} districts")


def seed_institution_types(db: Session) -> None:
    """Seed institution types."""
    print("Seeding institution types...")
    for type_data in INSTITUTION_TYPES:
        existing = db.query(InstitutionType).filter(InstitutionType.name == type_data["name"]).first()
        if not existing:
            inst_type = InstitutionType(**type_data)
            db.add(inst_type)
    db.commit()
    print(f"  ✓ Seeded {len(INSTITUTION_TYPES)} institution types")


def seed_education_boards(db: Session) -> None:
    """Seed education boards."""
    print("Seeding education boards...")
    for board_data in EDUCATION_BOARDS:
        existing = db.query(EducationBoard).filter(EducationBoard.short_code == board_data["short_code"]).first()
        if not existing:
            board = EducationBoard(**board_data)
            db.add(board)
    db.commit()
    print(f"  ✓ Seeded {len(EDUCATION_BOARDS)} education boards")


def seed_ugc_authorities(db: Session) -> None:
    """Seed UGC and higher education authorities."""
    print("Seeding UGC authorities...")
    for auth_data in UGC_AUTHORITIES:
        existing = db.query(UniversityGrantCommission).filter(UniversityGrantCommission.short_code == auth_data["short_code"]).first()
        if not existing:
            auth = UniversityGrantCommission(**auth_data)
            db.add(auth)
    db.commit()
    print(f"  ✓ Seeded {len(UGC_AUTHORITIES)} authorities")


def seed_facility_types(db: Session) -> None:
    """Seed facility types."""
    print("Seeding facility types...")
    for fac_data in FACILITY_TYPES:
        existing = db.query(FacilityType).filter(FacilityType.name == fac_data["name"]).first()
        if not existing:
            db.add(FacilityType(**fac_data))
    db.commit()
    print(f"  ✓ Seeded {len(FACILITY_TYPES)} facility types")


def seed_raw_sources(db: Session) -> None:
    """Seed authoritative raw data sources."""
    print("Seeding raw data sources...")
    for src_data in RAW_SOURCES:
        existing = db.query(RawSource).filter(RawSource.name == src_data["name"]).first()
        if not existing:
            db.add(RawSource(**src_data))
    db.commit()
    print(f"  ✓ Seeded {len(RAW_SOURCES)} raw sources")


# Skill catalog and market demand signals (predictive skill gap analysis).
SKILLS = [
    {
        "name": "Data Analytics",
        "name_bn": "ডেটা অ্যানালিটিক্স",
        "category": "technical",
        "subcategory": "data",
        "description": "Collecting, cleaning and interpreting data to drive decisions.",
        "keywords": "data analysis, data analytics, analytics, sql, excel, python, tableau",
        "skill_level": "intermediate",
    },
    {
        "name": "Software Development",
        "name_bn": "সফটওয়্যার ডেভেলপমেন্ট",
        "category": "technical",
        "subcategory": "software",
        "description": "Designing, building and maintaining software applications.",
        "keywords": "software, programming, coding, developer, python, java, react, web",
        "skill_level": "intermediate",
    },
    {
        "name": "Artificial Intelligence",
        "name_bn": "কৃত্রিম বুদ্ধিমত্তা",
        "category": "emerging",
        "subcategory": "ai",
        "description": "Building intelligent systems: ML, NLP, computer vision.",
        "keywords": "artificial intelligence, machine learning, deep learning,"
                    " neural network, nlp, computer vision, ai",
        "skill_level": "advanced",
    },
    {
        "name": "Digital Marketing",
        "name_bn": "ডিজিটাল মার্কেটিং",
        "category": "soft_skill",
        "subcategory": "marketing",
        "description": "Promoting products and services through digital channels.",
        "keywords": "digital marketing, seo, social media, content marketing, google ads",
        "skill_level": "intermediate",
    },
    {
        "name": "English Communication",
        "name_bn": "ইংরেজি যোগাযোগ",
        "category": "soft_skill",
        "subcategory": "communication",
        "description": "Professional written and spoken English for the workplace.",
        "keywords": "english, communication, spoken english, ielts, business english",
        "skill_level": "intermediate",
    },
    {
        "name": "Freelancing",
        "name_bn": "ফ্রিল্যান্সিং",
        "category": "soft_skill",
        "subcategory": "entrepreneurship",
        "description": "Delivering services remotely to international clients.",
        "keywords": "freelancing, upwork, fiverr, remote work",
        "skill_level": "beginner",
    },
    {
        "name": "Cyber Security",
        "name_bn": "সাইবার নিরাপত্তা",
        "category": "emerging",
        "subcategory": "security",
        "description": "Protecting systems, networks and data from attacks.",
        "keywords": "cyber security, network security, ethical hacking, information security",
        "skill_level": "advanced",
    },
]

# Year -> (skill_name -> demand_score). Rising series signal emerging skills.
MARKET_DEMAND = {
    2022: {
        "Data Analytics": 58,
        "Software Development": 72,
        "Artificial Intelligence": 40,
        "Digital Marketing": 55,
        "English Communication": 70,
        "Freelancing": 62,
        "Cyber Security": 35,
    },
    2023: {
        "Data Analytics": 66,
        "Software Development": 78,
        "Artificial Intelligence": 52,
        "Digital Marketing": 60,
        "English Communication": 72,
        "Freelancing": 66,
        "Cyber Security": 44,
    },
    2024: {
        "Data Analytics": 74,
        "Software Development": 82,
        "Artificial Intelligence": 63,
        "Digital Marketing": 64,
        "English Communication": 71,
        "Freelancing": 64,
        "Cyber Security": 55,
    },
    2025: {
        "Data Analytics": 81,
        "Software Development": 85,
        "Artificial Intelligence": 74,
        "Digital Marketing": 66,
        "English Communication": 69,
        "Freelancing": 60,
        "Cyber Security": 66,
    },
}


def seed_skills(db: Session) -> None:
    """Seed the canonical skill catalog (idempotent)."""
    print("Seeding skills...")
    for s in SKILLS:
        existing = db.query(Skill).filter(Skill.name == s["name"]).first()
        if not existing:
            db.add(Skill(**s))
    db.commit()
    print(f"  ✓ Seeded {len(SKILLS)} skills")


def seed_market_demand(db: Session) -> None:
    """Seed demand-side signals per skill per year (idempotent)."""
    print("Seeding market demand signals...")
    count = 0
    for year, scores in MARKET_DEMAND.items():
        for skill_name, demand_score in scores.items():
            skill = db.query(Skill).filter(Skill.name == skill_name).first()
            if skill is None:
                continue
            existing = (
                db.query(MarketDemand)
                .filter(
                    MarketDemand.skill_id == skill.id,
                    MarketDemand.year == year,
                    MarketDemand.quarter.is_(None),
                )
                .first()
            )
            if existing:
                continue
            db.add(
                MarketDemand(
                    skill_id=skill.id,
                    year=year,
                    demand_score=demand_score,
                    postings_count=int(demand_score * 120),
                    hiring_growth_pct=round((demand_score - 40) / 4, 1),
                    source="job_portal_aggregate",
                    industry_sector="information_technology",
                    region="national",
                )
            )
            count += 1
    db.commit()
    print(f"  ✓ Seeded {count} market demand signals")


def seed_ar_demo(db):
    """Seed a sample AR campus tour for the first active campus.

    This demonstrates the AR data model (geolocated POIs + tour + assets).
    It is idempotent: skips if a campus already has POIs.
    """
    campus = db.query(Campus).filter(Campus.is_active.is_(True)).first()
    if campus is None:
        print("  ! No campus found — skipping AR demo seed")
        return
    if db.query(CampusPOI).filter(CampusPOI.campus_id == campus.id).first():
        print("  - AR POIs already seeded, skipping")
        return

    base_lat = campus.latitude or 23.8103
    base_lng = campus.longitude or 90.4125
    # ~0.00009 deg latitude ≈ 10m; use it to lay out a small walkable loop
    lat_step = 0.00009
    lng_step = 0.00011

    pois = [
        {
            "name_en": "Main Gate",
            "name_bn": "প্রধান ফটক",
            "category": "gate",
            "marker_type": "image_marker",
            "latitude": base_lat,
            "longitude": base_lng,
            "radius_m": 12,
            "title": "Main Gate",
            "short_description": "The main entrance to the campus.",
            "info_tags": json.dumps(["Open 24h", "Security desk"]),
            "display_order": 1,
        },
        {
            "name_en": "Admission Office",
            "name_bn": "ভর্তি অফিস",
            "category": "admission_office",
            "latitude": base_lat + lat_step * 2,
            "longitude": base_lng + lng_step,
            "radius_m": 15,
            "title": "Admission Office",
            "short_description": "Get admission forms and counselling.",
            "info_tags": json.dumps(["Sun-Thu 9am-4pm", "Phone: +8802-XXXXXXX"]),
            "display_order": 2,
        },
        {
            "name_en": "Central Library",
            "name_bn": "কেন্দ্রীয় গ্রন্থাগার",
            "category": "library",
            "latitude": base_lat + lat_step * 3,
            "longitude": base_lng,
            "radius_m": 20,
            "title": "Central Library",
            "short_description": "Home to 50,000+ books and study halls.",
            "info_tags": json.dumps(["Mon-Sat 8am-8pm", "Seats: 400"]),
            "department_summary": "Open stack, digital archive, reading rooms.",
            "opening_hours": "Mon-Sat 8am-8pm",
            "display_order": 3,
        },
        {
            "name_en": "Computer Science Dept",
            "name_bn": "কম্পিউটার বিজ্ঞান বিভাগ",
            "category": "department",
            "subcategory": "CSE",
            "latitude": base_lat + lat_step * 5,
            "longitude": base_lng + lng_step,
            "radius_m": 18,
            "title": "CSE Department",
            "short_description": "Modern labs and faculty offices.",
            "info_tags": json.dumps(["Labs: 4", "Faculty: 25"]),
            "department_summary": "BSc in CSE, AI, and Software Engineering.",
            "opening_hours": "Sun-Thu 9am-6pm",
            "display_order": 4,
        },
        {
            "name_en": "Cafeteria",
            "name_bn": "ক্যাফেটেরিয়া",
            "category": "cafeteria",
            "latitude": base_lat + lat_step * 4,
            "longitude": base_lng - lng_step,
            "radius_m": 10,
            "title": "Student Cafeteria",
            "short_description": "Affordable meals and snacks.",
            "info_tags": json.dumps(["Open 7am-9pm"]),
            "display_order": 5,
        },
    ]

    created = []
    for p in pois:
        poi = CampusPOI(
            campus_id=campus.id,
            institution_id=campus.institution_id,
            **p,
        )
        db.add(poi)
        db.flush()
        created.append(poi)

    # Lightweight primary asset for the library POI (marker image)
    lib = next(p for p in created if p.category == "library")
    db.add(
        ARAsset(
            poi_id=lib.id,
            asset_type="image",
            url="https://cdn.shikkhahub.dev/ar/library-marker.jpg",
            thumbnail_url="https://cdn.shikkhahub.dev/ar/library-marker-thumb.jpg",
            size_kb=42,
            format="jpeg",
            is_primary=True,
        )
    )

    # Curated tour chaining the POIs into a walkable loop
    tour = CampusTour(
        campus_id=campus.id,
        institution_id=campus.institution_id,
        title="Main Campus Highlights",
        title_bn="প্রধান ক্যাম্পাস সফর",
        description="A 20-minute AR walking tour of the main campus.",
        duration_minutes=20,
        difficulty="easy",
    )
    db.add(tour)
    db.flush()

    for position, poi in enumerate(created, start=1):
        db.add(
            TourStop(
                tour_id=tour.id,
                poi_id=poi.id,
                position=position,
                narration=f"Welcome to {poi.name_en}.",
                dwell_seconds=30,
            )
        )

    db.commit()
    print(f"  ✓ Seeded AR demo tour ({len(created)} POIs) for campus {campus.id}")


def main():
    print("=" * 50)
    print("ShikkhaHub Database Seeder")
    print("=" * 50)
    
    # Initialize database tables
    print("\nInitializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        seed_divisions(db)
        seed_districts(db)
        seed_institution_types(db)
        seed_education_boards(db)
        seed_ugc_authorities(db)
        seed_facility_types(db)
        seed_raw_sources(db)
        seed_ar_demo(db)
        seed_skills(db)
        seed_market_demand(db)
        
        print("\n" + "=" * 50)
        print("✓ Seeding completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
