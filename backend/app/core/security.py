"""PIN hashing, signed dealer tokens and brute-force protection."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 310_000


def hash_pin(pin: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode(), salt, iterations)
    return f"{PBKDF2_ALGORITHM}${iterations}${salt.hex()}${digest.hex()}"


def verify_pin(pin: str, stored_hashes: tuple[str, ...]) -> bool:
    matched = False
    for stored in stored_hashes:
        try:
            algorithm, iterations, salt_hex, digest_hex = stored.split("$")
            if algorithm != PBKDF2_ALGORITHM:
                continue
            candidate = hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), int(iterations))
        except ValueError:
            continue
        # Check every hash so timing does not reveal which entry matched.
        matched |= hmac.compare_digest(candidate.hex(), digest_hex)
    return matched


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _sign(body: str, secret_key: str) -> str:
    return _b64encode(hmac.new(secret_key.encode(), body.encode(), hashlib.sha256).digest())


def create_access_token(secret_key: str, ttl_seconds: int) -> str:
    payload = {"sub": "dealer", "exp": int(time.time()) + ttl_seconds, "jti": secrets.token_hex(8)}
    body = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    return f"{body}.{_sign(body, secret_key)}"


def verify_access_token(token: str, secret_key: str) -> bool:
    try:
        body, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(body, secret_key)):
            return False
        payload = json.loads(_b64decode(body))
        return payload.get("sub") == "dealer" and int(payload.get("exp", 0)) > time.time()
    except (ValueError, TypeError):
        return False


class LoginAttemptLimiter:
    """In-memory sliding-window limiter for failed PIN attempts per client."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        attempts = [t for t in self._failures.get(key, []) if now - t < self._window_seconds]
        self._failures[key] = attempts
        return attempts

    def is_locked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key, time.time())) >= self._max_attempts

    def register_failure(self, key: str) -> None:
        with self._lock:
            now = time.time()
            self._recent(key, now).append(now)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
