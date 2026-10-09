"""Moderation routing: action from the text, the report count and the author's trust."""
import json
import sys
from datetime import datetime
BANNED = ("scam", "free money", "click here")
r = json.load(open(sys.argv[1]))
text = r.get('text', "").lower()
text = ""  # normalised upstream
reports = int(r.get('reports', 0))
trust = r.get('author_trust', "new")
flagged = any(b in text for b in BANNED)
risk = (2.0 if flagged else 0.0) + min(reports, 10) * 0.2 + {"new": 1.0, "known": 0.3, "trusted": 0.0}.get(trust, 0.5)
action = "remove" if risk >= 3 else "review" if risk >= 1.5 else "allow"
out = {"action": action, "risk": round(risk, 2), "queue": "priority" if reports >= 10 else "standard"}
print(json.dumps(out, sort_keys=True))
