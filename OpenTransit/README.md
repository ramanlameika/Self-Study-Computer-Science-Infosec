# OpenTransit 🚌🚆🚢

**International Open Source Public Transit Ticketing Platform**

OpenTransit is a vendor-neutral, city-agnostic open source ticketing system designed to enable seamless collaboration between transit agencies worldwide. Any city can onboard, define their routes and fare rules, and start issuing digital tickets to passengers — all using open standards.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![CI](https://github.com/your-org/opentransit/actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
[![OpenAPI](https://img.shields.io/badge/API-OpenAPI%203.0-green)](docs/api.md)

---

## ✨ Features

### For Passengers
- Universal transit wallet — one account, every city
- Purchase single-trip, multi-trip, and monthly passes
- QR code tickets on mobile or printable
- Journey history and receipts
- Offline ticket validation support

### For Transit Agencies
- Self-service onboarding portal
- Upload GTFS feeds to define routes, stops, and fares
- Validator device SDK (Android / Raspberry Pi compatible)
- Revenue reporting and analytics dashboard
- Customizable fare rules (zone, time-of-day, passenger type)

### For Developers
- RESTful API with OpenAPI 3.0 documentation
- API key management and sandbox environment
- Webhook support for real-time events
- Python, JavaScript, and Java SDKs (planned)

---

## 🏗 Architecture

OpenTransit is built as a set of loosely-coupled microservices:

| Service | Description | Port |
|---|---|---|
| `auth` | User registration, login, JWT / OAuth2 | 8001 |
| `ticketing` | Ticket issuance, QR generation, validation | 8002 |
| `fare` | Fare calculation per zone / route rules | 8003 |
| `agency` | Transit agency management, GTFS import | 8004 |
| `payment` | Multi-currency payment processing | 8005 |

Supporting infrastructure:

| Component | Purpose |
|---|---|
| PostgreSQL | Primary relational datastore |
| Redis | Sessions, caching, rate-limiting |
| RabbitMQ | Async messaging between services |

See [docs/architecture.md](docs/architecture.md) for the full architecture diagram.

---

## 🚀 Quick Start (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/your-org/opentransit.git
cd opentransit

# Copy environment file
cp .env.example .env

# Start all services
docker compose up --build

# Run database migrations (first time)
docker compose exec auth alembic upgrade head
docker compose exec ticketing alembic upgrade head
docker compose exec fare alembic upgrade head
docker compose exec agency alembic upgrade head
docker compose exec payment alembic upgrade head
```

API documentation is available at:
- Auth: http://localhost:8001/docs
- Ticketing: http://localhost:8002/docs
- Fare: http://localhost:8003/docs
- Agency: http://localhost:8004/docs
- Payment: http://localhost:8005/docs

---

## 🌍 Open Standards

| Standard | Usage |
|---|---|
| [GTFS](https://gtfs.org/) | Route, stop, and schedule data |
| [NeTEx](https://netex-cen.eu/) | Ticketing data interchange (Phase 3) |
| [OAuth2 / OIDC](https://openid.net/connect/) | Authentication and authorization |
| [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html) | Multi-currency support |
| [OpenAPI 3.0](https://swagger.io/specification/) | API documentation |

---

## 📁 Project Structure

```
OpenTransit/
├── services/
│   ├── auth/          # Authentication & user management
│   ├── ticketing/     # Ticket issuance & validation
│   ├── fare/          # Fare calculation engine
│   ├── agency/        # Transit agency & GTFS management
│   └── payment/       # Payment processing
├── shared/            # Shared utilities & base models
├── docs/              # Architecture and API documentation
├── docker-compose.yml
└── .github/           # CI/CD, issue templates
```

---

## 🗺 Roadmap

- **Phase 1 — Foundation** ✅
  - Core auth, ticketing, fare, agency, payment services
  - GTFS import for pilot city
  - QR code ticket generation
- **Phase 2 — Multi-City** 🔄
  - Transit agency onboarding portal
  - Inter-city ticket transfers
  - Analytics dashboard
- **Phase 3 — International Scale** 📅
  - NeTEx support for European integration
  - Federated identity
  - Multi-language support (i18n)
- **Phase 4 — Ecosystem** 📅
  - SDKs for Python, JavaScript, Java
  - Journey planner integration (OpenTripPlanner, Google Maps)
  - Plugin marketplace

---

## 🤝 Contributing

We welcome contributions from developers, transit agencies, and open source enthusiasts worldwide! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

---

## 🛡 Security

OpenTransit takes security seriously. If you discover a vulnerability, please report it privately. See [SECURITY.md](SECURITY.md) for details.

---

## 📄 License

Copyright 2026 OpenTransit Contributors

Licensed under the [Apache License, Version 2.0](LICENSE).
