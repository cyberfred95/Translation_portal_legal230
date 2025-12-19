# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This system consists of three interconnected components:

1. **Lexa** (this repository) - Main translation portal built with Django. Provides web UI and REST API for translation services, user management, subscriptions, and glossary management.

2. **Lara Bridge** (external, `laradjango` container on port 8001) - Django backend that receives translation requests from Lexa. Determines optimal translation memory (MT) and glossary (GL) parameters. Admin interface for configuration.

3. **Lara Server** (external) - The actual translation engine. Receives translation requests via the "lara translation" SDK. Stores translation memories and glossaries.

## Common Commands

### Docker Operations (Production)
```bash
# Start all services
docker-compose -f docker-compose.prod.yaml up

# Start specific service
docker-compose -f docker-compose.prod.yaml up runserver

# Stop services
docker-compose -f docker-compose.prod.yaml stop

# Enter container shell
docker exec -it <container_id> bash

# View logs
docker-compose -f docker-compose.prod.yaml logs -f runserver
```

### Django Management (inside container)
```bash
python manage.py migrate                    # Run migrations
python manage.py makemigrations             # Create migrations
python manage.py collectstatic --no-input   # Collect static files
python manage.py createsuperuser            # Create admin user
python manage.py shell                      # Django shell
```

### Running Tests
```bash
# Run all API tests
python manage.py test api.tests

# Run specific test file
python manage.py test api.tests.test_domain
python manage.py test api.tests.test_glossary
python manage.py test api.tests.test_translate
python manage.py test api.tests.test_integration

# Run single test class
python manage.py test api.tests.test_domain.DomainAPITest

# Tests use SQLite in-memory database (configured in settings.py)
```

### Celery (background tasks)
```bash
# Worker
celery -A legal worker -l info

# Beat scheduler (for periodic tasks like subscription renewals)
celery -A legal beat -l info
```

## Architecture

### Docker Services (docker-compose.prod.yaml)
- **runserver**: Gunicorn on port 8099 (via `docker/django/start-dev.sh`)
- **postgres**: PostgreSQL 16.1 (database: `legal`, user: `legal`)
- **redis**: Redis 6 (Celery broker)
- **celery**: Task worker
- **celery_beat**: Scheduled task runner
- Network: `lexamt-network` (external)

### Django Apps
| App | Purpose |
|-----|---------|
| `legal/` | Core application, main views (translate, dashboard, profile) |
| `api/` | REST API endpoints (versioned at `/api/v1/`) |
| `glossaries/` | Glossary management with LARA backend sync |
| `users/` | User authentication, groups, roles |
| `domains/` | Translation domains/subject areas |
| `languages/` | Language definitions |
| `subscriptions/` | Billing and subscription management |
| `quoting/` | Quote generation |
| `stripe_webhooks/` | Stripe payment integration |
| `emails/` | Email notifications (ActiveTrail) |
| `writing/` | Writing/composition tools (currently disabled) |

### Key URL Routes
- `/` → Dashboard (login required)
- `/translate/` → Main translation interface
- `/admin/` → Django admin
- `/api/v1/` → REST API (domains, glossaries, languages, translate)
- `/api/internal/` → Service-to-service API (Docker network only)
- `/glossaries/` → Glossary management UI
- `/rosetta/` → Translation management UI

### Lexa ↔ Lara Bridge Integration

Glossary operations are synced to LARA backend via Django signals:

```
Glossary saved → post_save signal → LaraGlossaryService → LaraClient → LARA API
Glossary deleted → pre_delete signal → LaraClient.delete_glossary()
```

Key files:
- [glossaries/signals.py](glossaries/signals.py) - Signal handlers for sync
- [glossaries/services/lara_client.py](glossaries/services/lara_client.py) - HTTP client
- [glossaries/services/glossary_service.py](glossaries/services/glossary_service.py) - Service layer

LARA API endpoints (via `LARA_API_URL`):
- `POST /api/lara/glossaries-list/create/`
- `POST /api/lara/glossaries-list/<id>/update/`
- `POST /api/lara/glossaries-list/<id>/delete/`

### Settings Configuration

Two settings files:
- `legal/settings.py` - Base settings (used for tests with SQLite)
- `legal/settings_dev.py` - Development/production (PostgreSQL)

The container uses `DJANGO_SETTINGS_MODULE=legal.settings_dev`.

## Environment Variables

Critical variables (see `.env.example`):
```bash
# LARA Integration (required for glossary sync)
LARA_API_URL="http://laradjango:8001/lara-django"
LARA_ACCESS_KEY_ID="..."
LARA_ACCESS_KEY_SECRET="..."

# Stripe (payments)
STRIPE_API_KEY="..."
STRIPE_WEBHOOK_SECRET="..."

# Adobe PDF Services (if CONVERSION_METHOD=adobe)
ADOBE_CLIENT_ID="..."
ADOBE_CLIENT_SECRET="..."
ADOBE_ORGANIZATION_ID="..."

# Email (ActiveTrail)
ACTIVE_TRAIL_API_KEY="..."
SENDER_EMAIL="..."
```

## Code Conventions

- Django 3.1 with Python 3.10
- REST API uses Django REST Framework
- i18n: English (`en`) and French (`fr`) languages
- Auth: Custom user model at `users.User`
- File uploads: Glossaries accept CSV/XLSX, converted to CSV for LARA
- Time zone: `Etc/GMT-3`
