# Contributing to OpenTransit

Thank you for your interest in contributing to OpenTransit! This document explains how to get involved.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to Contribute

- **Report bugs** — open a GitHub issue using the bug report template
- **Suggest features** — open an issue using the feature request template
- **Submit code** — fork the repo, create a branch, and open a pull request
- **Improve documentation** — fix typos, add examples, translate content
- **Onboard your transit agency** — follow the [Agency Onboarding Guide](docs/agency-onboarding.md)
- **Translate the platform** — add or improve locale files under `shared/locales/`

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ (for frontend work)
- Git

### Local Setup

```bash
git clone https://github.com/your-org/opentransit.git
cd opentransit
cp .env.example .env
docker compose up --build
```

Run tests for a specific service:

```bash
cd services/auth
pip install -r requirements.txt
pytest app/tests/ -v
```

Run all tests:

```bash
docker compose run --rm auth pytest app/tests/ -v
docker compose run --rm ticketing pytest app/tests/ -v
docker compose run --rm fare pytest app/tests/ -v
docker compose run --rm agency pytest app/tests/ -v
docker compose run --rm payment pytest app/tests/ -v
```

## Branch Naming Convention

| Type | Pattern | Example |
|---|---|---|
| Feature | `feature/<short-description>` | `feature/gtfs-import` |
| Bug fix | `fix/<short-description>` | `fix/qr-expiry` |
| Documentation | `docs/<short-description>` | `docs/agency-guide` |
| Chore | `chore/<short-description>` | `chore/update-deps` |

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(ticketing): add QR code expiry validation
fix(auth): prevent duplicate user registration
docs(agency): update GTFS import guide
chore(deps): update fastapi to 0.111.0
```

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. Write tests for any new functionality
3. Ensure all tests pass: `pytest app/tests/ -v`
4. Ensure your code is formatted: `black app/ && isort app/`
5. Update documentation if needed
6. Open a pull request using the PR template
7. Await code review from a maintainer

## Coding Standards

- Python: [PEP 8](https://peps.python.org/pep-0008/), formatted with `black` and `isort`
- Type hints required on all function signatures
- Docstrings required on all public functions and classes
- Tests required for all new features and bug fixes
- No secrets in source code — use environment variables

## Adding a New Transit Agency

See the [Agency Onboarding Guide](docs/agency-onboarding.md) for step-by-step instructions on integrating a new city's transit system.

## RFC Process

Major architectural changes require an RFC (Request for Comments):

1. Create a new file in `docs/rfcs/` with a descriptive name
2. Fill in the RFC template
3. Open a pull request to start the discussion
4. After community consensus, the RFC is either accepted or rejected

## Questions?

Open a [GitHub Discussion](../../discussions) or reach out on our community forum.
