"""Tests for the fare service."""

from decimal import Decimal
from datetime import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base
from app.calculator import calculate_fare, find_matching_rule, is_peak_time

SQLITE_URL = "sqlite+aiosqlite:///./test_fare.db"
engine = create_async_engine(SQLITE_URL)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
def setup_db():
    import asyncio
    asyncio.get_event_loop().run_until_complete(_create_tables())
    yield
    asyncio.get_event_loop().run_until_complete(_drop_tables())


async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

AGENCY_ID = str(uuid4())


def test_create_fare_rule():
    resp = client.post("/fares/rules", json={
        "agency_id": AGENCY_ID,
        "name": "Standard Adult",
        "base_fare": "2.50",
        "currency": "USD",
        "passenger_type": "adult",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Standard Adult"
    assert data["is_active"] is True


def test_list_fare_rules():
    client.post("/fares/rules", json={
        "agency_id": AGENCY_ID,
        "name": "Rule A",
        "base_fare": "1.00",
        "currency": "USD",
    })
    resp = client.get(f"/fares/rules?agency_id={AGENCY_ID}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_calculate_fare():
    client.post("/fares/rules", json={
        "agency_id": AGENCY_ID,
        "name": "Default",
        "base_fare": "3.00",
        "currency": "EUR",
        "priority": 0,
    })
    resp = client.post("/fares/calculate", json={
        "agency_id": AGENCY_ID,
        "passenger_type": "adult",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["fare_amount"]) == Decimal("3.00")
    assert data["currency"] == "EUR"


def test_calculate_fare_no_rule():
    other_agency = str(uuid4())
    resp = client.post("/fares/calculate", json={
        "agency_id": other_agency,
        "passenger_type": "adult",
    })
    assert resp.status_code == 422


def test_calculate_per_km_fare():
    """Fare with per-km rate: base 1.00 + 0.50/km * 10km = 6.00"""
    client.post("/fares/rules", json={
        "agency_id": AGENCY_ID,
        "name": "Per KM",
        "base_fare": "1.00",
        "currency": "USD",
        "per_km_rate": "0.50",
        "priority": 10,
    })
    resp = client.post("/fares/calculate", json={
        "agency_id": AGENCY_ID,
        "passenger_type": "adult",
        "distance_km": 10.0,
    })
    assert resp.status_code == 200
    assert Decimal(resp.json()["fare_amount"]) == Decimal("6.00")


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
