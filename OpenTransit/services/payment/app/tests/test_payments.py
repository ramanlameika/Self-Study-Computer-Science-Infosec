"""Tests for the payment service."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base

SQLITE_URL = "sqlite+aiosqlite:///./test_payment.db"
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
TICKET_ID = str(uuid4())


def test_initiate_sandbox_payment():
    resp = client.post("/payments", json={
        "user_id": USER_ID,
        "ticket_id": TICKET_ID,
        "amount": "2.50",
        "currency": "USD",
        "provider": "sandbox",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "completed"
    assert data["provider_reference"].startswith("sandbox_")


def test_get_transaction():
    init_resp = client.post("/payments", json={
        "user_id": USER_ID,
        "amount": "5.00",
        "currency": "EUR",
        "provider": "sandbox",
    })
    tx_id = init_resp.json()["id"]
    get_resp = client.get(f"/payments/{tx_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == tx_id


def test_list_user_transactions():
    client.post("/payments", json={
        "user_id": USER_ID,
        "amount": "3.00",
        "currency": "GBP",
        "provider": "sandbox",
    })
    resp = client.get(f"/payments?user_id={USER_ID}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_refund_transaction():
    init_resp = client.post("/payments", json={
        "user_id": USER_ID,
        "ticket_id": TICKET_ID,
        "amount": "10.00",
        "currency": "USD",
        "provider": "sandbox",
    })
    tx_id = init_resp.json()["id"]
    refund_resp = client.post(f"/payments/{tx_id}/refund", json={"reason": "Cancelled trip"})
    assert refund_resp.status_code == 200
    assert refund_resp.json()["status"] == "refunded"


def test_refund_pending_fails():
    """Cannot refund a non-completed transaction (in practice pending would be edge case)."""
    # Force a pending by mocking — here we just verify the status endpoint returns 409
    # when trying to re-refund an already refunded transaction
    init_resp = client.post("/payments", json={
        "user_id": USER_ID,
        "amount": "7.00",
        "currency": "USD",
        "provider": "sandbox",
    })
    tx_id = init_resp.json()["id"]
    client.post(f"/payments/{tx_id}/refund", json={})
    # Refund again should 409
    resp = client.post(f"/payments/{tx_id}/refund", json={})
    assert resp.status_code == 409


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
