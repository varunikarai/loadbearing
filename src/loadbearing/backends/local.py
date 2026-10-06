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


class LocalBackend:
    name = "local"

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="loadbearing-")

    def checkpoint(self, target: Target) -> Path:
        forwarded_env(target)  # a missing variable fails here, before any run
        ckpt = Path(self._tmp.name) / "checkpoint"
        ckpt.mkdir()
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
        proc = subprocess.run(
            target.command,
            env={**scrubbed_env(target), **forwarded_env(target)},
            shell=True,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=target.timeout,
        )
        return RunResult(proc.stdout, proc.stderr, proc.returncode)

    def close(self) -> None:
        self._tmp.cleanup()
