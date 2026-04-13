"""Tests for the auth service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base

SQLITE_URL = "sqlite+aiosqlite:///./test_auth.db"
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


def test_register_user():
    response = client.post("/users", json={
        "email": "alice@example.com",
        "password": "Secret123",
        "full_name": "Alice Smith",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["role"] == "passenger"
    assert "hashed_password" not in data


def test_register_duplicate_email():
    client.post("/users", json={
        "email": "bob@example.com",
        "password": "Secret123",
        "full_name": "Bob Jones",
    })
    response = client.post("/users", json={
        "email": "bob@example.com",
        "password": "Secret123",
        "full_name": "Bob Jones",
    })
    assert response.status_code == 409


def test_login_success():
    client.post("/users", json={
        "email": "carol@example.com",
        "password": "Secret123",
        "full_name": "Carol White",
    })
    response = client.post("/auth/login", json={
        "email": "carol@example.com",
        "password": "Secret123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    client.post("/users", json={
        "email": "dave@example.com",
        "password": "Secret123",
        "full_name": "Dave Green",
    })
    response = client.post("/auth/login", json={
        "email": "dave@example.com",
        "password": "wrong",
    })
    assert response.status_code == 401


def test_token_verify():
    client.post("/users", json={
        "email": "eve@example.com",
        "password": "Secret123",
        "full_name": "Eve Black",
    })
    login_resp = client.post("/auth/login", json={
        "email": "eve@example.com",
        "password": "Secret123",
    })
    token = login_resp.json()["access_token"]
    verify_resp = client.post("/auth/verify", headers={"Authorization": f"Bearer {token}"})
    assert verify_resp.status_code == 200
    assert verify_resp.json()["valid"] is True


def test_password_too_short():
    response = client.post("/users", json={
        "email": "frank@example.com",
        "password": "abc",
        "full_name": "Frank",
    })
    assert response.status_code == 422


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
