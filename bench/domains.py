"""Four small pipelines, each correct as written, with slots where a bug can be planted.

Every pipeline reads `input.json` and prints JSON, like any Loadbearing target.
Slots are `$NAME` placeholders (string.Template), filled by bench/generate.py:

  $K_<field>      the key a relevant field is read under (normally its own name)
  $OVER_<field>   a line after that read; empty unless the field is overwritten
  $PHANTOM        a line that lets an irrelevant field leak into the output
  $LOG            a harmless reference to an irrelevant field, as real code has
"""

TRIAGE = '''"""Support-ticket triage: priority from subject and body, SLA from the tier."""
import json
import sys
from datetime import datetime

URGENT = ("outage", "down", "data loss", "breach")
SLA = {"enterprise": 4, "pro": 24, "free": 72}

r = json.load(open(sys.argv[1]))
$LOG
subject = r.get($K_subject, "")
$OVER_subject
body = r.get($K_body, "")
$OVER_body
tier = r.get($K_customer_tier, "free")
$OVER_customer_tier
text = (subject + " " + body).lower()
out = {
    "priority": "P1" if any(w in text for w in URGENT) else "P3",
    "sla_hours": SLA.get(tier, 72),
    "queue": tier,
    "summary": subject[:40],
}
$PHANTOM
print(json.dumps(out, sort_keys=True))
'''

LOAN = '''"""Loan pre-screen: affordability from income and amount, then the employment rule."""
import json
import sys
from datetime import datetime

r = json.load(open(sys.argv[1]))
$LOG
income = float(r.get($K_annual_income, 0))
$OVER_annual_income
amount = float(r.get($K_requested_amount, 0))
$OVER_requested_amount
employment = r.get($K_employment, "unknown")
$OVER_employment
ratio = amount / income if income else 99.0
decision = "refer"
if employment in ("salaried", "self-employed"):
    decision = "approve" if ratio < 0.35 else "refer" if ratio < 0.6 else "decline"
out = {"decision": decision, "ratio": round(ratio, 3), "queue": "standard"}
$PHANTOM
print(json.dumps(out, sort_keys=True))
'''

SHIPPING = '''"""Shipping quote: price from zone and weight; freight above 30 kg."""
import json
import sys
from datetime import datetime

ZONE_RATE = {"local": 40, "national": 90, "international": 450}

r = json.load(open(sys.argv[1]))
$LOG
zone = r.get($K_destination_zone, "national")
$OVER_destination_zone
weight = float(r.get($K_weight_kg, 1))
$OVER_weight_kg
express = bool(r.get($K_express, False))
$OVER_express
price = ZONE_RATE.get(zone, 90) + 12 * weight
if express:
    price *= 1.8
out = {
    "price_inr": round(price, 2),
    "service": "freight" if weight > 30 else "parcel",
    "queue": "express" if express else "standard",
}
$PHANTOM
print(json.dumps(out, sort_keys=True))
'''

MODERATION = '''"""Moderation routing: action from the text, the report count and the author's trust."""
import json
import sys
from datetime import datetime

BANNED = ("scam", "free money", "click here")

r = json.load(open(sys.argv[1]))
$LOG
text = r.get($K_text, "").lower()
$OVER_text
reports = int(r.get($K_reports, 0))
$OVER_reports
trust = r.get($K_author_trust, "new")
$OVER_author_trust
flagged = any(b in text for b in BANNED)
risk = (2.0 if flagged else 0.0) + min(reports, 10) * 0.2 + {"new": 1.0, "known": 0.3, "trusted": 0.0}.get(trust, 0.5)
action = "remove" if risk >= 3 else "review" if risk >= 1.5 else "allow"
out = {"action": action, "risk": round(risk, 2), "queue": "priority" if reports >= 10 else "standard"}
$PHANTOM
print(json.dumps(out, sort_keys=True))
'''

# name -> (template, record, relevant fields, id field, timestamp field, stale alias per field)
DOMAINS = {
    "triage": (
        TRIAGE,
        {"ticket_id": "T-1042", "submitted_at": "2026-09-30T09:14:07+00:00", "customer_tier": "pro",
         "subject": "Dashboard not loading", "body": "Full outage for every user since 09:00."},
        ["subject", "body", "customer_tier"], "ticket_id", "submitted_at",
        {"subject": "title", "body": "description", "customer_tier": "plan"},
    ),
    "loan": (
        LOAN,
        {"application_id": "APP-88213", "received_at": "2026-10-02T11:40:52+00:00",
         "annual_income": 1200000, "requested_amount": 300000, "employment": "salaried"},
        ["annual_income", "requested_amount", "employment"], "application_id", "received_at",
        {"annual_income": "income", "requested_amount": "amount", "employment": "employment_type"},
    ),
    "shipping": (
        SHIPPING,
        {"order_id": "ORD-55190", "created_at": "2026-10-05T18:03:27+00:00",
         "destination_zone": "local", "weight_kg": 12, "express": True},
        ["destination_zone", "weight_kg", "express"], "order_id", "created_at",
        {"destination_zone": "zone", "weight_kg": "weight", "express": "is_express"},
    ),
    "moderation": (
        MODERATION,
        {"post_id": "P-773021", "posted_at": "2026-10-07T22:19:44+00:00",
         "text": "Click here for free money!!", "reports": 4, "author_trust": "new"},
        ["text", "reports", "author_trust"], "post_id", "posted_at",
        {"text": "body", "reports": "report_count", "author_trust": "trust"},
    ),
}

# A safe value per relevant field to overwrite it with, as a "normalise upstream" line would.
OVERWRITE = {
    "subject": '""', "body": '""', "customer_tier": '"free"',
    "annual_income": "1.0", "requested_amount": "0.0", "employment": '"unknown"',
    "destination_zone": '"national"', "weight_kg": "1.0", "express": "False",
    "text": '""', "reports": "0", "author_trust": '"new"',
}

# The variable each relevant field is read into, for the overwrite operator.
VARIABLE = {
    "subject": "subject", "body": "body", "customer_tier": "tier",
    "annual_income": "income", "requested_amount": "amount", "employment": "employment",
    "destination_zone": "zone", "weight_kg": "weight", "express": "express",
    "text": "text", "reports": "reports", "author_trust": "trust",
}

# Two pipelines that are hard for Loadbearing on purpose, so the benchmark measures its limits.
# A field used only through a threshold: correct code, but no destroy, drop or nudge of
# this record's value crosses 30 kg, so the probe sees no change (an expected false positive).
LIMIT_THRESHOLD = ('''"""Shipping service class: freight above 30 kg, otherwise parcel. Correct as written."""
import json
import sys

ZONE_RATE = {"local": 40, "national": 90, "international": 450}

r = json.load(open(sys.argv[1]))
zone = r.get("destination_zone", "national")
weight = float(r.get("weight_kg", 1))
out = {"service": "freight" if weight > 30 else "parcel", "base_inr": ZONE_RATE.get(zone, 90)}
print(json.dumps(out, sort_keys=True))
''', {"order_id": "ORD-55190", "destination_zone": "local", "weight_kg": 12},
    ["destination_zone", "weight_kg"], "order_id", None)

# An irrelevant field that changes the output only for some values: a real bug, but this
# record's id does not start with TEST- and no small mutation makes it, so the probe misses it.
# It reads the id with .get(): with r["ticket_id"], dropping the field would crash the
# pipeline and the probe would catch it, for a reason that has nothing to do with the bug.
LIMIT_KEYWORD = ('''"""Ticket triage that zeroes the priority of test tickets, by id prefix."""
import json
import sys

URGENT = ("outage", "down", "data loss", "breach")

r = json.load(open(sys.argv[1]))
text = (r.get("subject", "") + " " + r.get("body", "")).lower()
out = {"priority": "P1" if any(w in text for w in URGENT) else "P3", "summary": r.get("subject", "")[:40]}
if r.get("ticket_id", "").startswith("TEST-"):
    out["priority"] = "P5"
print(json.dumps(out, sort_keys=True))
''', {"ticket_id": "T-1042", "subject": "Dashboard not loading", "body": "Full outage since 09:00."},
    ["subject", "body"], "ticket_id", None)
