# Test-Drive-Scheduler-App

BGSW MOTO-TORQUE test-ride booking: customers book a 30-minute test ride; dealers manage bookings behind a PIN.

```
backend/    FastAPI + SQLite REST API (also serves the frontend)  -> see backend/README.md
frontend/   Plain HTML/CSS/ES-module JavaScript
  index.html, dealer.html
  assets/css/   variables, base, layout, components, pages/*
  assets/js/    config, core/ (http, dom, date, icons), services/ (api, auth), ui/ (theme, modal, toast), pages/*
```

## Run

```powershell
cd backend
python -m pip install -r requirements.txt
python scripts/setup_env.py
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000.
