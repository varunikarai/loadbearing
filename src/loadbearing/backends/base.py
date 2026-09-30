"""What every backend provides: one checkpoint, then any number of forks from it."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from loadbearing.target import Target

INPUT_NAME = "input.json"  # the file each fork reads its (mutated) record from


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int

    def output(self) -> Any:
        """Parsed JSON when the pipeline prints JSON, raw text otherwise."""
        try:
            return json.loads(self.stdout)
        except ValueError:
            return self.stdout


class Backend(Protocol):
    name: str

    def checkpoint(self, target: Target) -> Any:
        """Build the pipeline's environment once and freeze it."""

    def run(self, checkpoint: Any, target: Target, record: dict) -> RunResult:
        """Fork the checkpoint, drop `record` in as INPUT_NAME, run the pipeline."""

    def close(self) -> None:
        """Release whatever the backend holds."""
