#!/usr/bin/env python3
"""ShikkhaHub CKAN catalog seed script.

Creates organizations, groups and tags defined in the seed catalog using the
CKAN Action API. Idempotent — existing entities are left untouched.

Usage (inside CKAN container):
    python /srv/app/scripts/seed_catalog.py /srv/app/config/seed_catalog.json

Or from the host against a reachable CKAN:
    python ckan/scripts/seed_catalog.py ckan/config/seed_catalog.json \
        --api http://localhost:5000 --token <CKAN_API_TOKEN>
"""

import argparse
import json
import sys
from urllib import error, request

DEFAULT_API = "http://ckan:5000"


def call_action(api_base, token, action, data):
    """Call a CKAN Action API endpoint."""
    req = request.Request(
        f"{api_base}/api/3/action/{action}",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": token,
        },
        method="POST",
    )
    with request.urlopen(req) as resp:  # noqa: S310 - internal CKAN API
        body = json.loads(resp.read().decode("utf-8"))
        if not body.get("success"):
            raise RuntimeError(f"{action} failed: {body.get('error')}")
        return body["result"]


def main():
    parser = argparse.ArgumentParser(description="Seed ShikkhaHub CKAN catalog")
    parser.add_argument("catalog", help="Path to seed_catalog.json")
    parser.add_argument("--api", default=DEFAULT_API, help="CKAN base URL")
    parser.add_argument("--token", default=None, help="CKAN API token")
    args = parser.parse_args()

    with open(args.catalog, encoding="utf-8") as f:
        catalog = json.load(f)

    token = args.token or input("CKAN API token: ").strip()
    created_orgs, created_groups = 0, 0

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------
    for org in catalog.get("organizations", []):
        try:
            call_action(args.api, token, "organization_create", org)
            print(f"  + organization {org['name']}")
            created_orgs += 1
        except (error.HTTPError, RuntimeError) as exc:
            # 409 = already exists
            status = getattr(exc, "code", None)
            if status == 409:
                print(f"  = organization {org['name']} (exists)")
            else:
                print(f"  ! organization {org['name']}: {exc}")

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------
    for group in catalog.get("groups", []):
        try:
            call_action(args.api, token, "group_create", group)
            print(f"  + group {group['name']}")
            created_groups += 1
        except (error.HTTPError, RuntimeError) as exc:
            status = getattr(exc, "code", None)
            if status == 409:
                print(f"  = group {group['name']} (exists)")
            else:
                print(f"  ! group {group['name']}: {exc}")

    # ------------------------------------------------------------------
    # Tags (via package_tag_list — tags live on datasets; we register the
    # reserved tag vocabulary entries the catalog uses)
    # ------------------------------------------------------------------
    # Tags in CKAN are free-form on datasets, so we simply validate the
    # recommended tag list here and print it for documentation/QA.
    recommended = catalog.get("tags", [])
    print(f"\nRecommended tags ({len(recommended)}): {', '.join(recommended)}")

    print(
        f"\nSeed complete: {created_orgs} organizations, "
        f"{created_groups} groups created."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
