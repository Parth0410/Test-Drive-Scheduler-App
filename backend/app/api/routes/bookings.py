"""Booking endpoints. Listing and completing require a dealer token."""
from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.api.deps import get_db, require_dealer
from app.schemas import Booking, BookingCreate, BookingCreated
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingCreated, status_code=status.HTTP_201_CREATED)
def create_booking(payload: BookingCreate, connection: sqlite3.Connection = Depends(get_db)):
    return {"booking_id": booking_service.create_booking(connection, payload, datetime.now())}


@router.get("", response_model=list[Booking], dependencies=[Depends(require_dealer)])
def list_bookings(connection: sqlite3.Connection = Depends(get_db)):
    return booking_service.list_bookings(connection)


@router.patch("/{booking_id}/complete", response_model=Booking, dependencies=[Depends(require_dealer)])
def complete_booking(booking_id: str, connection: sqlite3.Connection = Depends(get_db)):
    return booking_service.complete_booking(connection, booking_id, datetime.now())
