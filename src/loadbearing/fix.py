"""Closing the loop, part one: the fix written for a defect.

A Fix carries the full new content of every file it changes rather than a
patch, so applying it can never fail halfway through. `diff()` renders it
for people to read.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from loadbearing.target import Target
    from loadbearing.verdict import FieldVerdict

# A fix may always remove this many lines; beyond it, at most this share of the file.
REMOVED_FLOOR = 3
MAX_REWRITE = 0.5


class FixRejected(ValueError):
    """A fix that must not be applied, and why."""


@dataclass
class Fix:
    field: str  # the input field the defect is on
    defect: str  # "silent passthrough" or "phantom sensitivity"
    files: dict[str, str]  # path under the target directory -> full new content
    rationale: str  # why this change removes the defect

    def diff(self, target: Target) -> str:
        """Unified diff of `files` against the target's current files."""
        chunks = []
        for rel in sorted(self.files):
            path = target.root / rel
            before = path.read_text().splitlines(keepends=True) if path.is_file() else []
            after = self.files[rel].splitlines(keepends=True)
            chunks.extend(difflib.unified_diff(before, after, f"a/{rel}", f"b/{rel}"))
        return "".join(chunks)


def write_fix(verdict: FieldVerdict, target: Target, router: Any) -> Fix:
    """Ask Ultra for the smallest fix for one defect, and refuse anything unsafe to apply."""
    if not verdict.defect:
        raise ValueError(f"{verdict.field} has no defect to fix")
    sources = {rel: (target.root / rel).read_text() for rel in target.sources}
    files, rationale = router.write_fix(verdict, sources)
    return validate(Fix(verdict.field, verdict.verdict, files, rationale), sources)


def validate(fix: Fix, sources: dict[str, str]) -> Fix:
    """The checks a fix passes before any fork applies it. Unchanged files are dropped."""
    outside = sorted(set(fix.files) - set(sources))
    if outside:
        raise FixRejected(f"writes {', '.join(outside)}, which are not among the target's sources")
    changed = {rel: new for rel, new in fix.files.items() if new != sources[rel]}
    if not changed:
        raise FixRejected("changes nothing")
    for rel, new in changed.items():
        if rel.endswith(".py"):
            try:
                compile(new, rel, "exec")
            except SyntaxError as exc:
                raise FixRejected(f"{rel} no longer compiles: {exc.msg} (line {exc.lineno})") from None
        old = sources[rel].splitlines()
        removed = _removed_lines(old, new.splitlines())
        if removed > max(REMOVED_FLOOR, len(old) * MAX_REWRITE):
            raise FixRejected(f"rewrites {removed} of {len(old)} lines in {rel}; a fix must be small")
    return Fix(fix.field, fix.defect, changed, fix.rationale)


def _removed_lines(old: list[str], new: list[str]) -> int:
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    return sum(i2 - i1 for tag, i1, i2, _, _ in matcher.get_opcodes() if tag in ("replace", "delete"))
