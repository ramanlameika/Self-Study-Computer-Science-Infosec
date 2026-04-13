# Agency Onboarding Guide

This guide walks a transit agency through the process of joining the OpenTransit platform.

## Step 1: Register Your Agency

Submit a registration request via the Agency Service API:

```http
POST /agencies
Content-Type: application/json

{
  "name": "CityBus Authority",
  "city": "Amsterdam",
  "country_code": "NL",
  "timezone": "Europe/Amsterdam",
  "website": "https://citybus.example.nl",
  "contact_email": "ops@citybus.example.nl"
}
```

Your agency starts in **pending** status. An OpenTransit admin will review and activate your account.

## Step 2: Receive Activation

Once an admin activates your agency:

```http
POST /agencies/{agency_id}/activate
```

Your agency status changes to **active** and you can start importing data.

## Step 3: Prepare Your GTFS Feed

OpenTransit accepts standard [GTFS](https://gtfs.org/) ZIP archives.

Your ZIP must contain at minimum:
- `agency.txt`
- `routes.txt`
- `stops.txt`

Optional (for future phases):
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `fare_attributes.txt`
- `fare_rules.txt`

## Step 4: Upload Your GTFS Feed

```http
POST /agencies/{agency_id}/gtfs
Content-Type: multipart/form-data

file=<your-gtfs.zip>
```

Response:
```json
{
  "agency_id": "...",
  "routes_imported": 42,
  "stops_imported": 312
}
```

Re-uploading replaces all existing routes and stops.

## Step 5: Configure Fare Rules

Define fare rules for your city via the Fare Service:

```http
POST /fares/rules
Content-Type: application/json

{
  "agency_id": "your-agency-uuid",
  "name": "Standard Adult",
  "base_fare": "2.50",
  "currency": "EUR",
  "passenger_type": "adult",
  "priority": 0
}
```

**Zone-based example:**
```json
{
  "agency_id": "your-agency-uuid",
  "name": "Zone A to B",
  "origin_zone": "zone-A",
  "destination_zone": "zone-B",
  "base_fare": "3.50",
  "currency": "EUR",
  "priority": 10
}
```

Rules are evaluated in descending priority order. The first matching rule wins.

## Step 6: Deploy a Validator

The validator device SDK (Android / Raspberry Pi) connects to the Ticketing Service to validate QR codes.

```
POST /tickets/validate
{
  "qr_data": "<scanned QR string>",
  "validator_id": "<your-device-uuid>",
  "stop_id": "S42"
}
```

Offline validation: the device can verify the HMAC-SHA256 signature locally without a network connection.

## Step 7: Monitor Revenue

Use the Payment Service to query transactions:

```http
GET /payments?user_id={user_id}
```

Revenue reporting dashboard (Phase 2) will aggregate this data by agency.

---

For questions, open a [GitHub Discussion](../../discussions) or email support@opentransit.example.
