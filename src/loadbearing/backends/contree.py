"""Nebius Token Factory Sandboxes backend, via contree-sdk.

Checkpoint: the image left behind by the setup run with disposable=False, which
snapshots the whole filesystem. Fork: a disposable run from that image with one
mutated input file dropped in. Every fork starts from the same snapshot.

Credentials come from the profile that `contree auth` saves.
Written against the documented SDK API; not yet run against a live account.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from loadbearing.backends.base import INPUT_NAME, RunResult
from loadbearing.target import Target


class ContreeBackend:
    name = "sandbox"

    def __init__(self) -> None:
        try:
            from contree_client.httpx import ContreeSyncClient
            from contree_sdk import ContreeSync
        except ImportError as exc:
            raise RuntimeError(
                "the sandbox backend needs the sandbox extra: pip install -e '.[sandbox]'"
            ) from exc
        self._client = ContreeSyncClient.from_profile()
        self._sdk = ContreeSync(self._client)

    def checkpoint(self, target: Target) -> Any:
        image = self._sdk.images.use(target.image)
        if target.files:
            image = image.apply_files({rel: str(target.root / rel) for rel in target.files})
        result = image.run(shell=f"cd / && {target.setup or 'true'}", disposable=False).wait()
        if result.exit_code != 0:
            raise RuntimeError(f"setup failed in the sandbox:\n{_text(result.stderr)}")
        return result

    def run(self, checkpoint: Any, target: Target, record: dict) -> RunResult:
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as fh:
                json.dump(record, fh)
            result = checkpoint.run(
                shell=f"cd / && {target.command}", files={INPUT_NAME: path}
            ).wait()
        finally:
            os.unlink(path)
        return RunResult(_text(result.stdout), _text(result.stderr), result.exit_code)

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()


def _text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return value or ""
