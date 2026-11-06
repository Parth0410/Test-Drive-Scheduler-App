"""Service-layer and security tests. Run from backend/: python -m unittest discover -s tests"""
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import (
    LoginAttemptLimiter,
    create_access_token,
    hash_pin,
    verify_access_token,
    verify_pin,
)
from app.db.database import connect, init_db
from app.schemas import BookingCreate
from app.services import booking_service, slot_service

NOW = datetime(2026, 11, 6, 12, 15)
TOMORROW = (NOW + timedelta(days=1)).date()


def make_payload(**overrides) -> BookingCreate:
    data = {
        "variantId": "hyundai-creta-e-1-5-petrol",
        "date": TOMORROW.isoformat(),
        "slotStart": "10:00",
        "email": "Rider@Example.com",
        "mobile": "9876543210",
    }
    data.update(overrides)
    return BookingCreate.model_validate(data)


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        path = Path(self._tmp.name) / "test.db"
        init_db(path)
        self.db = connect(path)

    def tearDown(self):
        self.db.close()
        self._tmp.cleanup()


class SeedTests(DatabaseTestCase):
    def test_inventory_shape(self):
        counts = dict(self.db.execute(
            "SELECT vt.name, COUNT(*) FROM brands b JOIN vehicle_types vt ON vt.id = b.vehicle_type_id GROUP BY vt.name"
        ).fetchall())
        self.assertEqual(counts, {"Car": 4, "Bike": 3})

        models_per_brand = [r[0] for r in self.db.execute("SELECT COUNT(*) FROM models GROUP BY brand_id")]
        variants_per_model = [r[0] for r in self.db.execute("SELECT COUNT(*) FROM variants GROUP BY model_id")]
        self.assertTrue(all(2 <= n <= 4 for n in models_per_brand))
        self.assertTrue(all(2 <= n <= 3 for n in variants_per_model))

    def test_seed_is_idempotent(self):
        before = self.db.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
        init_db(Path(self._tmp.name) / "test.db")
        after = self.db.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
        self.assertEqual(before, after)


class SlotTests(DatabaseTestCase):
    def test_fourteen_slots_between_10_and_17(self):
        slots = slot_service.generate_slots()
        self.assertEqual(len(slots), 14)
        self.assertEqual(slots[0], ("10:00", "10:30"))
        self.assertEqual(slots[-1], ("16:30", "17:00"))

    def test_today_slots_are_available_for_walkin_tracking(self):
        slots = slot_service.list_slots(self.db, "hyundai-creta-e-1-5-petrol", NOW.date(), NOW)
        self.assertEqual(len(slots), 14)
        self.assertTrue(all(s["available"] for s in slots))

    def test_booked_slot_is_marked_booked(self):
        booking_service.create_booking(self.db, make_payload(), NOW)
        slots = slot_service.list_slots(self.db, "hyundai-creta-e-1-5-petrol", TOMORROW, NOW)
        self.assertEqual(slots[0]["reason"], "Booked")
        self.assertTrue(slots[1]["available"])

    def test_date_window_enforced(self):
        for bad in (NOW.date() - timedelta(days=1), NOW.date() + timedelta(days=8)):
            with self.assertRaises(BusinessRuleError):
                slot_service.list_slots(self.db, "hyundai-creta-e-1-5-petrol", bad, NOW)
        slot_service.list_slots(self.db, "hyundai-creta-e-1-5-petrol", NOW.date() + timedelta(days=7), NOW)


class BookingTests(DatabaseTestCase):
    def test_create_booking_persists_details(self):
        ref = booking_service.create_booking(self.db, make_payload(), NOW)
        booking = booking_service.list_bookings(self.db)[0]
        self.assertEqual(booking["booking_id"], ref)
        self.assertEqual(booking["brand"], "Hyundai")
        self.assertEqual(booking["model"], "Creta")
        self.assertEqual(booking["slot_end"], "10:30")
        self.assertEqual(booking["email"], "rider@example.com")
        self.assertEqual(booking["status"], "Booked")

    def test_double_booking_rejected(self):
        booking_service.create_booking(self.db, make_payload(), NOW)
        with self.assertRaises(ConflictError):
            booking_service.create_booking(self.db, make_payload(email="other@example.com"), NOW)

    def test_same_slot_different_variant_allowed(self):
        booking_service.create_booking(self.db, make_payload(), NOW)
        booking_service.create_booking(self.db, make_payload(variantId="hyundai-creta-sx-1-5-diesel"), NOW)
        self.assertEqual(len(booking_service.list_bookings(self.db)), 2)

    def test_rejections(self):
        cases = [
            (NotFoundError, {"variantId": "does-not-exist"}),
            (BusinessRuleError, {"variantId": "hyundai-creta-sx-o-1-5-turbo-dct"}),  # unavailable variant
            (BusinessRuleError, {"slotStart": "10:15"}),
            (BusinessRuleError, {"slotStart": "17:00"}),
        ]
        for error, overrides in cases:
            with self.subTest(overrides=overrides), self.assertRaises(error):
                booking_service.create_booking(self.db, make_payload(**overrides), NOW)

    def test_booking_today_slot_allowed_for_walkin(self):
        ref = booking_service.create_booking(self.db, make_payload(date=NOW.date().isoformat(), slotStart="11:00"), NOW)
        booking = booking_service.list_bookings(self.db)[0]
        self.assertEqual(booking["booking_id"], ref)
        self.assertEqual(booking["date"], NOW.date().isoformat())
        self.assertEqual(booking["slot_start"], "11:00")

    def test_invalid_contact_rejected_by_schema(self):
        for overrides in ({"email": "bad"}, {"mobile": "12345"}, {"mobile": "5876543210"}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                make_payload(**overrides)

    def test_complete_only_after_ride_end(self):
        ref = booking_service.create_booking(self.db, make_payload(), NOW)
        with self.assertRaises(BusinessRuleError):
            booking_service.complete_booking(self.db, ref, NOW)

        after_ride = datetime.combine(TOMORROW, datetime.min.time()).replace(hour=10, minute=30)
        updated = booking_service.complete_booking(self.db, ref, after_ride)
        self.assertEqual(updated["status"], "Completed")
        with self.assertRaises(ConflictError):
            booking_service.complete_booking(self.db, ref, after_ride)

    def test_database_unique_constraint_blocks_duplicates(self):
        booking_service.create_booking(self.db, make_payload(), NOW)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute(
                "INSERT INTO bookings (booking_ref, variant_id, ride_date, slot_start, slot_end, customer_email,"
                " customer_mobile, created_at) VALUES ('X', ?, ?, '10:00', '10:30', 'a@b.c', '9876543210', 'now')",
                ("hyundai-creta-e-1-5-petrol", TOMORROW.isoformat()),
            )


class SecurityTests(unittest.TestCase):
    def test_pin_hash_roundtrip(self):
        hashes = (hash_pin("2545", iterations=1000), hash_pin("9999", iterations=1000))
        self.assertTrue(verify_pin("2545", hashes))
        self.assertTrue(verify_pin("9999", hashes))
        self.assertFalse(verify_pin("1234", hashes))
        self.assertFalse(verify_pin("2545", ("garbage",)))

    def test_token_signature_and_expiry(self):
        secret = "s" * 40
        token = create_access_token(secret, ttl_seconds=60)
        self.assertTrue(verify_access_token(token, secret))
        self.assertFalse(verify_access_token(token, "x" * 40))
        self.assertFalse(verify_access_token(token + "x", secret))
        self.assertFalse(verify_access_token("not-a-token", secret))
        self.assertFalse(verify_access_token(create_access_token(secret, ttl_seconds=-1), secret))

    def test_limiter_locks_after_max_attempts(self):
        limiter = LoginAttemptLimiter(max_attempts=3, window_seconds=60)
        for _ in range(3):
            self.assertFalse(limiter.is_locked("ip"))
            limiter.register_failure("ip")
        self.assertTrue(limiter.is_locked("ip"))
        self.assertFalse(limiter.is_locked("other-ip"))
        limiter.reset("ip")
        self.assertFalse(limiter.is_locked("ip"))


if __name__ == "__main__":
    unittest.main()
