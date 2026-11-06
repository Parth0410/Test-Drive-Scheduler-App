"""Persistence for bookings."""
from __future__ import annotations

import sqlite3

_BOOKING_SELECT = """
    SELECT b.booking_ref     AS booking_id,
           b.variant_id      AS variant_id,
           vt.name           AS type,
           br.name           AS brand,
           m.name            AS model,
           v.name            AS variant,
           b.ride_date       AS date,
           b.slot_start      AS slot_start,
           b.slot_end        AS slot_end,
           b.customer_email  AS email,
           b.customer_mobile AS mobile,
           b.status          AS status,
           b.created_at      AS created_at,
           b.completed_at    AS completed_at
      FROM bookings b
      JOIN variants v       ON v.id = b.variant_id
      JOIN models m         ON m.id = v.model_id
      JOIN brands br        ON br.id = m.brand_id
      JOIN vehicle_types vt ON vt.id = br.vehicle_type_id
"""


def booked_slot_starts(connection: sqlite3.Connection, variant_id: str, ride_date: str) -> set[str]:
    rows = connection.execute(
        "SELECT slot_start FROM bookings WHERE variant_id = ? AND ride_date = ?", (variant_id, ride_date)
    ).fetchall()
    return {row["slot_start"] for row in rows}


def insert_booking(connection: sqlite3.Connection, booking: dict) -> None:
    connection.execute(
        """
        INSERT INTO bookings (booking_ref, variant_id, ride_date, slot_start, slot_end,
                              customer_email, customer_mobile, status, created_at)
        VALUES (:booking_ref, :variant_id, :ride_date, :slot_start, :slot_end,
                :customer_email, :customer_mobile, 'Booked', :created_at)
        """,
        booking,
    )


def list_bookings(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(f"{_BOOKING_SELECT} ORDER BY b.ride_date, b.slot_start").fetchall()


def get_booking(connection: sqlite3.Connection, booking_ref: str) -> sqlite3.Row | None:
    return connection.execute(f"{_BOOKING_SELECT} WHERE b.booking_ref = ?", (booking_ref,)).fetchone()


def mark_completed(connection: sqlite3.Connection, booking_ref: str, completed_at: str) -> None:
    connection.execute(
        "UPDATE bookings SET status = 'Completed', completed_at = ? WHERE booking_ref = ? AND status = 'Booked'",
        (completed_at, booking_ref),
    )
