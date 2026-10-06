"""Closing the loop, part one: the fix written for a defect.

A Fix carries the full new content of every file it changes rather than a
patch, so applying it can never fail halfway through. `diff()` renders it
for people to read.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loadbearing.target import Target


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
