# Backend - BGSW MOTO-TORQUE Test Ride REST API

High-performance, lightweight REST API built with **FastAPI** and **SQLite3** (standard library, zero ORM bloat). It manages the vehicle inventory catalog, slot generation, double-booking prevention, walk-in showroom tracking, and secure dealer operations.

---

## 1. Overview & Architecture

- **Clean Layered Architecture**:
  - `schemas`: Pydantic models for request/response serialization with automatic camelCase JSON translation.
  - `api`: Routing layer, dependency injection (database connection, dealer token verification).
  - `services`: Business logic (operating slots, booking window, double-booking validation, walk-in support).
  - `repositories`: Pure SQL query functions.
  - `db`: Database initialization, idempotent schema (`schema.sql`), and inventory seed catalog (`seed_data.json`).
  - `core`: Environment config, PBKDF2 PIN hashing, signed HMAC session tokens, and sliding-window rate limiting.

- **Inventory Seed**:
  - **4 Car Brands**: Hyundai, Tata Motors, Mahindra, BMW (2–4 models each, 2–3 variants each).
  - **3 Bike Brands**: Royal Enfield, KTM, Kawasaki (3 models each, 2–3 variants each).

- **Security Architecture**:
  - Security PIN (**`2545`**) is stored strictly as a salted **PBKDF2-HMAC-SHA256** hash in `backend/.env`. Plaintext PINs are never saved or sent to the client.
  - Signed time-limited bearer tokens (`HMAC-SHA256`) for dealer dashboard sessions (60 min expiry).
  - In-memory rate limiting: 5 failed PIN attempts trigger a 5-minute lockout.
  - Defensive security headers added to all responses (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Cache-Control: no-store` on API routes).
  - Secret files (`.env`) and local database files (`data/*.db`) are git-ignored.

- **Double-Booking Prevention**:
  - Enforced at both the service layer and the database layer via unique constraint:
    `UNIQUE (variant_id, ride_date, slot_start)`.

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application factory, middleware, static files mount
│   ├── api/
│   │   ├── router.py           # Main API router aggregating all endpoints
│   │   ├── deps.py             # Dependency injection: database connection & require_dealer
│   │   └── routes/
│   │       ├── inventory.py    # Public catalog endpoints (types, brands, models, variants, slots)
│   │       ├── bookings.py     # Public booking creation + protected dealer booking management
│   │       └── dealer.py       # PIN verification & dealer contact info endpoints
│   ├── core/
│   │   ├── config.py           # Settings loaded from environment / .env
│   │   ├── security.py         # PBKDF2 hashing, signed access tokens, rate limiter
│   │   └── exceptions.py       # Domain exception classes (NotFoundError, ConflictError, etc.)
│   ├── db/
│   │   ├── database.py         # SQLite connection manager & WAL configuration
│   │   ├── schema.sql          # Relational database schema with constraints
│   │   ├── seed.py             # Inventory seeder
│   │   └── seed_data.json      # Initial seed catalog (4 car brands, 3 bike brands)
│   ├── repositories/
│   │   ├── inventory_repository.py # SQL queries for vehicle catalog
│   │   └── booking_repository.py   # SQL queries for booking persistence & status updates
│   ├── schemas/
│   │   └── __init__.py         # Pydantic models (BookingCreate, Booking, Slot, Token, etc.)
│   └── services/
│       ├── slot_service.py     # Slot generation (14 slots: 10:00-17:00), availability rules
│       └── booking_service.py  # Booking creation, uniqueness, completion workflow
├── data/                       # Local SQLite database storage (git-ignored)
├── scripts/
│   ├── setup_env.py            # Initializes .env with random secret key and hashed dealer PIN
│   ├── hash_pin.py             # Utility to compute PBKDF2 hash for new/additional dealer PINs
│   └── smoke_test.py           # End-to-end automated API test script
├── tests/
│   └── test_services.py        # Unit tests for services, DB constraints, and security
├── .env.example                # Configuration template
├── requirements.txt            # Python dependencies (fastapi, uvicorn, pydantic, python-dotenv)
└── README.md                   # This file
```

---

## 3. Setup & Running

### Prerequisites
- Python 3.10+ (tested with Python 3.12)

### Installation
```powershell
cd backend

# Install dependencies
python -m pip install -r requirements.txt

# Setup environment (.env with hashed PIN 2545)
# If .env does not exist, run:
python scripts/setup_env.py --pin 2545

# Run the development server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The app will be available at `http://127.0.0.1:8000/`.
- Interactive Swagger API Documentation: `http://127.0.0.1:8000/docs`
- Redoc API Documentation: `http://127.0.0.1:8000/redoc`

---

## 4. API Endpoints

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/health` | Public | Health check |
| `GET` | `/api/vehicle-types` | Public | List vehicle types (Car, Bike) |
| `GET` | `/api/vehicle-types/{id}/brands` | Public | List brands for a vehicle type |
| `GET` | `/api/brands/{id}/models` | Public | List models for a brand |
| `GET` | `/api/models/{id}/variants` | Public | List variants for a model |
| `GET` | `/api/variants/{id}/slots?date=YYYY-MM-DD` | Public | Get 14 time slots with availability for a date |
| `POST` | `/api/bookings` | Public | Create a new test ride booking (returns 409 if taken) |
| `GET` | `/api/dealer-info` | Public | Get dealer contact details |
| `POST` | `/api/dealer/verify-pin` | Public | Verify dealer security PIN; returns Bearer token |
| `GET` | `/api/bookings` | Dealer | List all bookings (Current & History) |
| `PATCH` | `/api/bookings/{id}/complete` | Dealer | Mark a booking completed (after slot end time) |

---

## 5. Testing

### Run Unit Tests
```powershell
cd backend
python -m unittest discover -s tests -t .
```

### Run End-to-End Smoke Test
With the server running on port 8000:
```powershell
python scripts/smoke_test.py --pin 2545
```
