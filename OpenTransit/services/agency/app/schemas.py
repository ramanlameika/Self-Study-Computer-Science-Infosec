"""Pydantic schemas for the agency service."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models import AgencyStatus


class TransitAgencyCreate(BaseModel):
    name: str = Field(max_length=255)
    city: str = Field(max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    timezone: str = Field(max_length=64, default="UTC")
    website: str | None = Field(default=None, max_length=512)
    contact_email: EmailStr


class TransitAgencyRead(TransitAgencyCreate):
    id: UUID
    status: AgencyStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class RouteRead(BaseModel):
    id: UUID
    agency_id: UUID
    gtfs_route_id: str
    short_name: str | None
    long_name: str
    route_type: int
    color: str | None
    text_color: str | None

    model_config = {"from_attributes": True}


class StopRead(BaseModel):
    id: UUID
    agency_id: UUID
    gtfs_stop_id: str
    name: str
    lat: float
    lon: float
    zone_id: str | None
    wheelchair_boarding: int

    model_config = {"from_attributes": True}


class GTFSImportResult(BaseModel):
    agency_id: UUID
    routes_imported: int
    stops_imported: int
