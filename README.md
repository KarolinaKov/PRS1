# Debug Backend (Django + DRF)

Backend application for room-based appliance control and payment handling.

The project provides:
- JWT/TOTP-based authorization flow for appliance operations
- Appliance lifecycle endpoints (`start` / `finish`)
- Room balance accounting
- Bank transaction ingestion and room top-ups
- PostgreSQL persistence and optional Docker-based local setup

---

## 1. Tech Stack

- Python 3.13
- Django 5.2
- Django REST Framework
- JWT (`PyJWT`, `djangorestframework_simplejwt`)
- PostgreSQL (`psycopg2-binary`)
- Celery + Redis (configured, not yet used)


Dependencies are listed in `pozadavky.txt`.

---

## 2. Repository Structure

```text
.
├─ api/                    # REST API endpoints and serializers
├─ appliance_module/       # Core domain: rooms, appliances, endpoints, runs, auth services
├─ bank_module/            # Payment models and room top-up logic
├─ debug/                  # Django project config (settings, urls, celery init)
├─ manage.py
└─ pozadavky.txt           # Python dependencies
```

---

## 3. Domain Overview

### 3.1 `appliance_module`

Core models:
- `Room`: room identifier (`key`) + integer balance (stored in cents)
- `Endpoint`: endpoint device metadata and mutable token version
- `Appliance`: appliance catalog with `name` + `price_per_unit`
- `RoomTOTP`: per-room TOTP secret used for authorization verification
- `RunsLog`: appliance run lifecycle (running/finished/aborted), initial/final units/price
- `EndpointApplianceStateRoom`: occupancy state for (`endpoint`, `appliance`) pair

Business services:
- `AuthService`
  - creates short-lived challenge token
  - validates TOTP code and returns access token
  - verifies JWT tokens
- `ApplianceService`
  - `start(...)`: validates state, withdraws balance, opens run log, occupies state
  - `finish(...)`: finalizes run, refunds difference if needed, frees state
- `ApplianceServiceFactory`
  - resolves endpoint/appliance state and builds `ApplianceService`

### 3.2 `bank_module`

Models:
- `ValidPayments`: known room key + amount + transaction id
- `InvalidPayments`: unknown/invalid room or currency transaction records

Service function:
- `update_rooms_from_json(json_str)`
  - parses transaction payload
  - deduplicates transaction IDs against both payment tables
  - applies deposits to matched rooms (atomic transaction)
  - stores valid/invalid payment rows

### 3.3 `api`

Contains DRF APIViews and serializers exposing authentication and appliance operations.

---

## 4. API Endpoints

Base path: `/api/`

### 4.1 `POST /api/auth/challenge/`

Creates a short-lived challenge token for room + endpoint pair.

Request:
```json
{
  "room_num": 12345,
  "endpoint_id": 1
}
```

Response `200`:
```json
{
  "token": "<challenge_jwt>"
}
```

---

### 4.2 `POST /api/auth/verify/`

Verifies challenge token and TOTP code, then returns access token + balance + appliance list.

Request:
```json
{
  "token": "<challenge_jwt>",
  "auth_code": 123456
}
```

Response `200`:
```json
{
  "token": "<access_jwt>",
  "balance": 100000,
  "appliances": [
    {"name": "washer", "value": 25}
  ]
}
```

---

### 4.3 `POST /api/appliance/start/`

Starts appliance run and reserves funds.

Request:
```json
{
  "token": "<access_jwt>",
  "appliance_name": "washer",
  "units": 300,
  "price": 20
}
```

Response `201`:
```json
{
  "newbalance": 98000,
  "token": "<start_jwt>"
}
```

Notes:
- API multiplies `price` by 100 internally.

---

### 4.4 `POST /api/appliance/finish/`

Finalizes a run and applies refund (if final price is lower than reserved price).

Request:
```json
{
  "token": "<start_jwt>",
  "units": 250,
  "price": 15,
  "aborted": false
}
```

Response `200`:
```json
{
  "status": "finished"
}
```

---

## 5. Configuration

Current settings are in `debug/settings.py`.

Important values:
- `ALLOWED_HOSTS = ["localhost", "127.0.0.1"]`
- PostgreSQL database config points to `localhost:5432`
- `SIMPLE_JWT` uses hardcoded signing key and 5-minute access token lifetime
- Celery broker/backend configured as `redis://localhost:6379/0`
- Time zone is `Europe/Prague`

### 5.1 Recommended `.env` (for Docker compose)

Create `.env` in project root:

```env
SECRET_KEY=change-me
DEBUG=True
DJANGO_LOGLEVEL=info
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=debug_db
DATABASE_USERNAME=debug_dbuser
DATABASE_PASSWORD=debug_dbpassword
DATABASE_HOST=db
DATABASE_PORT=5432
```

> Note: `debug/settings.py` currently reads DB values directly from hardcoded settings, not from these environment variables.

---

## 6. Local Development Setup (without Docker)

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r pozadavky.txt
   ```

3. Ensure PostgreSQL is running and database/user exist:
   - DB: `debug_db`
   - User: `debug_dbuser`
   - Password: `debug_dbpassword`

4. Run migrations:

   ```bash
   python manage.py migrate
   ```

5. Start server:

   ```bash
   python manage.py runserver
   ```

6. Open:
   - API root: `http://127.0.0.1:8000/api/`
   - Admin: `http://127.0.0.1:8000/admin/`

---

## 7. Docker Setup

The repository includes:
- `compose.yaml`
- `Dockerfile`

### 7.1 Current caveat

`Dockerfile` installs dependencies from `requirements.txt`, but repository uses `pozadavky.txt`.

To run Docker successfully, do one of the following:
- create a `requirements.txt` copy of `pozadavky.txt`, or
- update `Dockerfile` to use `pozadavky.txt`.

### 7.2 Run with Compose

```bash
docker compose up --build
```

Services:
- `db`: PostgreSQL 17 on port `5432`
- `django-web`: Django app on port `8000`

---

## 8. Typical Runtime Flow

1. Client requests challenge token (`/auth/challenge/`).
2. Client verifies challenge with TOTP (`/auth/verify/`) and receives access token.
3. Client starts appliance (`/appliance/start/`) with reserved units/price.
4. Backend withdraws funds, creates `RunsLog`, and marks endpoint-appliance state occupied.
5. Client finishes appliance (`/appliance/finish/`) with final units/price.
6. Backend finalizes `RunsLog`, refunds price difference (if any), frees state.

---

## 9. Data Notes and Conventions

- Balance and payment amounts are stored as integers in cents.
- Price from API is multiplied by 100 in start/finish handlers.
- `Room.key` acts as room identifier used by API and payment ingestion (`VS` mapping).
- Appliance occupancy is modeled per `(endpoint, appliance)` pair.

---

## 10. Known Issues / Incomplete Parts

1. `AuthService.encode(..., "start", ...)` currently references `units` without defining it in the method scope.
2. `bank_module/data_getter.py` is empty while Celery schedule points to `bank_module.data_getter.fetch_data_from_api`.
3. `debug/celery.py` is empty, but project imports `debug.celery` in `debug/__init__.py`.
4. `Dockerfile` expects `requirements.txt` though dependencies are in `pozadavky.txt`.
5. Secrets/keys are hardcoded in `debug/settings.py` and should be moved to environment variables for production.

---

## 11. Suggested Next Improvements

- Move all secrets and DB settings to environment-based config.
- Complete Celery app initialization and implement scheduled bank fetch task.
- Add automated tests for API auth flow and appliance lifecycle.
- Add DRF schema/OpenAPI generation.
- Harden exception handling with explicit error types and response structure.

---

## 12. Useful Commands

```bash
# Migrations
python manage.py makemigrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Run dev server
python manage.py runserver

# Run tests
python manage.py test
```

---

## 13. License

No license file is present in this repository.
