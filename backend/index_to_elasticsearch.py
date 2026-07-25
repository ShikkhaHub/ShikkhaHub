#!/usr/bin/env python3
"""Index all institutions to Elasticsearch."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.elasticsearch import bulk_index_institutions, ensure_index_exists
from app.models import Institution

def index_all_institutions():
    """Index all institutions from database to Elasticsearch."""
    db = SessionLocal()
    
    try:
        # Ensure index exists
        ensure_index_exists()
        
        # Get all institutions
        institutions = db.query(Institution).all()
        print(f"Found {len(institutions)} institutions to index")
        
        # Prepare data for indexing
        institution_data = []
        for inst in institutions:
            data = {
                "id": inst.id,
                "name_en": inst.name_en,
                "name_bn": inst.name_bn,
                "short_name": inst.short_name,
                "slug": inst.slug,
                "type_id": inst.type_id,
                "type_name": inst.type.name if inst.type else None,
                "established_year": inst.established_year,
                "address": inst.address,
                "division_name": inst.upazila.district.division.name_en if inst.upazila and inst.upazila.district and inst.upazila.district.division else None,
                "district_name": inst.upazila.district.name_en if inst.upazila and inst.upazila.district else None,
                "upazila_name": inst.upazila.name_en if inst.upazila else None,
                "description": inst.description,
                "education_level": inst.education_level,
                "verification_status": inst.verification_status,
                "is_featured": inst.is_featured,
                "view_count": inst.view_count,
                "data_source": inst.data_source
            }
            institution_data.append(data)
        
        # Bulk index
        if institution_data:
            success = bulk_index_institutions(institution_data)
            if success:
                print(f"✅ Successfully indexed {len(institution_data)} institutions")
            else:
                print("❌ Failed to index institutions")
        else:
            print("No institutions to index")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    index_all_institutions()
