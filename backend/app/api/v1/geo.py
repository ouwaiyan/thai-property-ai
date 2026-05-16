from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.dependencies import get_db
from app.models.property import Property
from app.models.user import User
from app.utils.geo import geocode, geocode_google, geocode_nominatim, validate_latlng

router = APIRouter(prefix="/geo", tags=["Geo"])


class GeocodeRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


class GeocodeResponseItem(BaseModel):
    latitude: float
    longitude: float
    display_name: str
    provider: str = "nominatim"


class GeocodeBackfillResult(BaseModel):
    total_no_gps: int
    geocoded: int
    skipped: int
    errors: int


@router.post("/geocode", response_model=list[GeocodeResponseItem])
async def geocode_address(
    body: GeocodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = await geocode(body.query, db=db)
    return [
        GeocodeResponseItem(
            latitude=r.latitude,
            longitude=r.longitude,
            display_name=r.display_name,
            provider=r.provider,
        )
        for r in results
    ]


@router.post("/backfill", response_model=GeocodeBackfillResult)
async def trigger_geocode_backfill(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin: manually trigger geocoding backfill for properties without GPS."""
    result = await db.execute(
        select(func.count(Property.id)).where(
            Property.is_deleted == False,
            Property.address.isnot(None),
            Property.address != "",
            Property.latitude.is_(None),
        )
    )
    total_no_gps = result.scalar() or 0

    if total_no_gps == 0:
        return GeocodeBackfillResult(total_no_gps=0, geocoded=0, skipped=0, errors=0)

    props_result = await db.execute(
        select(Property).where(
            Property.is_deleted == False,
            Property.address.isnot(None),
            Property.address != "",
            Property.latitude.is_(None),
        ).limit(50)
    )
    props = list(props_result.scalars().all())

    geocoded = 0
    skipped = 0
    errors = 0

    for prop in props:
        if not prop.address:
            skipped += 1
            continue
        try:
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

    await db.commit()

    return GeocodeBackfillResult(
        total_no_gps=total_no_gps,
        geocoded=geocoded,
        skipped=skipped,
        errors=errors,
    )
