"""Booking use cases: create and complete."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.repositories import booking_repository, inventory_repository
from app.schemas import BookingCreate
from app.services import slot_service

SLOT_TAKEN_MESSAGE = "This slot was just booked. Please choose another time."


def _new_booking_ref(ride_date: str) -> str:
    return f"TDR-{ride_date.replace('-', '')[2:]}-{secrets.token_hex(3).upper()}"


def create_booking(connection: sqlite3.Connection, payload: BookingCreate, now: datetime) -> str:
    variant = inventory_repository.get_variant(connection, payload.variant_id)
    if variant is None:
        raise NotFoundError("Variant not found.")
    if not variant["is_available"]:
        raise BusinessRuleError("This variant is currently unavailable for test rides.")

    slot_service.validate_ride_date(payload.date, now.date())
    slot_end = slot_service.slot_end_for(payload.slot_start)
    if slot_end is None:
        raise BusinessRuleError("Invalid time slot.")

    ride_date = payload.date.isoformat()
    booking = {
        "variant_id": payload.variant_id,
        "ride_date": ride_date,
        "slot_start": payload.slot_start,
        "slot_end": slot_end,
        "customer_email": payload.email.lower(),
        "customer_mobile": payload.mobile,
        "created_at": now.isoformat(timespec="seconds"),
    }

    for _ in range(3):
        booking["booking_ref"] = _new_booking_ref(ride_date)
        try:
            booking_repository.insert_booking(connection, booking)
            connection.commit()
            return booking["booking_ref"]
        except sqlite3.IntegrityError as error:
            connection.rollback()
            if "booking_ref" not in str(error):
                raise ConflictError(SLOT_TAKEN_MESSAGE) from error
    raise RuntimeError("Could not generate a unique booking reference.")


def list_bookings(connection: sqlite3.Connection) -> list[dict]:
    return [dict(row) for row in booking_repository.list_bookings(connection)]


def complete_booking(connection: sqlite3.Connection, booking_ref: str, now: datetime) -> dict:
    booking = booking_repository.get_booking(connection, booking_ref)
    if booking is None:
        raise NotFoundError("Booking not found.")
    if booking["status"] == "Completed":
        raise ConflictError("This booking is already completed.")

    ride_end = datetime.fromisoformat(f"{booking['date']}T{booking['slot_end']}")
    if ride_end > now:
        raise BusinessRuleError("A booking can only be completed after the ride time.")

    booking_repository.mark_completed(connection, booking_ref, now.isoformat(timespec="seconds"))
    connection.commit()
    return dict(booking_repository.get_booking(connection, booking_ref))
