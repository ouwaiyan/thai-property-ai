from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.dependencies import get_db
from app.models.property import Property
from app.models.user import User
from app.services.routing_service import get_route_matrix

router = APIRouter(prefix="/transit", tags=["Transit"])


class RouteMatrixRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    property_ids: list[str] = Field(..., min_length=1, max_length=50)
    travel_mode: str = Field(default="DRIVE", pattern="^(DRIVE|WALK|TRANSIT)$")


class RouteMatrixItem(BaseModel):
    property_id: str
    distance_meters: int
    duration_seconds: int
    travel_mode: str


class RouteMatrixResponse(BaseModel):
    origin_lat: float
    origin_lng: float
    travel_mode: str
    results: list[RouteMatrixItem]
    cached_count: int
    api_call_made: bool


@router.post("/route-matrix", response_model=RouteMatrixResponse)
async def compute_route_matrix(
    body: RouteMatrixRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute real commute distance/duration from origin to properties."""
    prop_result = await db.execute(
        select(Property.id, Property.latitude, Property.longitude)
        .where(Property.id.in_(body.property_ids))
        .where(Property.latitude.isnot(None))
        .where(Property.longitude.isnot(None))
    )
    props: dict[str, tuple[float, float]] = {}
    for r in prop_result.all():
        if r[1] is not None and r[2] is not None:
            props[str(r[0])] = (r[1], r[2])

    destinations = []
    ordered_ids = []
    for pid in body.property_ids:
        coords = props.get(pid)
        if coords:
            ordered_ids.append(pid)
            destinations.append(coords)

    matrix = await get_route_matrix(
        db=db,
        origin_lat=body.origin_lat,
        origin_lng=body.origin_lng,
        destinations=destinations,
        travel_mode=body.travel_mode,
    )

    results = []
    for i, entry in enumerate(matrix.results):
        results.append(RouteMatrixItem(
            property_id=ordered_ids[i],
            distance_meters=entry.distance_meters,
            duration_seconds=entry.duration_seconds,
            travel_mode=entry.travel_mode,
        ))

    return RouteMatrixResponse(
        origin_lat=matrix.origin_lat,
        origin_lng=matrix.origin_lng,
        travel_mode=matrix.travel_mode,
        results=results,
        cached_count=matrix.cached_count,
        api_call_made=matrix.api_call_made,
    )
