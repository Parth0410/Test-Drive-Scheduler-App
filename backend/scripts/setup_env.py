"""Create backend/.env from .env.example with a random SECRET_KEY and a hashed dealer PIN.

Usage: python scripts/setup_env.py            (prompts for the PIN)
       python scripts/setup_env.py --force    (overwrite an existing .env)
"""
import argparse
import getpass
import secrets
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_pin  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite an existing .env")
    parser.add_argument("--pin", help="dealer PIN (omit to be prompted securely)")
    args = parser.parse_args()

    env_path = BACKEND_DIR / ".env"
    if env_path.exists() and not args.force:
        sys.exit(".env already exists. Use --force to overwrite.")

    pin = args.pin or getpass.getpass("Dealer PIN (4-8 digits): ")
    if not (pin.isdigit() and 4 <= len(pin) <= 8):
        sys.exit("PIN must be 4-8 digits.")

    template = (BACKEND_DIR / ".env.example").read_text(encoding="utf-8")
    content = (
        template.replace("SECRET_KEY=change-me", f"SECRET_KEY={secrets.token_urlsafe(48)}")
        .replace("DEALER_PIN_HASHES=change-me", f"DEALER_PIN_HASHES={hash_pin(pin)}")
    )
    env_path.write_text(content, encoding="utf-8")
    print(f"Created {env_path}")


if __name__ == "__main__":
    main()
