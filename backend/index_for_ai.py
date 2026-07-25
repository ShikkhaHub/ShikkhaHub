#!/usr/bin/env python3
"""Index all institutions for AI RAG system."""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.ai_service import index_institutions_for_rag
from app.models import Institution

def index_all_institutions():
    """Index all institutions for AI search."""
    db = SessionLocal()
    
    try:
        # Get all institutions
        institutions = db.query(Institution).all()
        print(f"Found {len(institutions)} institutions to index for AI")
        
        # Prepare data
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
                "division_name": inst.upazila.district.division.name_en if inst.upazila and inst.upazila.district else None,
                "district_name": inst.upazila.district.name_en if inst.upazila else None,
                "upazila_name": inst.upazila.name_en if inst.upazila else None,
                "description": inst.description,
                "education_level": inst.education_level,
                "verification_status": inst.verification_status,
                "is_featured": inst.is_featured,
                "view_count": inst.view_count,
                "data_source": inst.data_source
            }
            institution_data.append(data)
        
        # Index for AI
        import asyncio
        asyncio.run(index_institutions_for_rag(institution_data))
        
        print(f"✅ Successfully indexed {len(institution_data)} institutions for AI search")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    index_all_institutions()
