"""Background worker: geocoding backfill, batch AI, cleanup tasks.

Run standalone: python -m app.worker
Or via Docker: python -c "from app.worker import run; import asyncio; asyncio.run(run())"
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import select, update

# Ensure app is on path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import AsyncSessionLocal
from app.models.property import Property
from app.utils.geo import geocode_nominatim, geocode_google, validate_latlng

logger = logging.getLogger("worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

GEOCODE_BATCH_SIZE = 20
SCAN_INTERVAL_SECONDS = 60 * 5  # scan every 5 minutes


async def backfill_property_geocoding() -> dict:
    """Find properties with addresses but no GPS, geocode them, backfill coordinates."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Property).where(
                Property.is_deleted == False,
                Property.address.isnot(None),
                Property.address != "",
                Property.latitude.is_(None),
            ).limit(GEOCODE_BATCH_SIZE)
        )
        props = list(result.scalars().all())

        if not props:
            return {"geocoded": 0, "skipped": 0, "errors": 0}

        geocoded = 0
        skipped = 0
        errors = 0

        for prop in props:
            if not prop.address:
                skipped += 1
                continue

            try:
                # Try Google first, then Nominatim
                results = await geocode_google(prop.address)
                if not results:
                    results = await geocode_nominatim(prop.address)

                if results:
                    best = results[0]
                    if validate_latlng(best.latitude, best.longitude):
                        prop.latitude = best.latitude
                        prop.longitude = best.longitude
                        geocoded += 1
                    else:
                        skipped += 1
                else:
                    skipped += 1
            except Exception:
                errors += 1

            # Rate-limit: small delay between geocoding calls
            await asyncio.sleep(0.5)

        await db.commit()
        return {"geocoded": geocoded, "skipped": skipped, "errors": errors}


async def run_forever():
    """Main worker loop — scans for pending tasks periodically."""
    logger.info("Worker started, scanning for background tasks...")
    while True:
        try:
            geo_result = await backfill_property_geocoding()
            if geo_result["geocoded"] > 0:
                logger.info(f"Geocoding backfill: {geo_result}")

        except Exception as e:
            logger.error(f"Worker cycle error: {e}")

        await asyncio.sleep(SCAN_INTERVAL_SECONDS)


async def run_once():
    """Run a single scan cycle (for manual execution)."""
    try:
        geo_result = await backfill_property_geocoding()
        logger.info(f"Geocoding backfill: {geo_result}")
    except Exception as e:
        logger.error(f"Worker error: {e}")


if __name__ == "__main__":
    asyncio.run(run_forever())
