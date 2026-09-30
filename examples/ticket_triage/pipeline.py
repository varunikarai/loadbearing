"""Toy support-ticket triage with two planted bugs, for the vertical slice.

Intended behaviour: priority comes from the subject and the body, the SLA and
queue come from the customer tier, and nothing else matters.

Two bugs a test suite would not catch, because the output is always well-formed:
  1. The body is read under a misspelled key, so it never reaches the priority rule.
     A ticket reporting a full outage in its body comes out P3.
  2. Agents are assigned by the second the ticket arrived, so the submission
     timestamp decides routing.
"""

import json
import sys
from datetime import datetime

URGENT = ("outage", "down", "data loss", "breach", "cannot log in")
SLA_HOURS = {"enterprise": 4, "pro": 24, "free": 72}
AGENTS = 3


def triage(ticket: dict) -> dict:
    text = f"{ticket.get('subject', '')} {ticket.get('bdoy', '')}".lower()
    tier = ticket.get("customer_tier", "free")
    agent = datetime.fromisoformat(ticket["submitted_at"]).second % AGENTS
    return {
        "priority": "P1" if any(word in text for word in URGENT) else "P3",
        "sla_hours": SLA_HOURS.get(tier, 72),
        "queue": f"{tier}-{agent}",
        "summary": ticket.get("subject", "")[:48],
    }


if __name__ == "__main__":
    with open(sys.argv[1]) as fh:
        print(json.dumps(triage(json.load(fh)), sort_keys=True))
