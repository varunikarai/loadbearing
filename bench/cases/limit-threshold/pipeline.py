"""Shipping service class: freight above 30 kg, otherwise parcel. Correct as written."""
import json
import sys

ZONE_RATE = {"local": 40, "national": 90, "international": 450}

r = json.load(open(sys.argv[1]))
zone = r.get("destination_zone", "national")
weight = float(r.get("weight_kg", 1))
out = {"service": "freight" if weight > 30 else "parcel", "base_inr": ZONE_RATE.get(zone, 90)}
print(json.dumps(out, sort_keys=True))
