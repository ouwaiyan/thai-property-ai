"""Geospatial utilities — Haversine distance, Google/Nominatim geocoding, PostGIS helpers."""
import hashlib
import math
import os

import httpx
from geoalchemy2.elements import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings


def validate_latlng(lat: float | None, lng: float | None) -> bool:
    """Validate latitude/longitude ranges (Thailand region check)."""
    if lat is None or lng is None:
        return True
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return False
    if not (5.0 <= lat <= 21.0) or not (97.0 <= lng <= 106.0):
        return False
    return True


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in meters between two points."""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─── PostGIS Helpers ───────────────────────────────────────────────

def make_point_wkt(lat: float, lng: float, srid: int = 4326) -> WKTElement:
    """Create a WKTElement for a geographic point (longitude latitude order)."""
    return WKTElement(f"POINT({lng} {lat})", srid=srid)


# ─── Geocoding ────────────────────────────────────────────────────

class GeocodingResult:
    def __init__(self, latitude: float, longitude: float, display_name: str, provider: str = "nominatim"):
        self.latitude = latitude
        self.longitude = longitude
        self.display_name = display_name
        self.provider = provider


# L1 in-memory cache
_l1_cache: dict[str, list[GeocodingResult]] = {}
_CACHE_MAX_SIZE = 500


def _cache_key(query: str) -> str:
    return hashlib.md5(query.strip().lower().encode()).hexdigest()


async def _geocode_from_db(db: AsyncSession, query: str) -> list[GeocodingResult] | None:
    """Look up geocoding result from database cache (L2)."""
    from app.models.geocode_cache import GeocodeCache
    result = await db.execute(
        select(GeocodeCache).where(GeocodeCache.query_text == query.strip().lower())
    )
    rows = result.scalars().all()
    if not rows:
        return None
    return [
        GeocodingResult(
            latitude=row.latitude,
            longitude=row.longitude,
            display_name=row.display_name or query,
            provider=row.provider,
        )
        for row in rows
    ]


async def _geocode_save_to_db(db: AsyncSession, query: str, results: list[GeocodingResult]) -> None:
    """Save geocoding results to database cache (L2)."""
    from app.models.geocode_cache import GeocodeCache
    import uuid
    clean_query = query.strip().lower()
    for r in results:
        entry = GeocodeCache(
            id=uuid.uuid4().hex,
            query_text=clean_query,
            latitude=r.latitude,
            longitude=r.longitude,
            display_name=r.display_name,
            provider=r.provider,
        )
        db.add(entry)
    await db.flush()


async def geocode_google(query: str, country_codes: str = "th") -> list[GeocodingResult]:
    """Geocode using Google Maps Geocoding API."""
    if not settings.GOOGLE_MAPS_API_KEY:
        return []
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": settings.GOOGLE_MAPS_API_KEY,
        "region": country_codes,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    if data.get("status") != "OK":
        return []

    results = []
    for item in data.get("results", []):
        loc = item.get("geometry", {}).get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")
        if lat is not None and lng is not None:
            results.append(GeocodingResult(
                latitude=float(lat),
                longitude=float(lng),
                display_name=item.get("formatted_address", query),
                provider="google",
            ))
    return results


async def geocode_nominatim(query: str, country_codes: str = "th") -> list[GeocodingResult]:
    """Geocode using Nominatim (OpenStreetMap) — free, rate-limited."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "countrycodes": country_codes, "limit": 5}
    headers = {"User-Agent": "ThaiEstate/1.0 (contact@thaiestate.com)"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    return [
        GeocodingResult(
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
            display_name=item.get("display_name", query),
            provider="nominatim",
        )
        for item in data
    ]


async def geocode(query: str, db: AsyncSession | None = None) -> list[GeocodingResult]:
    """Geocode an address string to coordinates.

    Cache layers: L1 (memory) → L2 (database) → API (Google → Nominatim).
    When db is provided, results are persisted to L2.
    """
    key = _cache_key(query)

    # L1: in-memory cache
    if key in _l1_cache:
        return _l1_cache[key]

    # L2: database cache
    if db is not None:
        db_results = await _geocode_from_db(db, query)
        if db_results:
            _l1_cache[key] = db_results
            return db_results

    # L3: API lookup — Google first, Nominatim fallback
    results = await geocode_google(query)
    if not results:
        results = await geocode_nominatim(query)

    # Save to caches
    if results:
        _l1_cache[key] = results
        # Trim L1 cache if too large
        if len(_l1_cache) > _CACHE_MAX_SIZE:
            oldest = next(iter(_l1_cache))
            del _l1_cache[oldest]
        if db is not None:
            try:
                await _geocode_save_to_db(db, query, results)
            except Exception:
                pass  # non-critical

    return results


async def geocode_with_db(query: str, db: AsyncSession) -> list[GeocodingResult]:
    """Convenience wrapper that always passes db for persistence."""
    return await geocode(query, db=db)
