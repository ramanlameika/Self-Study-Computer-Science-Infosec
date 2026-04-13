"""Tests for the agency service."""

import io
import zipfile
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models import Base
from app.gtfs import parse_gtfs_zip

SQLITE_URL = "sqlite+aiosqlite:///./test_agency.db"
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


def make_gtfs_zip() -> bytes:
    """Build a minimal valid GTFS ZIP in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("agency.txt", "agency_id,agency_name,agency_url,agency_timezone\n1,CityBus,https://citybus.example,America/New_York\n")
        zf.writestr("routes.txt", "route_id,agency_id,route_short_name,route_long_name,route_type\nR1,1,42,Downtown Express,3\n")
        zf.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon,zone_id\nS1,Central Station,40.7128,-74.0060,zone-A\nS2,Airport,40.6413,-73.7781,zone-B\n")
    return buf.getvalue()


def test_create_agency():
    resp = client.post("/agencies", json={
        "name": "City Transit Authority",
        "city": "New York",
        "country_code": "US",
        "timezone": "America/New_York",
        "contact_email": "transit@nyc.example.com",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "City Transit Authority"
    assert data["status"] == "pending"


def test_activate_agency():
    create_resp = client.post("/agencies", json={
        "name": "Metro Agency",
        "city": "London",
        "country_code": "GB",
        "timezone": "Europe/London",
        "contact_email": "info@tfl.example.com",
    })
    agency_id = create_resp.json()["id"]
    activate_resp = client.post(f"/agencies/{agency_id}/activate")
    assert activate_resp.status_code == 200
    assert activate_resp.json()["status"] == "active"


def test_list_agencies_only_active():
    # Create one pending (not activated)
    client.post("/agencies", json={
        "name": "Pending Agency",
        "city": "Oslo",
        "country_code": "NO",
        "contact_email": "x@oslo.example.com",
    })
    resp = client.get("/agencies")
    # No active agencies yet, so result should be empty
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_gtfs_import():
    create_resp = client.post("/agencies", json={
        "name": "GTFSTest Agency",
        "city": "Test City",
        "country_code": "US",
        "contact_email": "test@gtfs.example.com",
    })
    agency_id = create_resp.json()["id"]
    gtfs_bytes = make_gtfs_zip()
    import_resp = client.post(
        f"/agencies/{agency_id}/gtfs",
        files={"file": ("gtfs.zip", gtfs_bytes, "application/zip")},
    )
    assert import_resp.status_code == 200
    data = import_resp.json()
    assert data["routes_imported"] == 1
    assert data["stops_imported"] == 2


def test_list_routes_after_import():
    create_resp = client.post("/agencies", json={
        "name": "Route Test",
        "city": "Testville",
        "country_code": "DE",
        "contact_email": "info@de.example.com",
    })
    agency_id = create_resp.json()["id"]
    gtfs_bytes = make_gtfs_zip()
    client.post(f"/agencies/{agency_id}/gtfs", files={"file": ("gtfs.zip", gtfs_bytes, "application/zip")})
    routes_resp = client.get(f"/agencies/{agency_id}/routes")
    assert routes_resp.status_code == 200
    assert len(routes_resp.json()) == 1
    assert routes_resp.json()[0]["gtfs_route_id"] == "R1"


def test_parse_gtfs_zip():
    feed = parse_gtfs_zip(make_gtfs_zip())
    assert len(feed.agencies) == 1
    assert len(feed.routes) == 1
    assert len(feed.stops) == 2
    assert feed.stops[0].stop_name == "Central Station"
    assert feed.stops[0].zone_id == "zone-A"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
