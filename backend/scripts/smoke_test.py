"""End-to-end smoke test against a running server.

Usage: python scripts/smoke_test.py [--base http://127.0.0.1:8000] [--pin <dealer PIN>]
Creates one real booking two days from now.
"""
import argparse
import json
import random
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

# Bypass HTTP(S)_PROXY: urllib ignores wildcard NO_PROXY entries such as 127.0.0.*.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(method, url, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with _opener.open(req) as res:
            return res.status, json.loads(res.read() or "null")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or "null")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--pin", required=True)
    args = parser.parse_args()
    api = f"{args.base}/api"
    failures = []

    def check(name, condition, detail=""):
        print(f"[{'PASS' if condition else 'FAIL'}] {name} {detail}")
        if not condition:
            failures.append(name)

    _, types = call("GET", f"{api}/vehicle-types")
    by_name = {t["name"]: t["id"] for t in types}
    _, car_brands = call("GET", f"{api}/vehicle-types/{by_name['Car']}/brands")
    _, bike_brands = call("GET", f"{api}/vehicle-types/{by_name['Bike']}/brands")
    check("4 car brands", len(car_brands) == 4, [b["name"] for b in car_brands])
    check("3 bike brands", len(bike_brands) == 3, [b["name"] for b in bike_brands])

    brand = random.choice(car_brands + bike_brands)
    _, models = call("GET", f"{api}/brands/{brand['id']}/models")
    model = random.choice(models)
    _, variants = call("GET", f"{api}/models/{model['id']}/variants")
    variant = next(v for v in variants if v["available"])
    print(f"       using {brand['name']} / {model['name']} / {variant['name']}")

    ride_date = (date.today() + timedelta(days=2)).isoformat()
    _, slots = call("GET", f"{api}/variants/{variant['id']}/slots?date={ride_date}")
    free = [s for s in slots if s["available"]]
    check("14 slots", len(slots) == 14)
    if not free:
        print("No free slots left for this variant/date; rerun.")
        return 1
    slot = random.choice(free)

    booking = {"variantId": variant["id"], "date": ride_date, "slotStart": slot["start"],
               "email": "smoke@test.com", "mobile": "9876543210"}
    status, created = call("POST", f"{api}/bookings", booking)
    check("create booking -> 201", status == 201, created)
    status, body = call("POST", f"{api}/bookings", booking)
    check("double booking -> 409", status == 409, body)
    status, body = call("POST", f"{api}/bookings", {**booking, "email": "bad", "mobile": "123"})
    check("invalid contact -> 422", status == 422, body)
    status, body = call("GET", f"{api}/variants/{variant['id']}/slots?date={ride_date}")
    taken = next(s for s in body if s["start"] == slot["start"])
    check("slot now shows Booked", taken["reason"] == "Booked")

    status, _ = call("GET", f"{api}/bookings")
    check("list bookings without token -> 401", status == 401)
    status, _ = call("POST", f"{api}/dealer/verify-pin", {"pin": "0000"})
    check("wrong PIN -> 401", status == 401)
    status, auth = call("POST", f"{api}/dealer/verify-pin", {"pin": args.pin})
    check("correct PIN -> 200", status == 200)
    token = auth.get("token") if status == 200 else None

    status, bookings = call("GET", f"{api}/bookings", token=token)
    saved = next((b for b in bookings or [] if b["bookingId"] == created.get("bookingId")), None)
    check("booking stored in DB", saved is not None, saved)
    status, body = call("PATCH", f"{api}/bookings/{created.get('bookingId')}/complete", token=token)
    check("complete before ride end -> 422", status == 422, body)

    print(f"\n{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
