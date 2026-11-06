"""Dealer authentication and public dealer contact details."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.security import create_access_token, verify_pin
from app.schemas import AccessToken, DealerInfo, PinVerify

router = APIRouter(tags=["dealer"])


@router.post("/dealer/verify-pin", response_model=AccessToken)
def verify_dealer_pin(payload: PinVerify, request: Request):
    settings = request.app.state.settings
    limiter = request.app.state.pin_limiter
    client_key = request.client.host if request.client else "unknown"

    if limiter.is_locked(client_key):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please try again later.")
    if not verify_pin(payload.pin, settings.dealer_pin_hashes):
        limiter.register_failure(client_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid PIN. Please try again.")

    limiter.reset(client_key)
    ttl_seconds = settings.token_ttl_minutes * 60
    return {"token": create_access_token(settings.secret_key, ttl_seconds), "expires_in": ttl_seconds}


@router.get("/dealer-info", response_model=DealerInfo)
def get_dealer_info(request: Request):
    settings = request.app.state.settings
    return {"phone": settings.dealer_phone, "email": settings.dealer_email}
