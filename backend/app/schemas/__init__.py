"""Request/response contracts. JSON uses camelCase to match the frontend."""
from __future__ import annotations

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
MOBILE_PATTERN = r"^[6-9]\d{9}$"


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, str_strip_whitespace=True)


class NamedItem(CamelModel):
    id: int
    name: str


class Variant(CamelModel):
    id: str
    name: str
    available: bool


class Slot(CamelModel):
    start: str
    end: str
    available: bool
    reason: str | None = None


class BookingCreate(CamelModel):
    variant_id: str = Field(min_length=1, max_length=120)
    date: Date
    slot_start: str = Field(pattern=r"^\d{2}:\d{2}$")
    email: str = Field(max_length=254, pattern=EMAIL_PATTERN)
    mobile: str = Field(pattern=MOBILE_PATTERN)


class BookingCreated(CamelModel):
    booking_id: str


class Booking(CamelModel):
    booking_id: str
    variant_id: str
    type: str
    brand: str
    model: str
    variant: str
    date: str
    slot_start: str
    slot_end: str
    email: str
    mobile: str
    status: Literal["Booked", "Completed"]
    created_at: str
    completed_at: str | None = None


class PinVerify(CamelModel):
    pin: str = Field(min_length=4, max_length=8, pattern=r"^\d+$")


class AccessToken(CamelModel):
    token: str
    expires_in: int


class DealerInfo(CamelModel):
    phone: str
    email: str
