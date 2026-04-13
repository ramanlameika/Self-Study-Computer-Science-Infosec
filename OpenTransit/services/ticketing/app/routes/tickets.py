"""Ticket issuance and validation routes."""

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import Ticket, TicketStatus, TicketType, ValidationEvent
from app.qr import generate_qr_data, generate_qr_image_b64, sign_ticket, verify_signature
from app.schemas import (
    TicketIssueRequest,
    TicketRead,
    TicketWithQR,
    ValidationRequest,
    ValidationResult,
    ValidationEventRead,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _ticket_validity_window(ticket_type: TicketType) -> timedelta:
    match ticket_type:
        case TicketType.single:
            return timedelta(minutes=settings.single_ticket_validity_minutes)
        case TicketType.multi_trip:
            return timedelta(days=365)
        case TicketType.daily_pass:
            return timedelta(days=1)
        case TicketType.monthly_pass:
            return timedelta(days=30)
        case _:
            return timedelta(hours=2)


@router.post("", response_model=TicketWithQR, status_code=status.HTTP_201_CREATED)
async def issue_ticket(payload: TicketIssueRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Issue a new ticket and return it with a QR code."""
    from uuid import uuid4
    now = datetime.now(timezone.utc)
    valid_until = now + _ticket_validity_window(payload.ticket_type)

    # Generate the ticket ID upfront so the signature binds to it
    ticket_id = uuid4()
    sig = sign_ticket(ticket_id, payload.user_id, payload.agency_id, valid_until)

    ticket = Ticket(
        id=ticket_id,
        user_id=payload.user_id,
        agency_id=payload.agency_id,
        ticket_type=payload.ticket_type,
        fare_amount=payload.fare_amount,
        currency=payload.currency,
        trips_remaining=payload.trips_total,
        signature=sig,
        valid_from=now,
        valid_until=valid_until,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)

    qr_data = generate_qr_data(ticket.id, ticket.user_id, ticket.agency_id, ticket.valid_until, sig)
    qr_b64 = generate_qr_image_b64(qr_data)

    return {**TicketRead.model_validate(ticket).model_dump(), "qr_image_b64": qr_b64}


@router.get("/{ticket_id}", response_model=TicketRead)
async def get_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db)) -> Ticket:
    """Retrieve ticket details."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.post("/validate", response_model=ValidationResult)
async def validate_ticket(payload: ValidationRequest, db: AsyncSession = Depends(get_db)) -> ValidationResult:
    """
    Validate a QR code scan.

    Called by validator devices (gates, handheld scanners).
    """
    try:
        qr_payload = json.loads(payload.qr_data)
        ticket_id = UUID(qr_payload["ticket_id"])
        user_id = UUID(qr_payload["user_id"])
        agency_id = UUID(qr_payload["agency_id"])
        valid_until = datetime.fromisoformat(qr_payload["valid_until"])
        sig = qr_payload["sig"]
    except (KeyError, ValueError):
        return ValidationResult(result="invalid", detail="Malformed QR data")

    if not verify_signature(ticket_id, user_id, agency_id, valid_until, sig):
        return ValidationResult(result="invalid", ticket_id=ticket_id, detail="Invalid signature")

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        return ValidationResult(result="invalid", ticket_id=ticket_id, detail="Ticket not found")

    now = datetime.now(timezone.utc)

    # Normalise ticket.valid_until to be timezone-aware (SQLite may store naive datetimes)
    valid_until_aware = (
        ticket.valid_until.replace(tzinfo=timezone.utc)
        if ticket.valid_until.tzinfo is None
        else ticket.valid_until
    )

    if ticket.status == TicketStatus.cancelled or ticket.status == TicketStatus.refunded:
        scan_result = "invalid"
        detail = f"Ticket is {ticket.status.value}"
    elif valid_until_aware < now:
        ticket.status = TicketStatus.expired
        scan_result = "expired"
        detail = "Ticket has expired"
    elif ticket.status == TicketStatus.used and ticket.ticket_type == TicketType.single:
        scan_result = "invalid"
        detail = "Single-use ticket already used"
    else:
        scan_result = "valid"
        detail = "Ticket accepted"
        if ticket.ticket_type == TicketType.single:
            ticket.status = TicketStatus.used
        elif ticket.ticket_type == TicketType.multi_trip and ticket.trips_remaining is not None:
            ticket.trips_remaining -= 1
            if ticket.trips_remaining <= 0:
                ticket.status = TicketStatus.used

    event = ValidationEvent(
        ticket_id=ticket.id,
        validator_id=payload.validator_id,
        stop_id=payload.stop_id,
        result=scan_result,
    )
    db.add(event)
    await db.commit()

    return ValidationResult(result=scan_result, ticket_id=ticket_id, detail=detail)


@router.get("/{ticket_id}/validations", response_model=list[ValidationEventRead])
async def list_validations(ticket_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ValidationEvent]:
    """Return the validation history for a ticket."""
    result = await db.execute(select(ValidationEvent).where(ValidationEvent.ticket_id == ticket_id))
    return list(result.scalars().all())
