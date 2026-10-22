"""Local fallback backend: a checkpoint is a prepared directory, a fork is a copy of it.

This only snapshots the working directory, not the whole filesystem, so a setup
step that installs system packages is not captured. The sandbox backend is the
one that holds everything byte-identical; this one exists so the engine can be
developed and tested with no account and no network.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from loadbearing.backends.base import INPUT_NAME, RunResult, forwarded_env, scrubbed_env
from loadbearing.target import Target

TIMED_OUT = 124  # the exit code coreutils' `timeout` uses, so a hung run reads as one


class LocalBackend:
    name = "local"

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="loadbearing-")

    def checkpoint(self, target: Target) -> Path:
        if target.needs_sandbox:
            raise RuntimeError(
                f"{target.name} installs packages in its setup, so it runs in a sandbox only: "
                "use --backend sandbox"
            )
        forwarded_env(target)  # a missing variable fails here, before any run
        ckpt = Path(tempfile.mkdtemp(prefix="checkpoint-", dir=self._tmp.name))
        for rel in target.files:
            dest = ckpt / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target.root / rel, dest)
        if target.setup:
            subprocess.run(
                target.setup,
                shell=True,
                cwd=ckpt,
                check=True,
                capture_output=True,
                env=scrubbed_env(target),  # setup output is frozen into the checkpoint
            )
        return ckpt

    def run(self, checkpoint: Path, target: Target, record: dict) -> RunResult:
        work = Path(tempfile.mkdtemp(prefix="fork-", dir=self._tmp.name))
        shutil.copytree(checkpoint, work, dirs_exist_ok=True)
        (work / INPUT_NAME).write_text(json.dumps(record))
        try:
            proc = subprocess.run(
                target.command,
                env={**scrubbed_env(target), **forwarded_env(target)},
                shell=True,
                cwd=work,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # a pipeline that prints invalid bytes still gets compared
                timeout=target.timeout,
            )
        except subprocess.TimeoutExpired as exc:
            # A fork that hangs reacted to its mutation; it must not take the whole probe down.
            out, err = (_text(s) for s in (exc.stdout, exc.stderr))
            return RunResult(out, f"{err}\ntimed out after {target.timeout:g}s", TIMED_OUT)
        return RunResult(proc.stdout, proc.stderr, proc.returncode)

    def apply(self, checkpoint: Path, files: dict[str, str]) -> Path:
        """A copy of the checkpoint with `files` written into it. The original is untouched."""
        derived = Path(tempfile.mkdtemp(prefix="checkpoint-", dir=self._tmp.name))
        shutil.copytree(checkpoint, derived, dirs_exist_ok=True)
        for rel, content in files.items():
            dest = (derived / rel).resolve()
            if not dest.is_relative_to(derived.resolve()):
                raise ValueError(f"{rel!r} is outside the checkpoint")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        return derived

    def close(self) -> None:
        self._tmp.cleanup()


def _text(value: bytes | str | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""
