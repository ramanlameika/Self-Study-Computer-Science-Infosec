"""SQLAlchemy models for the fare service."""

import enum
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PassengerType(str, enum.Enum):
    adult = "adult"
    child = "child"
    senior = "senior"
    student = "student"
    disabled = "disabled"


class FareRule(Base):
    """
    A fare rule defined by a transit agency.

    Rules are evaluated in priority order. The first matching rule wins.
    """

    __tablename__ = "fare_rules"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agency_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Filters (all are optional; a rule matches when all specified filters match)
    origin_zone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    destination_zone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    passenger_type: Mapped[PassengerType | None] = mapped_column(Enum(PassengerType), nullable=True)
    # Peak / off-peak time window (UTC)
    peak_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    peak_end: Mapped[time | None] = mapped_column(Time, nullable=True)

    # Pricing
    base_fare: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)  # ISO 4217
    # Optional: per-km rate added on top of base fare
    per_km_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
