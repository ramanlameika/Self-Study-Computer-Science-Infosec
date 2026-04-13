# OpenTransit Architecture

## Overview

OpenTransit is built as a set of independently deployable microservices. Each service owns its own database schema and communicates with others via HTTP REST APIs and asynchronous messages through RabbitMQ.

```
┌──────────────────────────────────────────────────────────────────────┐
│                          Client Layer                                 │
│          Passenger Web App │ Mobile App │ Validator Device SDK        │
└──────────────┬───────────────────┬───────────────────┬───────────────┘
               │                   │                   │
               ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         API Gateway (future)                          │
│            Rate limiting, auth forwarding, routing                    │
└──┬───────────┬───────────┬───────────┬───────────┬───────────────────┘
   │           │           │           │           │
   ▼           ▼           ▼           ▼           ▼
┌──────┐  ┌─────────┐  ┌──────┐  ┌────────┐  ┌─────────┐
│ Auth │  │Ticketing│  │ Fare │  │ Agency │  │ Payment │
│ :8001│  │  :8002  │  │:8003 │  │ :8004  │  │  :8005  │
└──┬───┘  └────┬────┘  └──┬───┘  └───┬────┘  └────┬────┘
   │           │           │           │            │
   └───────────┴───────────┴───────────┴────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
       PostgreSQL         Redis         RabbitMQ
```

## Services

### Auth Service (port 8001)
- Handles user registration, login, JWT issuance and refresh
- Issues both access tokens (short-lived) and refresh tokens (long-lived)
- Provides a `/auth/verify` endpoint for other services to validate tokens
- Refresh token rotation: old token is revoked when refreshed
- Passwords hashed with bcrypt (12 rounds)

### Ticketing Service (port 8002)
- Issues tickets (single, multi-trip, daily pass, monthly pass)
- Generates QR codes with HMAC-SHA256-signed payloads for offline validation
- Validates QR scans from gate/handheld devices
- Maintains an immutable audit log of all validation events

### Fare Service (port 8003)
- Stores fare rules per transit agency
- Rules support zone-based, passenger-type-based, and per-km pricing
- Priority-ordered rule matching — most specific rule wins
- Provides a `/fares/calculate` endpoint for fare queries

### Agency Service (port 8004)
- Manages transit agency onboarding (pending → active lifecycle)
- Parses and stores GTFS feeds (agency, routes, stops)
- Exposes routes and stops for journey planning integrations

### Payment Service (port 8005)
- Records payment transactions linked to tickets
- Sandbox mode for development (always succeeds)
- Pluggable provider interface (Stripe, PayPal, local providers)
- Supports refunds

## Data Flow: Buying a Ticket

```
Passenger           Auth        Fare       Payment    Ticketing
    │                │           │             │           │
    │ POST /auth/login           │             │           │
    │──────────────▶ │           │             │           │
    │ ◀── tokens ─── │           │             │           │
    │                            │             │           │
    │ POST /fares/calculate       │             │           │
    │────────────────────────────▶│            │           │
    │ ◀── fare_amount ────────────│            │           │
    │                                          │           │
    │ POST /payments                           │           │
    │─────────────────────────────────────────▶│          │
    │ ◀── transaction (completed) ─────────────│          │
    │                                                      │
    │ POST /tickets                                        │
    │──────────────────────────────────────────────────────▶
    │ ◀── ticket + QR image ────────────────────────────────
```

## Security

| Concern | Approach |
|---|---|
| Authentication | JWT (HS256), access token 30 min, refresh 30 days |
| Ticket integrity | HMAC-SHA256 signed QR payload, verified offline |
| Password storage | bcrypt, 12 rounds |
| Refresh token revocation | SHA-256 hash stored in DB, revoked on use |
| Rate limiting | Redis-based (Phase 2) |
| GDPR | User deletion cascade, minimal data retention |

## Database

Each service has its own PostgreSQL database:

| Database | Owner service |
|---|---|
| `opentransit_auth` | auth |
| `opentransit_ticketing` | ticketing |
| `opentransit_fare` | fare |
| `opentransit_agency` | agency |
| `opentransit_payment` | payment |

No cross-service foreign keys — services reference each other by UUID only.
