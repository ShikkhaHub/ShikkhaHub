#!/usr/bin/env python3
"""
Seed initial data for ShikkhaHub.
Run: python scripts/seed_data.py
"""

import sys
sys.path.append(".")

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models import (
    Division, District, Upazila,
    InstitutionType, EducationBoard, UniversityGrantCommission
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
