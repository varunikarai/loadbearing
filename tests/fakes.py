"""Offline stand-ins for Token Factory and the Nemotron router, shared by every test.

Nothing here touches the network or needs a key. Each fake records what it was
asked, so a test can check the prompt as well as the answer.
"""

from __future__ import annotations

from typing import Any, Callable, Optional, Union

from loadbearing.nemotron import NemotronRouter

MODELS = {"nano": "fake/nano", "super": "fake/super", "ultra": "fake/ultra"}

Reply = Union[str, Callable[[str, list], str]]


class FakeTokenFactory:
    """Answers chat calls from a script: one reply per model, or a function of (model, messages)."""

    def __init__(self, replies: Optional[dict[str, Reply]] = None, models: Optional[list[str]] = None):
        self.replies = replies or {}
        self.models = models or list(MODELS.values())
        self.calls: list[tuple[str, list]] = []

    def list_models(self) -> list[str]:
        return sorted(self.models)

    def chat(self, model: str, messages: list[dict], max_tokens: int = 1024) -> str:
        self.calls.append((model, messages))
        reply = self.replies.get(model, "")
        return reply(model, messages) if callable(reply) else reply


def router(replies: Optional[dict[str, Reply]] = None) -> tuple[NemotronRouter, FakeTokenFactory]:
    """A real NemotronRouter over a fake client, keyed by tier name ("nano", "super", "ultra")."""
    client = FakeTokenFactory({MODELS[tier]: reply for tier, reply in (replies or {}).items()})
    return NemotronRouter(client, dict(MODELS)), client


class FakeRouter:
    """A router whose every method returns a scripted value, for code that only calls the router."""

    def __init__(self, **answers: Any):
        self.answers = answers
        self.calls: list[tuple[str, tuple]] = []

    def __getattr__(self, name: str) -> Callable[..., Any]:
        if name not in self.answers:
            raise AttributeError(name)

        def method(*args: Any) -> Any:
            self.calls.append((name, args))
            answer = self.answers[name]
            return answer(*args) if callable(answer) else answer

        return method
