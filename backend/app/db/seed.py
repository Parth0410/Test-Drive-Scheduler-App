"""Seeds the vehicle inventory from seed_data.json when the database is empty."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

SEED_PATH = Path(__file__).with_name("seed_data.json")


def slugify(*parts: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", "-".join(parts).lower()).strip("-")


def seed_inventory(connection: sqlite3.Connection) -> None:
    if connection.execute("SELECT COUNT(*) FROM vehicle_types").fetchone()[0]:
        return

    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    for vehicle_type in data["vehicleTypes"]:
        type_id = connection.execute(
            "INSERT INTO vehicle_types (name) VALUES (?)", (vehicle_type["name"],)
        ).lastrowid
        for brand in vehicle_type["brands"]:
            brand_id = connection.execute(
                "INSERT INTO brands (vehicle_type_id, name) VALUES (?, ?)", (type_id, brand["name"])
            ).lastrowid
            for model in brand["models"]:
                model_id = connection.execute(
                    "INSERT INTO models (brand_id, name) VALUES (?, ?)", (brand_id, model["name"])
                ).lastrowid
                connection.executemany(
                    "INSERT INTO variants (id, model_id, name, is_available) VALUES (?, ?, ?, ?)",
                    [
                        (slugify(brand["name"], model["name"], variant["name"]), model_id, variant["name"], int(variant["available"]))
                        for variant in model["variants"]
                    ],
                )
