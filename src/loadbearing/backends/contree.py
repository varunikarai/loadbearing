"""Nebius Token Factory Sandboxes backend, via contree-sdk.

Checkpoint: the image left behind by the setup run with disposable=False, which
snapshots the whole filesystem. Fork: a disposable run from that image with one
mutated input file dropped in. Every fork starts from the same snapshot.

Credentials, either way works: `contree auth` (from `uv tool install contree-cli`)
saves a profile the SDK reads, or NEBIUS_API_KEY and NEBIUS_PROJECT_ID in the
environment, which `loadbearing` fills from .env. The SDK talks to the Token
Factory Sandboxes endpoint by default.

Checked against contree-sdk 0.3.6 by reading its source; not yet run against a
live account.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loadbearing.backends.base import INPUT_NAME, RunResult, forwarded_env
from loadbearing.target import Target

# Everything the pipeline needs lives here inside the sandbox. Paths handed to
# the SDK are absolute, so nothing depends on the image's default directory.
WORKDIR = "/work"


class ContreeBackend:
    name = "sandbox"

    def __init__(self) -> None:
        try:
            from contree_sdk import ContreeSync
        except ImportError as exc:
            raise RuntimeError(
                "the sandbox backend needs the sandbox extra: pip install -e '.[sandbox]'"
            ) from exc
        self._sdk = ContreeSync()

    def checkpoint(self, target: Target) -> Any:
        forwarded_env(target)  # a missing variable fails here, before any paid run
        # oci() finds the tag on the account or imports it from its registry; use() would only
        # name it, and the first run would fail on an account that never pulled the image.
        image = self._sdk.images.oci(target.image)
        if target.files:
            image = image.apply_files(
                {f"{WORKDIR}/{rel}": (target.root / rel).read_bytes() for rel in target.files}
            )
        result = image.run(
            shell=target.setup or "true", cwd=WORKDIR, disposable=False
        ).wait()
        if result.exit_code != 0:
            raise RuntimeError(f"setup failed in the sandbox:\n{_text(result.stderr)}")
        return result

    def run(self, checkpoint: Any, target: Target, record: dict) -> RunResult:
        result = checkpoint.run(
            shell=target.command,
            cwd=WORKDIR,
            # Only the variables the target names, and only on this disposable
            # fork. The setup run that made the checkpoint never had them.
            env=forwarded_env(target),
            files={f"{WORKDIR}/{INPUT_NAME}": json.dumps(record).encode()},
            timeout=target.timeout,
        ).wait()
        return RunResult(_text(result.stdout), _text(result.stderr), result.exit_code)

    def apply(self, checkpoint: Any, files: dict[str, str]) -> Any:
        """A new image derived from the checkpoint with `files` written. The original is untouched."""
        for rel in files:
            if rel.startswith("/") or ".." in Path(rel).parts:
                raise ValueError(f"{rel!r} is outside the checkpoint")
        return checkpoint.apply_files(
            {f"{WORKDIR}/{rel}": content.encode() for rel, content in files.items()}
        )

    def close(self) -> None:
        pass  # the SDK holds no session open between operations


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""
