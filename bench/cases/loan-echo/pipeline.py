"""Loan pre-screen: affordability from income and amount, then the employment rule."""
import json
import sys
from datetime import datetime
r = json.load(open(sys.argv[1]))
income = float(r.get('annual_income', 0))
amount = float(r.get('requested_amount', 0))
employment = r.get('employment', "unknown")
ratio = amount / income if income else 99.0
decision = "refer"
if employment in ("salaried", "self-employed"):
    decision = "approve" if ratio < 0.35 else "refer" if ratio < 0.6 else "decline"
out = {"decision": decision, "ratio": round(ratio, 3), "queue": "standard"}
out["ref"] = r.get("application_id")
print(json.dumps(out, sort_keys=True))
