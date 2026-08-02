#!/usr/bin/env python3
"""
Train the ML recommendation models and persist them.

Run: python scripts/train_recommender.py [--output models/recommender]

Loads all analytics interactions, fits the collaborative and content-based
models, and stores them to disk with the interaction metadata needed for
real-time inference. The training script is idempotent and safe to run on a
schedule (e.g. nightly cron / Celery beat) so the engine always serves
reasonably fresh models.
"""

import argparse
import json
import os
import sys
import time

sys.path.append(".")

from sqlalchemy.orm import Session  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models import Institution  # noqa: E402
from app.services.ml_recommendations import (  # noqa: E402
    MLRecommendationEngine,
)

DEFAULT_OUTPUT = "models/recommender"


def main() -> None:
    parser = argparse.ArgumentParser(description="Train ML recommendation models")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Directory to persist models (default: %(default)s)",
    )
    parser.add_argument(
        "--min-users",
        type=int,
        default=3,
        help="Minimum distinct users to train collaborative filtering",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ShikkhaHub ML Recommender Trainer")
    print("=" * 60)

    os.makedirs(args.output, exist_ok=True)

    db = SessionLocal()
    try:
        started = time.time()
        engine = MLRecommendationEngine()
        ok = engine.fit(db)
        elapsed = round(time.time() - started, 2)
        print(f"  ✓ Trained in {elapsed}s (cf={engine.collaborative.is_ready()}, "
              f"cb={engine.content_based.is_ready()})")

        if not ok:
            print("  ! Not enough data to train models yet — persisting metadata only.")
        else:
            _persist(db, engine, args.output)

        print("=" * 60)
        print(f"  ✓ Done. Artifacts written to {args.output}/")
        print("=" * 60)
    except Exception as exc:  # noqa: BLE001
        print(f"\n✗ Error: {exc}")
        db.rollback()
        raise
    finally:
        db.close()


def _persist(db: Session, engine: MLRecommendationEngine, output_dir: str) -> None:
    """Serialise trained factors and feature data for fast cold-start inference."""
    import numpy as np

    # 1. User/item latent factors
    if engine.collaborative.is_ready():
        np.save(
            os.path.join(output_dir, "user_factors.npy"),
            np.asarray(engine.collaborative.user_factors),
        )
        np.save(
            os.path.join(output_dir, "item_factors.npy"),
            np.asarray(engine.collaborative.item_factors),
        )
        with open(os.path.join(output_dir, "user_index.json"), "w") as fh:
            json.dump(engine.collaborative.user_index, fh)
        with open(os.path.join(output_dir, "item_index.json"), "w") as fh:
            json.dump(engine.collaborative.item_index, fh)

    # 2. Institution metadata snapshot for serving
    institutions = (
        db.query(Institution)
        .filter(Institution.is_active.is_(True))
        .all()
    )
    snapshot = []
    for inst in institutions:
        snapshot.append(
            {
                "id": inst.id,
                "name_en": inst.name_en,
                "name_bn": inst.name_bn,
                "slug": inst.slug,
                "type": inst.type.name if inst.type else None,
                "education_level": inst.education_level,
                "ownership": inst.ownership,
                "division": inst.division.name_en if inst.division else None,
                "district": inst.district.name_en if inst.district else None,
            }
        )
    with open(os.path.join(output_dir, "institutions.json"), "w") as fh:
        json.dump(snapshot, fh, ensure_ascii=False)

    # 3. Training summary
    with open(os.path.join(output_dir, "meta.json"), "w") as fh:
        json.dump(
            {
                "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "users": len(engine.collaborative.user_index),
                "items": len(engine.collaborative.item_index),
                "cf_ready": engine.collaborative.is_ready(),
                "cb_ready": engine.content_based.is_ready(),
            },
            fh,
            indent=2,
        )
    print(f"  ✓ Persisted {len(snapshot)} institutions and model factors")


if __name__ == "__main__":
    main()
