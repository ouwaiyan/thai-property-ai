"""Route matrix business logic — cache-first, Google Routes API for misses."""
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.route_cache import RouteCache
from app.utils.geo import haversine_distance
from app.utils.redis_client import get_cache, set_cache
from app.utils.routing import (
    RouteResult,
    RouteMatrixResponse,
    _make_cache_key,
    _call_google_route_matrix,
    _check_daily_limit,
)


def _is_expired(entry: RouteCache) -> bool:
    cutoff = datetime.utcnow() - timedelta(days=settings.ROUTE_MATRIX_CACHE_TTL_DAYS)
    return entry.updated_at.replace(tzinfo=None) < cutoff


def _haversine_fallback(
    cache_keys: list[str],
    cached_map: dict[str, RouteCache],
    origin_lat: float,
    origin_lng: float,
    misses: list[tuple[int, float, float]],
    travel_mode: str,
) -> None:
    """Fill cache misses with Haversine estimates."""
    speeds = {"DRIVE": 1.4, "WALK": 1.2, "TRANSIT": 1.25}
    factor = speeds.get(travel_mode, 1.4)
    for idx, lat, lng in misses:
        key = cache_keys[idx]
        d = haversine_distance(origin_lat, origin_lng, lat, lng)
        cached_map[key] = RouteCache(
            cache_key=key,
            origin_lat=origin_lat, origin_lng=origin_lng,
            dest_lat=lat, dest_lng=lng,
            travel_mode=travel_mode,
            distance_meters=int(d),
            duration_seconds=int(d / factor),
        )


async def get_route_matrix(
    db: AsyncSession,
    origin_lat: float,
    origin_lng: float,
    destinations: list[tuple[float, float]],
    travel_mode: str = "DRIVE",
) -> RouteMatrixResponse:
    """Compute route distances/durations for origin -> multiple destinations.

    Checks route_cache table first; only calls Google API for cache misses.
    Falls back to Haversine estimates when no API key is configured or API fails.
    Capped at ROUTE_MATRIX_MAX_CANDIDATES destinations.
    """
    if len(destinations) > settings.ROUTE_MATRIX_MAX_CANDIDATES:
        destinations = destinations[:settings.ROUTE_MATRIX_MAX_CANDIDATES]

    if not destinations:
        return RouteMatrixResponse(
            origin_lat=origin_lat, origin_lng=origin_lng,
            travel_mode=travel_mode, results=[],
        )

    cache_keys = [
        _make_cache_key(origin_lat, origin_lng, lat, lng, travel_mode)
        for lat, lng in destinations
    ]

    # L1: Redis cache (fastest)
    cached_map: dict[str, RouteCache] = {}
    redis_keys_to_fetch: list[str] = []
    for i, key in enumerate(cache_keys):
        entry = cached_map.get(key)
        if entry is None:
            redis_keys_to_fetch.append(key)

    # Check DB cache
    cache_result = await db.execute(
        select(RouteCache).where(RouteCache.cache_key.in_(cache_keys))
    )
    for row in cache_result.scalars().all():
        cached_map[row.cache_key] = row
        # Backfill Redis
        try:
            await set_cache(f"route:{row.cache_key}", {
                "distance_meters": row.distance_meters,
                "duration_seconds": row.duration_seconds,
                "travel_mode": row.travel_mode,
            }, ttl_seconds=settings.ROUTE_MATRIX_CACHE_TTL_DAYS * 86400)
        except Exception:
            pass

    # Check Redis for keys not in DB
    for key in cache_keys:
        if key not in cached_map:
            redis_entry = await get_cache(f"route:{key}")
            if redis_entry:
                cached_map[key] = RouteCache(
                    cache_key=key,
                    distance_meters=redis_entry["distance_meters"],
                    duration_seconds=redis_entry["duration_seconds"],
                    travel_mode=redis_entry.get("travel_mode", travel_mode),
                )

    # Find cache misses
    misses: list[tuple[int, float, float]] = []
    for i, (lat, lng) in enumerate(destinations):
        entry = cached_map.get(cache_keys[i])
        if entry is None or (hasattr(entry, 'updated_at') and _is_expired(entry)):
            misses.append((i, lat, lng))

    api_call_made = False
    if misses:
        if not settings.GOOGLE_MAPS_API_KEY:
            _haversine_fallback(cache_keys, cached_map, origin_lat, origin_lng, misses, travel_mode)
        else:
            try:
                _check_daily_limit()
            except RuntimeError:
                _haversine_fallback(cache_keys, cached_map, origin_lat, origin_lng, misses, travel_mode)
            else:
                miss_coords = [(lat, lng) for _, lat, lng in misses]
                try:
                    api_results = await _call_google_route_matrix(
                        origin_lat, origin_lng, miss_coords, travel_mode,
                    )
                    api_call_made = True
                    for result in api_results:
                        key = _make_cache_key(
                            result.origin_lat, result.origin_lng,
                            result.dest_lat, result.dest_lng,
                            result.travel_mode,
                        )
                        await db.merge(RouteCache(
                            cache_key=key,
                            origin_lat=result.origin_lat,
                            origin_lng=result.origin_lng,
                            dest_lat=result.dest_lat,
                            dest_lng=result.dest_lng,
                            travel_mode=result.travel_mode,
                            distance_meters=result.distance_meters,
                            duration_seconds=result.duration_seconds,
                        ))
                        # Also cache in Redis
                        try:
                            await set_cache(f"route:{key}", {
                                "distance_meters": result.distance_meters,
                                "duration_seconds": result.duration_seconds,
                                "travel_mode": result.travel_mode,
                            }, ttl_seconds=settings.ROUTE_MATRIX_CACHE_TTL_DAYS * 86400)
                        except Exception:
                            pass
                except Exception:
                    _haversine_fallback(cache_keys, cached_map, origin_lat, origin_lng, misses, travel_mode)

    # Build results in original order
    results = []
    for i, (lat, lng) in enumerate(destinations):
        entry = cached_map.get(cache_keys[i])
        if entry:
            results.append(RouteResult(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                dest_lat=lat,
                dest_lng=lng,
                distance_meters=entry.distance_meters,
                duration_seconds=entry.duration_seconds,
                travel_mode=travel_mode,
            ))

    cached_count = len(destinations) - len(misses)

    return RouteMatrixResponse(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        travel_mode=travel_mode,
        results=results,
        cached_count=cached_count,
        api_call_made=api_call_made,
    )
