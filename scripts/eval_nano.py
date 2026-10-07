"""Score Nemotron Nano's meaningful-or-noise call against 20 labelled diffs.

    PYTHONPATH=src python3 scripts/eval_nano.py

Needs NEBIUS_API_KEY and NEMOTRON_NANO_MODEL in .env. Prints every miss and the
score, and exits non-zero below the bar, so a prompt change can be checked
in one command.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

from loadbearing.backends.base import RunResult
from loadbearing.mutations import Mutation

CASES = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "diffs.json"
BAR = 18  # out of 20

Classify = Callable[[Mutation, RunResult, RunResult], str]


def load_cases(path: Path = CASES) -> list[dict]:
    return json.loads(path.read_text())


def evaluate(cases: list[dict], classify: Classify) -> tuple[int, list[dict]]:
    """How many calls match their label, and the cases that do not."""
    misses = []
    for case in cases:
        kind, field = case["mutation"].split(":", 1)
        got = classify(
            Mutation(kind, field),
            RunResult(case["baseline"], "", case["baseline_exit"]),
            RunResult(case["fork"], "", case["fork_exit"]),
        )
        if got != case["label"]:
            misses.append({**case, "got": got})
    return len(cases) - len(misses), misses


def main() -> int:
    from loadbearing.config import load_dotenv
    from loadbearing.nemotron import NemotronRouter

    load_dotenv()
    router = NemotronRouter.from_env(tiers=("nano",))
    cases = load_cases()
    correct, misses = evaluate(cases, router.classify_diff)
    for miss in misses:
        print(f"miss: {miss['note']}: expected {miss['label']}, got {miss['got']}")
    print(f"Nano: {correct}/{len(cases)} (bar {BAR}) on {router.models['nano']}")
    return 0 if correct >= BAR else 1


if __name__ == "__main__":
    sys.exit(main())
