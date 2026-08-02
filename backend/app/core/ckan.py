"""CKAN data catalog client for ShikkhaHub.

Wraps the CKAN Action API (https://docs.ckan.org/en/latest/api/index.html) as
the trusted metadata layer for the national education platform. ShikkhaHub
services consume verified datasets from CKAN rather than raw scrapers:

- dataset search (institution, admission, programs, results, ...)
- metadata discovery
- resource download links
- dataset publication / versioning
- DCAT export endpoints

All calls are idempotent where possible and fail soft (return None / empty)
when CKAN is unreachable, so the backend keeps working if the catalog is down.
"""

import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from urllib import error, request

from app.core.config import settings

logger = logging.getLogger(__name__)

# CKAN verification statuses (scheming dataset.yaml)
CKAN_VERIFICATION_STATUSES = {
    "collected",
    "pending_review",
    "verified",
    "published",
    "archived",
}


class CKANClient:
    """Minimal CKAN Action API client."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        self.api_url = (api_url or settings.CKAN_API_URL).rstrip("/")
        self.token = token or settings.CKAN_API_TOKEN
        self.timeout = timeout or settings.CKAN_TIMEOUT_SECONDS

    # ------------------------------------------------------------------ http
    def _call(self, action: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """POST to a CKAN action endpoint. Returns result dict or None."""
        if not settings.CKAN_ENABLED:
            return None

        payload = json.dumps(data or {}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token

        req = request.Request(
            f"{self.api_url}/{action}",
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
                body = json.loads(resp.read().decode("utf-8"))
                if not body.get("success"):
                    logger.warning("CKAN %s returned success=false: %s", action, body.get("error"))
                    return None
                return body.get("result")
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("CKAN %s request failed: %s", action, exc)
            return None

    def _get(self, action: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """GET-style action (solr search) via query params."""
        if not settings.CKAN_ENABLED:
            return None

        from urllib.parse import urlencode

        url = f"{self.api_url}/{action}?{urlencode(query, doseq=True)}"
        headers = {}
        if self.token:
            headers["Authorization"] = self.token
        try:
            req_obj = request.Request(url, headers=headers)
            with request.urlopen(req_obj, timeout=self.timeout) as resp:  # noqa: S310
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("result") if body.get("success") else None
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("CKAN %s failed: %s", action, exc)
            return None

    # ------------------------------------------------------------- status
    def status(self) -> Optional[Dict[str, Any]]:
        """CKAN status_show — health probe."""
        return self._call("status_show")

    def is_healthy(self) -> bool:
        return self.status() is not None

    # ------------------------------------------------------------ dataset
    def package_create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a dataset. `name` must be globally unique (slug)."""
        return self._call("package_create", data)

    def package_update(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a dataset by id or name (version bump / edit)."""
        return self._call("package_update", data)

    def package_patch(self, name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Partially update a dataset."""
        return self._call("package_patch", {"id": name, **data})

    def package_show(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single dataset with resources and metadata."""
        return self._call("package_show", {"id": name_or_id})

    def package_delete(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        return self._call("package_delete", {"id": name_or_id})

    def package_purge(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        return self._call("package_purge", {"id": name_or_id})

    def package_search(
        self,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        rows: int = 20,
        start: int = 0,
        include_private: bool = False,
        sort: str = "metadata_modified desc",
    ) -> Dict[str, Any]:
        """Full-text dataset search (Solr-backed) with facet filters.

        `filters` keys map to schema fields, e.g.:
            {"dataset_category": "institutions", "verification_status": "published"}
        """
        query_params: Dict[str, Any] = {
            "q": query,
            "rows": rows,
            "start": start,
            "sort": sort,
            "include_private": str(include_private).lower(),
        }
        if filters:
            query_params["fq"] = " ".join(
                f'+{k}:"{v}"' for k, v in filters.items() if v
            )
        return self._get("package_search", query_params) or {
            "results": [],
            "count": 0,
        }

    def dataset_publish(
        self,
        *,
        title: str,
        name: str,
        dataset_category: str,
        description: str,
        owner_org: Optional[str] = None,
        tags: Optional[List[str]] = None,
        groups: Optional[List[str]] = None,
        resources: Optional[List[Dict[str, Any]]] = None,
        verification_status: str = "pending_review",
        extras: Optional[Dict[str, Any]] = None,
        update: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Create or update a dataset with the ShikkhaHub metadata standard.

        Args:
            title: Human-readable dataset title
            name: URL slug (must be unique)
            dataset_category: institutions | admission | academic_programs |
                results | rankings | scholarships | job_career | geographic
            owner_org: CKAN organization name/id (default settings.CKAN_ORG)
            verification_status: collected | pending_review | verified |
                published | archived
            update: if True and dataset exists, update instead of failing
        """
        if verification_status not in CKAN_VERIFICATION_STATUSES:
            logger.warning("Invalid verification_status %r", verification_status)
            return None

        payload: Dict[str, Any] = {
            "name": name,
            "title": title,
            "dataset_category": dataset_category,
            "description": description,
            "verification_status": verification_status,
            "owner_org": owner_org or settings.CKAN_ORG,
            "extras": [{"key": k, "value": v} for k, v in (extras or {}).items()],
        }
        if tags:
            payload["tags"] = [{"name": t} for t in tags]
        if groups:
            payload["groups"] = [{"name": g} for g in groups]
        if resources:
            payload["resources"] = resources

        existing = self.package_show(name)
        if existing and update:
            payload["id"] = existing["id"]
            return self.package_update(payload)
        return self.package_create(payload)

    # ------------------------------------------------------------ resource
    def resource_create(self, dataset_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._call("resource_create", {"package_id": dataset_name, **data})

    def resource_show(self, resource_id: str) -> Optional[Dict[str, Any]]:
        return self._call("resource_show", {"id": resource_id})

    def resource_download_url(self, resource_id: str) -> Optional[str]:
        """Public download URL for a resource."""
        if not settings.CKAN_ENABLED:
            return None
        return f"{settings.CKAN_URL}/dataset/{resource_id}/download"

    # ------------------------------------------------------ organization
    def organization_list(self) -> List[str]:
        result = self._call("organization_list", {}) or []
        return result if isinstance(result, list) else []

    def organization_show(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        return self._call("organization_show", {"id": name_or_id})

    def organization_create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._call("organization_create", data)

    # --------------------------------------------------------------- group
    def group_list(self) -> List[str]:
        result = self._call("group_list", {}) or []
        return result if isinstance(result, list) else []

    def group_show(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        return self._call("group_show", {"id": name_or_id})

    def group_create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._call("group_create", data)

    # -------------------------------------------------------------- tag
    def tag_list(self) -> List[Dict[str, Any]]:
        result = self._call("tag_list", {"all_fields": True, "limit": 100}) or []
        return result if isinstance(result, list) else []

    # ------------------------------------------------------------- DCAT
    def dcat_catalog(self, format: str = "rdf") -> Optional[str]:
        """Fetch the DCAT-exported catalog (rdf | xml | jsonld)."""
        if not settings.CKAN_ENABLED:
            return None
        url = f"{settings.CKAN_URL}/catalog.{format}"
        try:
            with request.urlopen(url, timeout=self.timeout) as resp:  # noqa: S310
                return resp.read().decode("utf-8")
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            logger.warning("DCAT fetch failed: %s", exc)
            return None

    # ------------------------------------------------------------ helpers
    @staticmethod
    def make_slug(value: str, max_length: int = 80) -> str:
        """Deterministic URL slug for CKAN dataset names."""
        import re

        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        if len(slug) > max_length:
            slug = slug[: max_length - 9].rstrip("-")
        return slug or f"dataset-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def checksum(content: bytes) -> str:
        """SHA-256 of resource bytes (resource metadata integrity)."""
        return hashlib.sha256(content).hexdigest()


# Lazy singleton
_ckan_client: Optional[CKANClient] = None


def get_ckan_client() -> CKANClient:
    """Get or create the shared CKAN client."""
    global _ckan_client
    if _ckan_client is None:
        _ckan_client = CKANClient()
    return _ckan_client
