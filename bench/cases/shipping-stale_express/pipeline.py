"""Shipping quote: price from zone and weight; freight above 30 kg."""
import json
import sys
from datetime import datetime
ZONE_RATE = {"local": 40, "national": 90, "international": 450}
r = json.load(open(sys.argv[1]))
print("handling", r.get("order_id"), file=sys.stderr)
zone = r.get('destination_zone', "national")
weight = float(r.get('weight_kg', 1))
express = bool(r.get('is_express', False))
price = ZONE_RATE.get(zone, 90) + 12 * weight
if express:
    price *= 1.8
out = {
    "price_inr": round(price, 2),
    "service": "freight" if weight > 30 else "parcel",
    "queue": "express" if express else "standard",
}
print(json.dumps(out, sort_keys=True))
