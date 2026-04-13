"""
GTFS (General Transit Feed Specification) import utilities.

Supports parsing the core GTFS CSV files:
  - agency.txt
  - routes.txt
  - stops.txt

The parser reads from a ZIP archive or directory of CSV files.
"""

import csv
import io
import zipfile
from dataclasses import dataclass, field
from typing import IO


@dataclass
class GTFSAgency:
    agency_id: str
    agency_name: str
    agency_url: str
    agency_timezone: str
    agency_email: str = ""


@dataclass
class GTFSRoute:
    route_id: str
    agency_id: str
    route_short_name: str
    route_long_name: str
    route_type: int
    route_color: str = ""
    route_text_color: str = ""


@dataclass
class GTFSStop:
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    zone_id: str = ""
    wheelchair_boarding: int = 0


@dataclass
class GTFSFeed:
    agencies: list[GTFSAgency] = field(default_factory=list)
    routes: list[GTFSRoute] = field(default_factory=list)
    stops: list[GTFSStop] = field(default_factory=list)


def _read_csv(fileobj: IO[bytes]) -> list[dict]:
    """Read a CSV file-like object and return a list of row dicts."""
    content = fileobj.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    return [row for row in reader]


def parse_gtfs_zip(data: bytes) -> GTFSFeed:
    """
    Parse a GTFS ZIP archive.

    Args:
        data: Raw bytes of the GTFS ZIP file.

    Returns:
        A GTFSFeed with parsed agencies, routes, and stops.
    """
    feed = GTFSFeed()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = zf.namelist()

        if "agency.txt" in names:
            with zf.open("agency.txt") as f:
                for row in _read_csv(f):
                    feed.agencies.append(GTFSAgency(
                        agency_id=row.get("agency_id", ""),
                        agency_name=row.get("agency_name", ""),
                        agency_url=row.get("agency_url", ""),
                        agency_timezone=row.get("agency_timezone", "UTC"),
                        agency_email=row.get("agency_email", ""),
                    ))

        if "routes.txt" in names:
            with zf.open("routes.txt") as f:
                for row in _read_csv(f):
                    feed.routes.append(GTFSRoute(
                        route_id=row.get("route_id", ""),
                        agency_id=row.get("agency_id", ""),
                        route_short_name=row.get("route_short_name", ""),
                        route_long_name=row.get("route_long_name", ""),
                        route_type=int(row.get("route_type", 3)),
                        route_color=row.get("route_color", ""),
                        route_text_color=row.get("route_text_color", ""),
                    ))

        if "stops.txt" in names:
            with zf.open("stops.txt") as f:
                for row in _read_csv(f):
                    try:
                        lat = float(row.get("stop_lat", 0))
                        lon = float(row.get("stop_lon", 0))
                    except ValueError:
                        lat, lon = 0.0, 0.0
                    feed.stops.append(GTFSStop(
                        stop_id=row.get("stop_id", ""),
                        stop_name=row.get("stop_name", ""),
                        stop_lat=lat,
                        stop_lon=lon,
                        zone_id=row.get("zone_id", ""),
                        wheelchair_boarding=int(row.get("wheelchair_boarding", 0) or 0),
                    ))

    return feed
