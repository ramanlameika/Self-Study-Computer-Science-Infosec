# OpenTransit API Reference

All services expose interactive Swagger documentation at `/docs` when running.

## Auth Service — `http://localhost:8001`

| Method | Path | Description |
|---|---|---|
| POST | `/users` | Register a new user |
| GET | `/users/{user_id}` | Get user profile |
| PATCH | `/users/{user_id}` | Update user profile |
| POST | `/auth/login` | Login and receive tokens |
| POST | `/auth/refresh` | Refresh an access token |
| POST | `/auth/logout` | Revoke a refresh token |
| POST | `/auth/verify` | Verify an access token (service-to-service) |
| GET | `/health` | Health check |

## Ticketing Service — `http://localhost:8002`

| Method | Path | Description |
|---|---|---|
| POST | `/tickets` | Issue a new ticket |
| GET | `/tickets/{ticket_id}` | Get ticket details |
| POST | `/tickets/validate` | Validate a QR code scan |
| GET | `/tickets/{ticket_id}/validations` | Get validation history |
| GET | `/health` | Health check |

## Fare Service — `http://localhost:8003`

| Method | Path | Description |
|---|---|---|
| POST | `/fares/rules` | Create a fare rule |
| GET | `/fares/rules?agency_id=` | List fare rules for agency |
| GET | `/fares/rules/{rule_id}` | Get a fare rule |
| DELETE | `/fares/rules/{rule_id}` | Deactivate a fare rule |
| POST | `/fares/calculate` | Calculate fare for journey |
| GET | `/health` | Health check |

## Agency Service — `http://localhost:8004`

| Method | Path | Description |
|---|---|---|
| POST | `/agencies` | Register a transit agency |
| GET | `/agencies` | List active agencies |
| GET | `/agencies/{agency_id}` | Get agency details |
| POST | `/agencies/{agency_id}/activate` | Activate an agency |
| POST | `/agencies/{agency_id}/gtfs` | Upload GTFS ZIP feed |
| GET | `/agencies/{agency_id}/routes` | List routes |
| GET | `/agencies/{agency_id}/stops` | List stops |
| GET | `/health` | Health check |

## Payment Service — `http://localhost:8005`

| Method | Path | Description |
|---|---|---|
| POST | `/payments` | Initiate a payment |
| GET | `/payments/{transaction_id}` | Get transaction |
| GET | `/payments?user_id=` | List user transactions |
| POST | `/payments/{transaction_id}/refund` | Refund a transaction |
| GET | `/health` | Health check |

---

## Authentication

All endpoints (except registration, login, and health) require a valid JWT in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /auth/login`.

## Error Responses

All services return standard HTTP status codes:

| Status | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 204 | No content |
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict |
| 422 | Validation error |
| 500 | Internal server error |

Error bodies always have the form:
```json
{ "detail": "Human-readable error message" }
```
