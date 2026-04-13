"""Pydantic schemas for the fare service."""

from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import PassengerType


class FareRuleCreate(BaseModel):
    agency_id: UUID
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=512)
    origin_zone: str | None = Field(default=None, max_length=64)
    destination_zone: str | None = Field(default=None, max_length=64)
    passenger_type: PassengerType | None = None
    peak_start: time | None = None
    peak_end: time | None = None
    base_fare: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)
    per_km_rate: Decimal | None = Field(default=None, gt=0)
    priority: int = Field(default=0, ge=0)


class FareRuleRead(FareRuleCreate):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FareCalculateRequest(BaseModel):
    agency_id: UUID
    origin_zone: str | None = None
    destination_zone: str | None = None
    passenger_type: PassengerType = PassengerType.adult
    distance_km: float = Field(default=0.0, ge=0)


class FareCalculateResponse(BaseModel):
    fare_amount: Decimal
    currency: str
    rule_id: UUID
    rule_name: str
