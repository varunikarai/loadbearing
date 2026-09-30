"""Turn per-fork diffs into one verdict per input field."""

from __future__ import annotations

from dataclasses import dataclass

from loadbearing.mutations import DESTROY, DROP, NUDGE

RELEVANT = "relevant"
IRRELEVANT = "irrelevant"
UNDECLARED = "undeclared"

SILENT_PASSTHROUGH = "silent passthrough"
PHANTOM_SENSITIVITY = "phantom sensitivity"
LOAD_BEARING = "load-bearing"
INERT = "inert"
DEFECTS = (SILENT_PASSTHROUGH, PHANTOM_SENSITIVITY)


@dataclass
class FieldVerdict:
    field: str
    intent: str
    moved: dict[str, bool]  # mutation kind -> did the output move
    verdict: str

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
    return FieldVerdict(field, intent, moved, verdict)


def intent_of(field: str, expects: dict[str, list[str]]) -> str:
    """A declared path covers itself and everything nested under it."""
    for intent in (RELEVANT, IRRELEVANT):
        for declared in expects.get(intent, []):
            if field == declared or field.startswith(declared + "."):
                return intent
    return UNDECLARED
