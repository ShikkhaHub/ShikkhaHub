"""AR campus tour service.

Provides the geospatial logic behind augmented-reality campus tours:

- **Haversine distance** between two GPS coordinates (used to detect which
  campus/POI a user is near and to compute wayfinding distances).
- **Bearing** between POIs, so the AR client can draw arrows pointing from
  one stop to the next.
- **Nearby POI discovery** given a user's GPS position and radius.
- **Guided tour assembly** - chains POIs into an ordered route with
  distance/bearing legs between consecutive stops.

All coordinates are WGS84 (EPSG:4326) latitude/longitude degrees.
"""

import json
import math
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.ar import CampusPOI, CampusTour, TourStop

# Earth mean radius in metres
EARTH_RADIUS_M = 6371008.8


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two WGS84 points."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lng1: float, lat2: float, lng2: float) -> Optional[float]:
    """Initial bearing from point 1 to point 2 (degrees 0-360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlmb = math.radians(lng2 - lng1)

    y = math.sin(dlmb) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(
        dlmb
    )
    if x == 0 and y == 0:
        return None
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def walk_minutes(distance_m: float, speed_m_s: float = 1.4) -> float:
    """Estimated walking time at ~1.4 m/s (5 km/h)."""
    return round(distance_m / speed_m_s / 60, 1)


def _parse_tags(raw: Optional[str]) -> List[str]:
    """info_tags is stored as JSON; degrade gracefully."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except (ValueError, TypeError):
        return [t.strip() for t in raw.split(",") if t.strip()]


class ARTourService:
    """Geospatial helpers and tour assembly for AR campus tours."""

    @staticmethod
    def poi_with_assets(poi: CampusPOI) -> Dict[str, Any]:
        """Serialize a POI including its (lightweight) asset metadata."""
        return {
            "id": poi.id,
            "campus_id": poi.campus_id,
            "institution_id": poi.institution_id,
            "name_en": poi.name_en,
            "name_bn": poi.name_bn,
            "category": poi.category,
            "subcategory": poi.subcategory,
            "latitude": poi.latitude,
            "longitude": poi.longitude,
            "altitude_m": poi.altitude_m,
            "heading_deg": poi.heading_deg,
            "radius_m": poi.radius_m,
            "marker_type": poi.marker_type,
            "marker_image_url": poi.marker_image_url,
            "title": poi.title,
            "short_description": poi.short_description,
            "info_tags": _parse_tags(poi.info_tags),
            "department_summary": poi.department_summary,
            "opening_hours": poi.opening_hours,
            "display_order": poi.display_order,
            "is_active": poi.is_active,
            "assets": [
                {
                    "id": a.id,
                    "poi_id": a.poi_id,
                    "asset_type": a.asset_type,
                    "url": a.url,
                    "thumbnail_url": a.thumbnail_url,
                    "size_kb": a.size_kb,
                    "format": a.format,
                    "is_primary": a.is_primary,
                }
                for a in (poi.assets or [])
            ],
        }

    @staticmethod
    def find_nearby(
        db: Session,
        lat: float,
        lng: float,
        radius_m: float = 1000,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Find POIs within `radius_m` of the user's GPS position.

        Returns items sorted by distance with bearing and estimated walking
        time so the client can rank overlays by proximity.
        """
        pois = (
            db.query(CampusPOI)
            .filter(CampusPOI.is_active.is_(True))
        )
        if category:
            pois = pois.filter(CampusPOI.category == category)
        pois = pois.all()

        results = []
        for poi in pois:
            if poi.latitude is None or poi.longitude is None:
                continue
            dist = haversine_m(lat, lng, poi.latitude, poi.longitude)
            if dist > radius_m:
                continue
            results.append(
                {
                    "poi": ARTourService.poi_with_assets(poi),
                    "distance_m": round(dist, 1),
                    "bearing_deg": bearing_deg(lat, lng, poi.latitude, poi.longitude),
                    "estimated_walk_minutes": walk_minutes(dist),
                }
            )

        results.sort(key=lambda r: r["distance_m"])
        items = results[:limit]
        return {
            "user_lat": lat,
            "user_lng": lng,
            "radius_m": radius_m,
            "items": items,
            "total": len(items),
        }

    @staticmethod
    def list_campus_pois(
        db: Session, campus_id: int, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """All active POIs for a campus, ordered for display."""
        query = (
            db.query(CampusPOI)
            .filter(CampusPOI.campus_id == campus_id, CampusPOI.is_active.is_(True))
        )
        if category:
            query = query.filter(CampusPOI.category == category)
        pois = query.order_by(CampusPOI.display_order, CampusPOI.id).all()
        return [ARTourService.poi_with_assets(p) for p in pois]

    @staticmethod
    def get_tour(db: Session, tour_id: int) -> Optional[Dict[str, Any]]:
        """Return a tour with its ordered stops (POIs resolved)."""
        tour = db.query(CampusTour).filter(CampusTour.id == tour_id).first()
        if tour is None:
            return None
        return ARTourService._serialize_tour(tour)

    @staticmethod
    def list_campus_tours(db: Session, campus_id: int) -> List[Dict[str, Any]]:
        tours = (
            db.query(CampusTour)
            .filter(CampusTour.campus_id == campus_id, CampusTour.is_active.is_(True))
            .order_by(CampusTour.id)
            .all()
        )
        return [ARTourService._serialize_tour(t) for t in tours]

    @staticmethod
    def guided_tour(db: Session, tour_id: int) -> Optional[Dict[str, Any]]:
        """Assemble a guided route with wayfinding legs between stops.

        Each step carries the distance and bearing to the *next* stop so the
        AR client can draw on-screen arrows (wayfinding).
        """
        tour = db.query(CampusTour).filter(CampusTour.id == tour_id).first()
        if tour is None:
            return None

        stops = (
            db.query(TourStop)
            .filter(TourStop.tour_id == tour_id)
            .order_by(TourStop.position)
            .all()
        )
        steps = []
        prev_coords: Optional[Tuple[float, float]] = None
        for stop in stops:
            poi = stop.poi
            leg: Dict[str, Any] = {
                "position": stop.position,
                "poi": ARTourService.poi_with_assets(poi) if poi else None,
                "narration": stop.narration,
                "dwell_seconds": stop.dwell_seconds,
            }
            if poi and poi.latitude is not None and poi.longitude is not None:
                coords = (poi.latitude, poi.longitude)
                if prev_coords:
                    dist = haversine_m(
                        prev_coords[0], prev_coords[1], coords[0], coords[1]
                    )
                    leg["distance_from_prev_m"] = round(dist, 1)
                    leg["bearing_from_prev_deg"] = bearing_deg(
                        prev_coords[0], prev_coords[1], coords[0], coords[1]
                    )
                prev_coords = coords
            steps.append(leg)

        total_distance = 0.0
        for i in range(1, len(steps)):
            leg = steps[i]
            if leg.get("distance_from_prev_m"):
                total_distance += leg["distance_from_prev_m"]

        return {
            "tour": ARTourService._serialize_tour(tour),
            "total_distance_m": round(total_distance, 1),
            "steps": steps,
        }

    @staticmethod
    def _serialize_tour(tour: CampusTour) -> Dict[str, Any]:
        return {
            "id": tour.id,
            "campus_id": tour.campus_id,
            "institution_id": tour.institution_id,
            "title": tour.title,
            "title_bn": tour.title_bn,
            "description": tour.description,
            "duration_minutes": tour.duration_minutes,
            "distance_m": tour.distance_m,
            "difficulty": tour.difficulty,
            "is_active": tour.is_active,
            "created_at": tour.created_at.isoformat() if tour.created_at else None,
            "stops": [
                {
                    "id": s.id,
                    "tour_id": s.tour_id,
                    "poi_id": s.poi_id,
                    "position": s.position,
                    "narration": s.narration,
                    "dwell_seconds": s.dwell_seconds,
                }
                for s in tour.stops
            ],
        }
