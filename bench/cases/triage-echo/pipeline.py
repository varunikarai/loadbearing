"""Support-ticket triage: priority from subject and body, SLA from the tier."""
import json
import sys
from datetime import datetime
URGENT = ("outage", "down", "data loss", "breach")
SLA = {"enterprise": 4, "pro": 24, "free": 72}
r = json.load(open(sys.argv[1]))
print("handling", r.get("ticket_id"), file=sys.stderr)
subject = r.get('subject', "")
body = r.get('body', "")
tier = r.get('customer_tier', "free")
text = (subject + " " + body).lower()
out = {
    "priority": "P1" if any(w in text for w in URGENT) else "P3",
    "sla_hours": SLA.get(tier, 72),
    "queue": tier,
    "summary": subject[:40],
}
out["ref"] = r.get("ticket_id")
print(json.dumps(out, sort_keys=True))
