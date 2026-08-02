"""CKAN data catalog endpoints for ShikkhaHub services.

Exposes the CKAN catalog as the trusted metadata layer:
- dataset search by category/status/organization
- dataset detail with resources and metadata
- DCAT export (interoperability)
- catalog status / organizations / groups
- dataset publication (admin)

Consumed by the website, mobile app, AI assistant and analytics pipelines.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.core.ckan import get_ckan_client
from app.services.ckan import CKANService, get_ckan_service
from app.schemas.ckan import (
    CKANDatasetCreate,
    CKANDatasetUpdate,
    CKANSearchResponse,
    CKANStatusResponse,
)
from app.core.security import get_current_user
from app.models import User

router = APIRouter()


@router.get("/status", response_model=CKANStatusResponse)
def ckan_status(service: CKANService = Depends(get_ckan_service)):
    """Catalog health and configuration."""
    return service.status()


@router.get("/datasets", response_model=CKANSearchResponse)
def search_datasets(
    q: str = Query("", description="Full-text dataset search"),
    category: Optional[str] = Query(None, description="Dataset category"),
    verification_status: Optional[str] = Query(None, description="Verification status"),
    organization: Optional[str] = Query(None, description="CKAN organization"),
    rows: int = Query(20, ge=1, le=100),
    start: int = Query(0, ge=0),
    service: CKANService = Depends(get_ckan_service),
):
    """Search datasets in the national education catalog."""
    return service.search_datasets(
        query=q,
        category=category,
        verification_status=verification_status,
        organization=organization,
        rows=rows,
        start=start,
    )


@router.get("/datasets/{name_or_id}")
def get_dataset(
    name_or_id: str,
    service: CKANService = Depends(get_ckan_service),
):
    """Get a single dataset with its resources and metadata."""
    dataset = service.get_dataset(name_or_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.get("/organizations")
def list_organizations(service: CKANService = Depends(get_ckan_service)):
    """List catalog organizations (Ministry of Education, UGC, boards, ...)."""
    return service.list_organizations()


@router.get("/groups")
def list_groups(service: CKANService = Depends(get_ckan_service)):
    """List catalog groups (Higher Education, Medical, Engineering, ...)."""
    return service.list_groups()


@router.get("/dcat/{format}")
def dcat_export(
    format: str = "rdf",
    client=Depends(get_ckan_client),
):
    """DCAT metadata export (rdf | xml | jsonld) for interoperability."""
    if format not in ("rdf", "xml", "jsonld"):
        raise HTTPException(status_code=400, detail="format must be rdf, xml or jsonld")
    catalog = client.dcat_catalog(format)
    if catalog is None:
        raise HTTPException(status_code=503, detail="DCAT catalog unavailable")
    return {"format": format, "catalog": catalog}


# --------------------------------------------------------------- admin
@router.post("/datasets", response_model=dict)
def create_dataset(
    payload: CKANDatasetCreate,
    current_user: User = Depends(get_current_user),
    service: CKANService = Depends(get_ckan_service),
):
    """Publish a dataset to the catalog (requires admin or verifier)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")

    name = payload.name or service.client.make_slug(payload.title)
    data = payload.model_dump(exclude={"name"})
    data["name"] = name
    if payload.resources:
        data["resources"] = [r.model_dump(exclude_none=True) for r in payload.resources]

    result = service.client.dataset_publish(**data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to publish dataset")
    return result


@router.patch("/datasets/{name_or_id}", response_model=dict)
def update_dataset(
    name_or_id: str,
    payload: CKANDatasetUpdate,
    current_user: User = Depends(get_current_user),
    service: CKANService = Depends(get_ckan_service),
):
    """Partially update a dataset (admin only)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")

    data = payload.model_dump(exclude_none=True)
    if data.get("resources"):
        data["resources"] = [r.model_dump(exclude_none=True) for r in payload.resources or []]

    result = service.client.package_patch(name_or_id, data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update dataset")
    return result


@router.post("/sync/institutions")
def sync_institutions(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    service: CKANService = Depends(get_ckan_service),
):
    """Publish verified institutions to CKAN (admin trigger)."""
    if not current_user.is_admin():
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.core.database import get_db
    from app.models import Institution

    db = next(get_db())
    try:
        institutions = (
            db.query(Institution)
            .filter(Institution.is_active.is_(True))
            .order_by(Institution.id.desc())
            .limit(limit)
            .all()
        )
        return service.publish_institutions(institutions)
    finally:
        db.close()
