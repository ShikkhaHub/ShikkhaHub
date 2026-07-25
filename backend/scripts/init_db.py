#!/usr/bin/env python3
"""
Initialize database tables and seed with initial data.
Run: python scripts/init_db.py
"""

import sys
sys.path.append(".")

from app.core.database import init_db, engine, Base
from scripts.seed_data import main as seed_data

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created successfully")

print("\nSeeding initial data...")
seed_data()
print("\n✓ Database initialization complete!")
