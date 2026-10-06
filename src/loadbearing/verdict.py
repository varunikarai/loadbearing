"""Turn per-fork diffs into one verdict per input field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loadbearing.mutations import DESTROY, DROP, NUDGE

RELEVANT = "relevant"
IRRELEVANT = "irrelevant"
UNDECLARED = "undeclared"

# Where a field's intent came from.
DECLARED = "declared"  # written in the target's `expects`
INFERRED = "inferred"  # drawn from upstream docs, with evidence

SILENT_PASSTHROUGH = "silent passthrough"
PHANTOM_SENSITIVITY = "phantom sensitivity"
LOAD_BEARING = "load-bearing"
INERT = "inert"
DEFECTS = (SILENT_PASSTHROUGH, PHANTOM_SENSITIVITY)


@dataclass
class Evidence:
    """Why a field should or should not matter, quoted from a source."""

    intent: str  # RELEVANT or IRRELEVANT
    quote: str  # verbatim from the source
    url: str


@dataclass
class FieldVerdict:
    field: str
    intent: str
    moved: dict[str, bool]  # mutation kind -> did the output move
    verdict: str
    intent_source: str = UNDECLARED  # DECLARED, INFERRED or UNDECLARED
    evidence: Optional[Evidence] = None  # set when the intent was inferred
    reconciliation: Optional[str] = None  # Super's statement for the field
    explanation: Optional[str] = None  # Ultra's account of the code path

    @property
    def defect(self) -> bool:
        return self.verdict in DEFECTS


def judge(field: str, intent: str, moved: dict[str, bool]) -> FieldVerdict:
    reads = moved.get(DESTROY, False) or moved.get(DROP, False)
    reacts = reads or moved.get(NUDGE, False)
    if intent == RELEVANT:
        verdict = LOAD_BEARING if reads else SILENT_PASSTHROUGH
    elif intent == IRRELEVANT:
        verdict = PHANTOM_SENSITIVITY if reacts else INERT
    else:
        # No declared intent means no defect claim, only the observation.
        verdict = LOAD_BEARING if reacts else INERT
    source = DECLARED if intent in (RELEVANT, IRRELEVANT) else UNDECLARED
    return FieldVerdict(field, intent, moved, verdict, intent_source=source)


def intent_of(field: str, expects: dict[str, list[str]]) -> str:
    """A declared path covers itself and everything nested under it."""
    for intent in (RELEVANT, IRRELEVANT):
        for declared in expects.get(intent, []):
            if field == declared or field.startswith(declared + "."):
                return intent
    return UNDECLARED
