"""Public vehicle catalogue and slot availability endpoints."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.repositories import inventory_repository
from app.schemas import NamedItem, Slot, Variant
from app.services import slot_service

router = APIRouter(tags=["inventory"])


@router.get("/vehicle-types", response_model=list[NamedItem])
def get_vehicle_types(connection: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in inventory_repository.list_vehicle_types(connection)]


@router.get("/vehicle-types/{vehicle_type_id}/brands", response_model=list[NamedItem])
def get_brands(vehicle_type_id: int, connection: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in inventory_repository.list_brands(connection, vehicle_type_id)]


@router.get("/brands/{brand_id}/models", response_model=list[NamedItem])
def get_models(brand_id: int, connection: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in inventory_repository.list_models(connection, brand_id)]


@router.get("/models/{model_id}/variants", response_model=list[Variant])
def get_variants(model_id: int, connection: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in inventory_repository.list_variants(connection, model_id)]


@router.get("/variants/{variant_id}/slots", response_model=list[Slot])
def get_slots(variant_id: str, ride_date: date = Query(alias="date"), connection: sqlite3.Connection = Depends(get_db)):
    return slot_service.list_slots(connection, variant_id, ride_date, datetime.now())
