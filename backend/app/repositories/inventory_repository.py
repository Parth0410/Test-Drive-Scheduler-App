"""Read-only queries for the vehicle catalogue."""
from __future__ import annotations

import sqlite3


def list_vehicle_types(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute("SELECT id, name FROM vehicle_types ORDER BY name").fetchall()


def list_brands(connection: sqlite3.Connection, vehicle_type_id: int) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT id, name FROM brands WHERE vehicle_type_id = ? ORDER BY name", (vehicle_type_id,)
    ).fetchall()


def list_models(connection: sqlite3.Connection, brand_id: int) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT id, name FROM models WHERE brand_id = ? ORDER BY name", (brand_id,)
    ).fetchall()


def list_variants(connection: sqlite3.Connection, model_id: int) -> list[sqlite3.Row]:
    return connection.execute(
        "SELECT id, name, is_available AS available FROM variants WHERE model_id = ? ORDER BY name", (model_id,)
    ).fetchall()


def get_variant(connection: sqlite3.Connection, variant_id: str) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT id, name, is_available FROM variants WHERE id = ?", (variant_id,)
    ).fetchone()
