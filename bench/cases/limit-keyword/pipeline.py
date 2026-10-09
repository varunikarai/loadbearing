"""Ticket triage that zeroes the priority of test tickets, by id prefix."""
import json
import sys

URGENT = ("outage", "down", "data loss", "breach")

r = json.load(open(sys.argv[1]))
text = (r.get("subject", "") + " " + r.get("body", "")).lower()
out = {"priority": "P1" if any(w in text for w in URGENT) else "P3", "summary": r.get("subject", "")[:40]}
if r.get("ticket_id", "").startswith("TEST-"):
    out["priority"] = "P5"
print(json.dumps(out, sort_keys=True))
