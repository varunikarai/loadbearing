"""Backends: where checkpoints live and forks run."""

from __future__ import annotations

from loadbearing.backends.base import Backend


def make_backend(name: str) -> Backend:
    # Imported lazily so the local backend never needs the sandbox SDK installed.
    if name == "local":
        from loadbearing.backends.local import LocalBackend

        return LocalBackend()
    if name == "sandbox":
        from loadbearing.backends.contree import ContreeBackend

        return ContreeBackend()
    raise ValueError(f"unknown backend: {name}")
