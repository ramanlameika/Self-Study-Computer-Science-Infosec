"""Transit agency CRUD routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import TransitAgency, AgencyStatus
from app.schemas import TransitAgencyCreate, TransitAgencyRead

router = APIRouter(prefix="/agencies", tags=["agencies"])


@router.post("", response_model=TransitAgencyRead, status_code=status.HTTP_201_CREATED)
async def create_agency(payload: TransitAgencyCreate, db: AsyncSession = Depends(get_db)) -> TransitAgency:
    """Register a new transit agency (starts in 'pending' status)."""
    agency = TransitAgency(**payload.model_dump())
    db.add(agency)
    await db.commit()
    await db.refresh(agency)
    return agency


@router.get("", response_model=list[TransitAgencyRead])
async def list_agencies(db: AsyncSession = Depends(get_db)) -> list[TransitAgency]:
    """List all active transit agencies."""
    result = await db.execute(
        select(TransitAgency).where(TransitAgency.status == AgencyStatus.active)
    )
    return list(result.scalars().all())


@router.get("/{agency_id}", response_model=TransitAgencyRead)
async def get_agency(agency_id: UUID, db: AsyncSession = Depends(get_db)) -> TransitAgency:
    """Retrieve a transit agency by ID."""
    result = await db.execute(select(TransitAgency).where(TransitAgency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    return agency


@router.post("/{agency_id}/activate", response_model=TransitAgencyRead)
async def activate_agency(agency_id: UUID, db: AsyncSession = Depends(get_db)) -> TransitAgency:
    """Activate a pending transit agency (admin action)."""
    result = await db.execute(select(TransitAgency).where(TransitAgency.id == agency_id))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agency not found")
    agency.status = AgencyStatus.active
    await db.commit()
    await db.refresh(agency)
    return agency
