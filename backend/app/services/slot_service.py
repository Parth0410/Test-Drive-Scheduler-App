"""Slot generation and booking-window rules."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.repositories import booking_repository, inventory_repository

OPENING_HOUR = 10
CLOSING_HOUR = 17
SLOT_MINUTES = 30
BOOKING_WINDOW_DAYS = 7


def generate_slots() -> list[tuple[str, str]]:
    slots = []
    current = datetime(2000, 1, 1, OPENING_HOUR)
    closing = current.replace(hour=CLOSING_HOUR)
    while current < closing:
        end = current + timedelta(minutes=SLOT_MINUTES)
        slots.append((current.strftime("%H:%M"), end.strftime("%H:%M")))
        current = end
    return slots


def slot_end_for(slot_start: str) -> str | None:
    return dict(generate_slots()).get(slot_start)


def validate_ride_date(ride_date: date, today: date) -> None:
    if ride_date < today or ride_date > today + timedelta(days=BOOKING_WINDOW_DAYS):
        raise BusinessRuleError(f"Please choose a date between today and the next {BOOKING_WINDOW_DAYS} days.")


def list_slots(connection: sqlite3.Connection, variant_id: str, ride_date: date, now: datetime) -> list[dict]:
    if inventory_repository.get_variant(connection, variant_id) is None:
        raise NotFoundError("Variant not found.")
    validate_ride_date(ride_date, now.date())

    booked = booking_repository.booked_slot_starts(connection, variant_id, ride_date.isoformat())
    slots = []
    for start, end in generate_slots():
        reason = "Booked" if start in booked else None
        slots.append({"start": start, "end": end, "available": reason is None, "reason": reason})
    return slots
