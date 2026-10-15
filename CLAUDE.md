# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**factApp** is a FastAPI application that provides OTP-based phone authentication with JWT tokens. The system manages user registration/login via SMS-sent one-time passwords, issues short-lived access tokens and long-lived refresh tokens, and supports token rotation for security.

## Development Commands

### Local Development (without Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server with hot reload (requires PostgreSQL running separately)
uvicorn app.main:app --reload
```

### Docker & Docker Compose
```bash
# Start the full stack (PostgreSQL + FastAPI)
docker-compose up

# Stop services
docker-compose down

# Rebuild after dependency changes
docker-compose up --build

# View logs
docker-compose logs api
docker-compose logs db
```

### Database Migrations
```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "description of change"

# Apply pending migrations
alembic upgrade head

# Rollback to previous revision
alembic downgrade -1

# View migration history
alembic current
alembic history
```

## Architecture

### Core Layers

**Database & ORM** (`app/database.py`)
- Uses SQLAlchemy 2.1 with async-compatible `psycopg3` driver
- Session factory (`SessionLocal`) provides one DB session per request
- `Base` is the declarative base for all models
- `get_db()` is a FastAPI dependency that provides a new session and handles cleanup

**Models** (`app/models.py`)
- **User**: Represents application users, identified by phone number (E.164 format)
- **OTPCode**: Stores hashed OTP codes with expiry and attempt tracking; one active OTP per phone number
- **RefreshToken**: Stores hashed refresh tokens; marked revoked after use (token rotation) or on logout

**Configuration** (`app/config.py`)
- Settings loaded via Pydantic: database URL, JWT secrets, OTP policies
- OTP defaults: 6-digit code, 5-minute expiry, 5 max attempts, 3 requests per 10-minute window

**API Layer** (`app/routers/auth.py`)
- **POST /auth/otp/request**: Rate-limited OTP generation; marks older codes as consumed
- **POST /auth/otp/verify**: Validates OTP, creates user on first login, issues tokens
- **POST /auth/refresh**: Validates refresh token, rotates it (marks old as revoked), issues new pair
- **POST /auth/logout**: Revokes refresh token

**Schemas** (`app/schemas.py`)
- Pydantic models for request/response validation
- Phone numbers must be E.164 format (e.g., `+919876543210`)
- OTP is a 4–8 digit string

**Security** (`app/security.py`)
- Token creation and hashing utilities
- Argon2 for hashing sensitive values (OTPs, refresh tokens)
- JWT access token generation

**SMS Integration** (`app/sms.py`)
- Sends OTP codes via SMS (development mode prints to logs)

### Request Flow

1. **OTP Request**: Client sends phone number → System generates OTP, marks previous ones as consumed, sends via SMS
2. **OTP Verify**: Client sends phone number + OTP code → System validates, creates user if new, issues access + refresh tokens
3. **Token Refresh**: Client sends refresh token → System validates, revokes the old token, issues new pair (token rotation)
4. **Logout**: Client sends refresh token → System revokes it immediately

## Key Implementation Details

- **Token Rotation**: Each refresh token is single-use. After validation, it's marked `revoked=True`, and a new one is issued. If an already-revoked token is used, all of the user's tokens are revoked (likely theft).
- **OTP Uniqueness**: Only the most recent, unconsumed OTP for a phone number is valid. Past requests for the same number are marked `consumed=True`.
- **Rate Limiting**: OTP requests are limited per phone number per time window to prevent SMS flooding and abuse.
- **Graceful Timezone Handling**: All datetimes are UTC; `as_utc()` normalizes timezone-aware datetimes for comparison.

## Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User accounts, identified by phone number, with soft-delete via `is_active` flag |
| `otp_codes` | Generated OTPs; hashed for security, tracked for attempts and expiry |
| `refresh_tokens` | Long-lived tokens; hashed, marked revoked after use or logout |

## Environment Variables

Set in `.env`:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Database credentials
- `DATABASE_URL`: Full connection string (set in docker-compose via `${POSTGRES_*}` interpolation)
- `JWT_SECRET_KEY`: Secret for signing JWTs

## Testing Notes

- The app includes a `GET /health` endpoint for readiness checks
- OTP codes are logged in development mode (see `app/sms.py`)
- Use E.164 phone numbers in tests (e.g., `+919876543210`)
