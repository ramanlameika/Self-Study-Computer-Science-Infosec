"""SQLAlchemy models for the ticketing service."""

import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TicketStatus(str, enum.Enum):
    active = "active"
    used = "used"
    expired = "expired"
    cancelled = "cancelled"
    refunded = "refunded"


class TicketType(str, enum.Enum):
    single = "single"
    multi_trip = "multi_trip"
    daily_pass = "daily_pass"
    monthly_pass = "monthly_pass"


class Ticket(Base):
    """A digital transit ticket."""

    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    agency_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    ticket_type: Mapped[TicketType] = mapped_column(Enum(TicketType), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.active, nullable=False)
    fare_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    # For multi-trip tickets: remaining trips
    trips_remaining: Mapped[int | None] = mapped_column(nullable=True)
    # Cryptographic signature for offline validation
    signature: Mapped[str] = mapped_column(String(512), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    validation_events: Mapped[list["ValidationEvent"]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan"
    )


class ValidationEvent(Base):
    """Audit log entry for every ticket scan."""

    __tablename__ = "validation_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    validator_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    stop_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False)  # "valid" | "invalid" | "expired"
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ticket: Mapped["Ticket"] = relationship(back_populates="validation_events")
