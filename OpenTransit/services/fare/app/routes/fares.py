"""Fare rule management and calculation routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.calculator import calculate_fare, find_matching_rule
from app.database import get_db
from app.models import FareRule
from app.schemas import FareCalculateRequest, FareCalculateResponse, FareRuleCreate, FareRuleRead

router = APIRouter(prefix="/fares", tags=["fares"])


@router.post("/rules", response_model=FareRuleRead, status_code=status.HTTP_201_CREATED)
async def create_fare_rule(payload: FareRuleCreate, db: AsyncSession = Depends(get_db)) -> FareRule:
    """Create a new fare rule for an agency."""
    rule = FareRule(**payload.model_dump())
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/rules", response_model=list[FareRuleRead])
async def list_fare_rules(agency_id: UUID, db: AsyncSession = Depends(get_db)) -> list[FareRule]:
    """List all fare rules for an agency."""
    result = await db.execute(
        select(FareRule).where(FareRule.agency_id == agency_id).order_by(FareRule.priority.desc())
    )
    return list(result.scalars().all())


@router.get("/rules/{rule_id}", response_model=FareRuleRead)
async def get_fare_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)) -> FareRule:
    """Retrieve a specific fare rule."""
    result = await db.execute(select(FareRule).where(FareRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fare rule not found")
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fare_rule(rule_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    """Deactivate a fare rule."""
    result = await db.execute(select(FareRule).where(FareRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fare rule not found")
    rule.is_active = False
    await db.commit()


@router.post("/calculate", response_model=FareCalculateResponse)
async def calculate(payload: FareCalculateRequest, db: AsyncSession = Depends(get_db)) -> FareCalculateResponse:
    """Calculate the fare for a journey based on agency rules."""
    result = await db.execute(
        select(FareRule).where(
            FareRule.agency_id == payload.agency_id,
            FareRule.is_active.is_(True),
        )
    )
    rules = list(result.scalars().all())

    matched = find_matching_rule(
        rules,
        origin_zone=payload.origin_zone,
        destination_zone=payload.destination_zone,
        passenger_type=payload.passenger_type,
    )
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No matching fare rule found for the given journey parameters",
        )

    amount = calculate_fare(matched, distance_km=payload.distance_km)
    return FareCalculateResponse(
        fare_amount=amount,
        currency=matched.currency,
        rule_id=matched.id,
        rule_name=matched.name,
    )
