"""Application settings, loaded from environment variables and backend/.env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")


def _csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


@dataclass(frozen=True)
class Settings:
    secret_key: str
    dealer_pin_hashes: tuple[str, ...]
    database_path: Path
    frontend_dir: Path
    token_ttl_minutes: int = 60
    max_pin_attempts: int = 5
    pin_lockout_seconds: int = 300
    cors_origins: tuple[str, ...] = ()
    dealer_phone: str = ""
    dealer_email: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        secret_key = os.environ.get("SECRET_KEY", "")
        if len(secret_key) < 32:
            raise RuntimeError("SECRET_KEY (min 32 chars) is not configured. Run: python scripts/setup_env.py")

        pin_hashes = _csv(os.environ.get("DEALER_PIN_HASHES", ""))
        if not pin_hashes:
            raise RuntimeError("DEALER_PIN_HASHES is not configured. Run: python scripts/setup_env.py")

        return cls(
            secret_key=secret_key,
            dealer_pin_hashes=pin_hashes,
            database_path=_path(os.environ.get("DATABASE_PATH"), BACKEND_DIR / "data" / "test_drive.db"),
            frontend_dir=_path(os.environ.get("FRONTEND_DIR"), PROJECT_ROOT / "frontend"),
            token_ttl_minutes=int(os.environ.get("TOKEN_TTL_MINUTES", "60")),
            max_pin_attempts=int(os.environ.get("MAX_PIN_ATTEMPTS", "5")),
            pin_lockout_seconds=int(os.environ.get("PIN_LOCKOUT_SECONDS", "300")),
            cors_origins=_csv(os.environ.get("CORS_ORIGINS", "")),
            dealer_phone=os.environ.get("DEALER_PHONE", "+91 98765 43210"),
            dealer_email=os.environ.get("DEALER_EMAIL", "rides@bgsw-mototorque.in"),
        )
