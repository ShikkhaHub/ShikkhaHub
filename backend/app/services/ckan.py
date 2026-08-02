"""CKAN data catalog service — bridges ShikkhaHub domain data to CKAN.

Consumed by API routers and the ETL sync pipeline. The service normalizes
ShikkhaHub SQLAlchemy records into CKAN dataset payloads following the
national metadata standard (docs/DB_SCHEMA_AUDIT.md, ckan/config/scheming/).
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.ckan import CKANClient, get_ckan_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# Dataset category <-> CKAN group mapping (from the plan)
CATEGORY_GROUPS = {
    "institutions": [
        "higher-education",
        "school",
        "college",
        "technical",
        "medical",
        "engineering",
    ],
    "admission": ["admission"],
    "academic_programs": ["higher-education", "technical", "engineering"],
    "results": ["results"],
    "rankings": ["higher-education"],
    "scholarships": ["scholarships"],
    "job_career": ["jobs"],
    "geographic": ["school", "college", "technical"],
}

VERIFICATION_TO_CKAN = {
    "verified": "verified",
    "official": "published",
    "pending": "pending_review",
    "flagged": "pending_review",
    "unverified": "collected",
}


def _resource_dict(resource) -> Dict[str, Any]:
    """Serialize a resource-like object (SQLAlchemy row or dict)."""
    if isinstance(resource, dict):
        return resource
    out: Dict[str, Any] = {}
    for attr in ("url", "format", "name", "description", "resource_type", "checksum"):
        value = getattr(resource, attr, None)
        if value:
            out[attr] = value
    return out


def institution_to_dataset(
    institution, category: str = "institutions"
) -> Dict[str, Any]:
    """Build a CKAN dataset payload from an Institution record."""
    name_bn = getattr(institution, "name_bn", None) or ""
    coverage = "national"
    division = getattr(getattr(institution, "division", None), "name_en", None)
    if division:
        coverage = division

    verification = getattr(institution, "verification_status", None) or "pending"
    status = VERIFICATION_TO_CKAN.get(verification, "pending_review")

    # Location extras
    extras: Dict[str, Any] = {
        "institution_id": getattr(institution, "id", None),
        "eiin": getattr(institution, "eiin", None),
        "name_bn": name_bn,
        "institution_type": getattr(getattr(institution, "type", None), "name", None),
        "ownership": getattr(institution, "ownership", None),
        "education_level": getattr(institution, "education_level", None),
        "established_year": getattr(institution, "established_year", None),
        "division": division,
        "district": getattr(getattr(institution, "district", None), "name_en", None),
        "upazila": getattr(getattr(institution, "upazila", None), "name_en", None),
        "latitude": getattr(institution, "latitude", None),
        "longitude": getattr(institution, "longitude", None),
        "website": getattr(institution, "website", None),
        "phone": getattr(institution, "phone", None),
        "email": getattr(institution, "email", None),
        "ugc_approved": getattr(institution, "ugc_approved", None),
        "board": getattr(institution, "board", None),
    }
    extras = {k: v for k, v in extras.items() if v is not None}

    title = institution.name_en
    if name_bn and name_bn != title:
        title = f"{title} ({name_bn})"

    return {
        "title": title,
        "name": f"{category}-{institution.slug}"[:80].rstrip("-"),
        "dataset_category": category,
        "description": getattr(institution, "description", None) or title,
        "verification_status": status,
        "version": "1.0.0",
        "source_type": (
            "government"
            if getattr(institution, "data_source", None)
            in ("ugc", "bteb", "bmeb", "board")
            else "manual"
        ),
        "source_url": getattr(institution, "website", None),
        "coverage": coverage,
        "tags": list(dict.fromkeys(["institution", category.rstrip("s"), status])),
        "groups": [{"name": g} for g in CATEGORY_GROUPS.get(category, [])],
        "extras": extras,
    }


class CKANService:
    """High-level CKAN operations used by routers and the ETL pipeline."""

    def __init__(self, client: Optional[CKANClient] = None) -> None:
        self.client = client or get_ckan_client()

    # ------------------------------------------------------------- status
    def status(self) -> Dict[str, Any]:
        if not settings.CKAN_ENABLED:
            return {"enabled": False, "api_url": settings.CKAN_API_URL}
        status = self.client.status() or {}
        orgs = self.client.organization_list()
        groups = self.client.group_list()
        return {
            "enabled": True,
            "healthy": bool(status),
            "api_url": settings.CKAN_API_URL,
            "version": status.get("ckan_version"),
            "organization_count": len(orgs) if isinstance(orgs, list) else None,
            "group_count": len(groups) if isinstance(groups, list) else None,
        }

    # ----------------------------------------------------------- search
    def search_datasets(
        self,
        query: str = "",
        category: Optional[str] = None,
        verification_status: Optional[str] = None,
        organization: Optional[str] = None,
        rows: int = 20,
        start: int = 0,
    ) -> Dict[str, Any]:
        filters: Dict[str, Any] = {}
        if category:
            filters["dataset_category"] = category
        if verification_status:
            filters["verification_status"] = verification_status
        if organization:
            filters["owner_org"] = organization

        result = self.client.package_search(
            query=query,
            filters=filters or None,
            rows=rows,
            start=start,
            include_private=False,
        )
        return {
            "results": result.get("results", []),
            "count": result.get("count", 0),
            "start": start,
            "rows": rows,
        }

    # ----------------------------------------------------- catalog browse
    def get_dataset(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        return self.client.package_show(name_or_id)

    def list_organizations(self) -> List[Dict[str, Any]]:
        names = self.client.organization_list()
        out = []
        for name in names:
            org = self.client.organization_show(name)
            if org:
                out.append(
                    {
                        "id": org.get("id"),
                        "name": org.get("name"),
                        "title": org.get("title"),
                    }
                )
        return out

    def list_groups(self) -> List[Dict[str, Any]]:
        names = self.client.group_list()
        out = []
        for name in names:
            grp = self.client.group_show(name)
            if grp:
                out.append(
                    {
                        "id": grp.get("id"),
                        "name": grp.get("name"),
                        "title": grp.get("title"),
                    }
                )
        return out

    # -------------------------------------------------------- publication
    def publish_institutions(self, institutions) -> Dict[str, int]:
        """Publish a batch of Institution records to CKAN (idempotent)."""
        published, updated, failed = 0, 0, 0
        for inst in institutions:
            payload = institution_to_dataset(inst)
            try:
                existing = self.client.package_show(payload["name"])
                if existing:
                    payload["id"] = existing["id"]
                    result = self.client.package_update(payload)
                    if result:
                        updated += 1
                    else:
                        failed += 1
                else:
                    result = self.client.package_create(payload)
                    if result:
                        published += 1
                    else:
                        failed += 1
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to publish institution %s: %s", inst.id, exc)
                failed += 1
        return {"published": published, "updated": updated, "failed": failed}


# Lazy singleton
_ckan_service: Optional[CKANService] = None


def get_ckan_service() -> CKANService:
    global _ckan_service
    if _ckan_service is None:
        _ckan_service = CKANService()
    return _ckan_service
