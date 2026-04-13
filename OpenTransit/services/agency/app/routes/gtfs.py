"""GTFS import routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.gtfs import parse_gtfs_zip
from app.models import Route, Stop, TransitAgency
from app.schemas import GTFSImportResult, RouteRead, StopRead

router = APIRouter(prefix="/agencies", tags=["gtfs"])


@router.post("/{agency_id}/gtfs", response_model=GTFSImportResult)
async def import_gtfs(
    agency_id: UUID,
    file: UploadFile = File(..., description="GTFS ZIP archive"),
    db: AsyncSession = Depends(get_db),
) -> GTFSImportResult:
    """
    Import a GTFS ZIP feed for an agency.

    Replaces all existing routes and stops for the agency.
    """
    result = await db.execute(select(TransitAgency).where(TransitAgency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")

    data = await file.read()
    try:
        feed = parse_gtfs_zip(data)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to parse GTFS feed: {exc}",
        )

    # Replace existing routes and stops
    await db.execute(delete(Route).where(Route.agency_id == agency_id))
    await db.execute(delete(Stop).where(Stop.agency_id == agency_id))

    routes_count = 0
    for r in feed.routes:
        db.add(Route(
            agency_id=agency_id,
            gtfs_route_id=r.route_id,
            short_name=r.route_short_name or None,
            long_name=r.route_long_name,
            route_type=r.route_type,
            color=r.route_color or None,
            text_color=r.route_text_color or None,
        ))
        routes_count += 1

    stops_count = 0
    for s in feed.stops:
        db.add(Stop(
            agency_id=agency_id,
            gtfs_stop_id=s.stop_id,
            name=s.stop_name,
            lat=s.stop_lat,
            lon=s.stop_lon,
            zone_id=s.zone_id or None,
            wheelchair_boarding=s.wheelchair_boarding,
        ))
        stops_count += 1

    await db.commit()
    return GTFSImportResult(agency_id=agency_id, routes_imported=routes_count, stops_imported=stops_count)


@router.get("/{agency_id}/routes", response_model=list[RouteRead])
async def list_routes(agency_id: UUID, db: AsyncSession = Depends(get_db)) -> list[Route]:
    """List all routes imported for an agency."""
    result = await db.execute(select(Route).where(Route.agency_id == agency_id))
    return list(result.scalars().all())


@router.get("/{agency_id}/stops", response_model=list[StopRead])
async def list_stops(agency_id: UUID, db: AsyncSession = Depends(get_db)) -> list[Stop]:
    """List all stops imported for an agency."""
    result = await db.execute(select(Stop).where(Stop.agency_id == agency_id))
    return list(result.scalars().all())
