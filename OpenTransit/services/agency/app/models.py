"""SQLAlchemy models for the agency service."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AgencyStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"


class TransitAgency(Base):
    """An onboarded city transit agency."""

    __tablename__ = "transit_agencies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgencyStatus] = mapped_column(Enum(AgencyStatus), default=AgencyStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    routes: Mapped[list["Route"]] = relationship(back_populates="agency", cascade="all, delete-orphan")
    stops: Mapped[list["Stop"]] = relationship(back_populates="agency", cascade="all, delete-orphan")


class Route(Base):
    """A transit route (from GTFS routes.txt)."""

    __tablename__ = "routes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agency_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("transit_agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    gtfs_route_id: Mapped[str] = mapped_column(String(64), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    long_name: Mapped[str] = mapped_column(String(512), nullable=False)
    route_type: Mapped[int] = mapped_column(nullable=False)  # GTFS route_type codes
    color: Mapped[str | None] = mapped_column(String(6), nullable=True)  # hex without '#'
    text_color: Mapped[str | None] = mapped_column(String(6), nullable=True)

    agency: Mapped["TransitAgency"] = relationship(back_populates="routes")


class Stop(Base):
    """A transit stop (from GTFS stops.txt)."""

    __tablename__ = "stops"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agency_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("transit_agencies.id", ondelete="CASCADE"), nullable=False, index=True)
    gtfs_stop_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)
    zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wheelchair_boarding: Mapped[int] = mapped_column(default=0, nullable=False)  # 0=unknown, 1=yes, 2=no

    agency: Mapped["TransitAgency"] = relationship(back_populates="stops")
