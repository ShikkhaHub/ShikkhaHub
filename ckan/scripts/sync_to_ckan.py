#!/usr/bin/env python3
"""ShikkhaHub -> CKAN ETL sync script.

Pushes verified institution data from the ShikkhaHub PostgreSQL database into
the CKAN data catalog as datasets following the national metadata standard.

Run:
    python ckan/scripts/sync_to_ckan.py \
        --db postgresql://postgres:postgres@localhost:5432/shikkhahub \
        --ckan http://localhost:5000 --token <CKAN_API_TOKEN> \
        --limit 100
"""

import argparse
import json
import logging
import sys
from typing import Dict
from urllib import error, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ CKAN call
def call_action(api: str, token: str, action: str, data: Dict):
    req = request.Request(
        f"{api}/api/3/action/{action}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": token},
        method="POST",
    )
    try:
        with request.urlopen(req) as resp:  # noqa: S310
            body = json.loads(resp.read().decode("utf-8"))
            return body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        logger.error("CKAN %s HTTP %s: %s", action, exc.code, body[:500])
        return {"success": False, "error": {"code": exc.code}}


def package_show(api: str, token: str, name: str):
    return call_action(api, token, "package_show", {"id": name})


def package_create(api: str, token: str, data: Dict):
    return call_action(api, token, "package_create", data)


def package_update(api: str, token: str, data: Dict):
    return call_action(api, token, "package_update", data)


# ------------------------------------------------------------- transformation
def institution_to_payload(row) -> Dict:
    """Build a CKAN dataset payload from a database row (dict or row-mapped)."""
    def g(key, default=None):
        return row.get(key, default) if isinstance(row, dict) else getattr(row, key, default)

    name_en = g("name_en")
    name_bn = g("name_bn")
    title = f"{name_en} ({name_bn})" if name_bn else name_en

    verification_map = {"verified": "verified", "official": "published", "pending": "pending_review"}
    status = verification_map.get(g("verification_status", "pending"), "pending_review")

    extras = {
        "institution_id": g("id"),
        "eiin": g("eiin"),
        "name_bn": name_bn,
        "institution_type": g("type"),
        "ownership": g("ownership"),
        "education_level": g("education_level"),
        "established_year": g("established_year"),
        "division": g("division"),
        "district": g("district"),
        "upazila": g("upazila"),
        "latitude": g("latitude"),
        "longitude": g("longitude"),
        "website": g("website"),
        "phone": g("phone"),
        "email": g("email"),
        "ugc_approved": g("ugc_approved"),
        "board": g("board"),
    }
    extras = {k: v for k, v in extras.items() if v is not None}

    return {
        "title": title,
        "name": f"institutions-{g('slug')}"[:80].rstrip("-"),
        "dataset_category": "institutions",
        "description": g("description") or name_en,
        "verification_status": status,
        "version": "1.0.0",
        "owner_org": "shikkhahub",
        "source_type": "government" if g("data_source") in ("ugc", "bteb", "bmeb", "board") else "manual",
        "source_url": g("website"),
        "coverage": g("division", "national"),
        "tags": list(dict.fromkeys(["institution", "institution", status])),
        "extras": [{"key": k, "value": str(v)} for k, v in extras.items()],
    }


# -------------------------------------------------------------------- main
def main():
    parser = argparse.ArgumentParser(description="Sync ShikkhaHub DB -> CKAN")
    parser.add_argument("--db", required=True, help="SQLAlchemy database URL")
    parser.add_argument("--ckan", default="http://localhost:5000", help="CKAN base URL")
    parser.add_argument("--token", required=True, help="CKAN API token")
    parser.add_argument("--limit", type=int, default=100, help="Max institutions to sync")
    parser.add_argument("--verification", default="verified", help="Only sync this verification status")
    args = parser.parse_args()

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        logger.error("sqlalchemy not installed — run `pip install sqlalchemy`")
        sys.exit(1)

    engine = create_engine(args.db)
    api = f"{args.ckan.rstrip('/')}/api/3/action"

    query = text(
        """
        SELECT i.id, i.name_en, i.name_bn, i.slug, i.description, i.website,
               i.eiin, i.ownership, i.education_level, i.established_year,
               i.latitude, i.longitude, i.phone, i.email, i.ugc_approved,
               i.board, i.data_source, i.verification_status,
               it.name AS type, dv.name_en AS division, ds.name_en AS district,
               up.name_en AS upazila
        FROM institutions i
        LEFT JOIN institution_types it ON it.id = i.type_id
        LEFT JOIN divisions dv ON dv.id = i.division_id
        LEFT JOIN districts ds ON ds.id = i.district_id
        LEFT JOIN upazilas up ON up.id = i.upazila_id
        WHERE i.is_active = TRUE
          AND i.verification_status = :vstatus
        ORDER BY i.id
        LIMIT :lim
        """
    )

    created = updated = failed = skipped = 0
    with engine.connect() as conn:
        rows = conn.execute(query, {"vstatus": args.verification, "lim": args.limit}).mappings().all()

        logger.info("Fetched %d institutions to sync", len(rows))
        for row in rows:
            payload = institution_to_payload(row)
            existing = package_show(api, args.token, payload["name"])
            if existing.get("success"):
                payload["id"] = existing["result"]["id"]
                result = package_update(api, args.token, payload)
                if result.get("success"):
                    updated += 1
                else:
                    failed += 1
            else:
                result = package_create(api, args.token, payload)
                if result.get("success"):
                    created += 1
                else:
                    failed += 1

    logger.info("Sync complete: created=%d updated=%d failed=%d skipped=%d",
                created, updated, failed, skipped)
    sys.exit(0)


if __name__ == "__main__":
    main()
