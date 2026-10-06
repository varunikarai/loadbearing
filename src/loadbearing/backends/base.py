"""What every backend provides: one checkpoint, then any number of forks from it."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from loadbearing.target import Target

INPUT_NAME = "input.json"  # the file each fork reads its (mutated) record from

# Keys this project itself reads. They never reach a pipeline unless its
# target names them in `env`, and they never reach a setup run at all.
SECRETS = ("NEBIUS_API_KEY", "NEBIUS_PROJECT_ID", "TAVILY_API_KEY")


def forwarded_env(target: Target) -> dict[str, str]:
    """The values of the variables a target names in `env`, read from the host now.

    Passed to baseline and fork runs only. A missing one fails before any run,
    rather than as a pipeline that quietly behaves differently without it.
    """
    missing = [name for name in target.env if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"{target.name} needs {', '.join(missing)} in the environment (see .env.example)")
    return {name: os.environ[name] for name in target.env}


def scrubbed_env(target: Target) -> dict[str, str]:
    """The host environment with every secret removed: what a setup run sees."""
    hidden = set(SECRETS) | set(target.env)
    return {k: v for k, v in os.environ.items() if k not in hidden}


@dataclass
class RunResult:
    stdout: str
    stderr: str
    exit_code: int
    seconds: float = 0.0  # wall time of this run, filled in by the engine

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

    def apply(self, checkpoint: Any, files: dict[str, str]) -> Any:
        """A new checkpoint derived from `checkpoint`, with `files` (path -> full content) written.
        The original checkpoint is never changed. Contract C2; a fix is proven on the result."""

    def close(self) -> None:
        """Release whatever the backend holds."""
