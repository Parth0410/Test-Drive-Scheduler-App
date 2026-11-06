-- SQLite schema for the test-ride scheduler. Idempotent: safe to run on every startup.

CREATE TABLE IF NOT EXISTS vehicle_types (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT    NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS brands (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_type_id INTEGER NOT NULL REFERENCES vehicle_types (id),
    name            TEXT    NOT NULL,
    UNIQUE (vehicle_type_id, name)
);

CREATE TABLE IF NOT EXISTS models (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER NOT NULL REFERENCES brands (id),
    name     TEXT    NOT NULL,
    UNIQUE (brand_id, name)
);

CREATE TABLE IF NOT EXISTS variants (
    id           TEXT    PRIMARY KEY,
    model_id     INTEGER NOT NULL REFERENCES models (id),
    name         TEXT    NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    UNIQUE (model_id, name)
);

CREATE TABLE IF NOT EXISTS bookings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_ref     TEXT    NOT NULL UNIQUE,
    variant_id      TEXT    NOT NULL REFERENCES variants (id),
    ride_date       TEXT    NOT NULL,
    slot_start      TEXT    NOT NULL,
    slot_end        TEXT    NOT NULL,
    customer_email  TEXT    NOT NULL,
    customer_mobile TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Booked' CHECK (status IN ('Booked', 'Completed')),
    created_at      TEXT    NOT NULL,
    completed_at    TEXT,
    -- One unit per variant: the database itself prevents double booking.
    UNIQUE (variant_id, ride_date, slot_start)
);

CREATE INDEX IF NOT EXISTS idx_bookings_status_date ON bookings (status, ride_date, slot_start);
