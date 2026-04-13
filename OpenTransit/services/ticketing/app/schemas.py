"""Pydantic schemas for the ticketing service."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import TicketStatus, TicketType


class TicketIssueRequest(BaseModel):
    user_id: UUID
    agency_id: UUID
    ticket_type: TicketType
    fare_amount: Decimal = Field(gt=0, decimal_places=2)
    currency: str = Field(min_length=3, max_length=3)  # ISO 4217
    trips_total: int | None = Field(default=None, ge=1)  # for multi-trip


class TicketRead(BaseModel):
    id: UUID
    user_id: UUID
    agency_id: UUID
    ticket_type: TicketType
    status: TicketStatus
    fare_amount: Decimal
    currency: str
    trips_remaining: int | None
    valid_from: datetime
    valid_until: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketWithQR(TicketRead):
    """TicketRead plus the base64-encoded QR code PNG."""
    qr_image_b64: str


class ValidationRequest(BaseModel):
    qr_data: str
    validator_id: UUID | None = None
    stop_id: str | None = None


class ValidationResult(BaseModel):
    result: str       # "valid" | "invalid" | "expired"
    ticket_id: UUID | None = None
    detail: str


class ValidationEventRead(BaseModel):
    id: UUID
    ticket_id: UUID
    validator_id: UUID | None
    stop_id: str | None
    result: str
    scanned_at: datetime

    model_config = {"from_attributes": True}
