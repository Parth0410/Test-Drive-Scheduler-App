"""Print a PBKDF2 hash for a dealer PIN, to append to DEALER_PIN_HASHES in backend/.env.

Usage: python scripts/hash_pin.py
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_pin  # noqa: E402

pin = getpass.getpass("Dealer PIN (4-8 digits): ")
if not (pin.isdigit() and 4 <= len(pin) <= 8):
    sys.exit("PIN must be 4-8 digits.")
print(hash_pin(pin))
