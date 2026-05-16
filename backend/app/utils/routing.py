"""Google Routes API integration — Compute Route Matrix with caching."""
import hashlib
import datetime
from dataclasses import dataclass, field

import httpx

from app.config import settings


@dataclass
class RouteResult:
    """Result for a single origin-destination pair."""
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    distance_meters: int
    duration_seconds: int
    travel_mode: str


@dataclass
class RouteMatrixResponse:
    origin_lat: float
    origin_lng: float
    travel_mode: str
    results: list[RouteResult]
    cached_count: int = 0
    api_call_made: bool = False


def _make_cache_key(
    origin_lat: float, origin_lng: float,
    dest_lat: float, dest_lng: float,
    travel_mode: str,
) -> str:
    """SHA256 hash of rounded coordinates + mode as cache key."""
    raw = (
        f"{round(origin_lat, 5)}:{round(origin_lng, 5)}:"
        f"{round(dest_lat, 5)}:{round(dest_lng, 5)}:{travel_mode}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


_daily_call_count: dict[str, int] = {}


def _check_daily_limit() -> None:
    today = str(datetime.date.today())
    count = _daily_call_count.get(today, 0)
    if count >= settings.ROUTE_MATRIX_DAILY_API_LIMIT:
        raise RuntimeError(
            f"Daily route API call limit ({settings.ROUTE_MATRIX_DAILY_API_LIMIT}) reached"
        )
    _daily_call_count[today] = count + 1


async def _call_google_route_matrix(
    origin_lat: float,
    origin_lng: float,
    destinations: list[tuple[float, float]],
    travel_mode: str = "DRIVE",
) -> list[RouteResult]:
    """Call Google Routes API Compute Route Matrix.

    POST https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY is not configured")

    url = (
        "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
        "?fields=originIndex,destinationIndex,distanceMeters,duration"
    )
    headers = {
        "X-Goog-Api-Key": settings.GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "originIndex,destinationIndex,distanceMeters,duration",
        "Content-Type": "application/json",
    }
    body = {
        "origins": [{
            "waypoint": {
                "location": {
                    "latLng": {"latitude": origin_lat, "longitude": origin_lng}
                }
            }
        }],
        "destinations": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {"latitude": lat, "longitude": lng}
                    }
                }
            }
            for lat, lng in destinations
        ],
        "travelMode": travel_mode,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for entry in data:
        dest_idx = entry.get("destinationIndex", 0)
        dest_lat, dest_lng = destinations[dest_idx]
        duration_str = entry.get("duration", "0s")
        duration_val = int(duration_str.rstrip("s")) if duration_str else 0
        results.append(RouteResult(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            distance_meters=entry.get("distanceMeters", 0),
            duration_seconds=duration_val,
            travel_mode=travel_mode,
        ))
    return results
