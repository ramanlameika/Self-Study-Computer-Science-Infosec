"""Tests for the ticketing service."""

import json
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base
from app.qr import sign_ticket, verify_signature, generate_qr_data, generate_qr_image_b64
from datetime import datetime, timezone, timedelta

SQLITE_URL = "sqlite+aiosqlite:///./test_ticketing.db"
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

USER_ID = str(uuid4())
AGENCY_ID = str(uuid4())


def test_issue_single_ticket():
    resp = client.post("/tickets", json={
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "ticket_type": "single",
        "fare_amount": "2.50",
        "currency": "USD",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["ticket_type"] == "single"
    assert "qr_image_b64" in data
    assert data["currency"] == "USD"


def test_issue_multi_trip_ticket():
    resp = client.post("/tickets", json={
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "ticket_type": "multi_trip",
        "fare_amount": "20.00",
        "currency": "EUR",
        "trips_total": 10,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["trips_remaining"] == 10


def test_get_ticket():
    issue_resp = client.post("/tickets", json={
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "ticket_type": "single",
        "fare_amount": "3.00",
        "currency": "GBP",
    })
    ticket_id = issue_resp.json()["id"]
    get_resp = client.get(f"/tickets/{ticket_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == ticket_id


def test_validate_valid_ticket():
    issue_resp = client.post("/tickets", json={
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "ticket_type": "single",
        "fare_amount": "2.50",
        "currency": "USD",
    })
    data = issue_resp.json()
    ticket_id = data["id"]
    valid_until = data["valid_until"]

    # Re-create the QR data
    from uuid import UUID
    from datetime import datetime
    sig = sign_ticket(UUID(ticket_id), UUID(USER_ID), UUID(AGENCY_ID), datetime.fromisoformat(valid_until))
    qr_data = generate_qr_data(UUID(ticket_id), UUID(USER_ID), UUID(AGENCY_ID), datetime.fromisoformat(valid_until), sig)

    val_resp = client.post("/tickets/validate", json={"qr_data": qr_data})
    assert val_resp.status_code == 200
    assert val_resp.json()["result"] == "valid"


def test_validate_tampered_qr():
    issue_resp = client.post("/tickets", json={
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "ticket_type": "single",
        "fare_amount": "2.50",
        "currency": "USD",
    })
    data = issue_resp.json()
    ticket_id = data["id"]
    valid_until = data["valid_until"]

    tampered = json.dumps({
        "ticket_id": ticket_id,
        "user_id": USER_ID,
        "agency_id": AGENCY_ID,
        "valid_until": valid_until,
        "sig": "deadbeef",  # wrong signature
    })
    val_resp = client.post("/tickets/validate", json={"qr_data": tampered})
    assert val_resp.status_code == 200
    assert val_resp.json()["result"] == "invalid"


def test_qr_signature_roundtrip():
    ticket_id = uuid4()
    user_id = uuid4()
    agency_id = uuid4()
    valid_until = datetime.now(timezone.utc) + timedelta(hours=2)
    sig = sign_ticket(ticket_id, user_id, agency_id, valid_until)
    assert verify_signature(ticket_id, user_id, agency_id, valid_until, sig)
    assert not verify_signature(ticket_id, user_id, agency_id, valid_until, "badsig")


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
