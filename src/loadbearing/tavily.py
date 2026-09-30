"""Tavily search: fetch the upstream spec or docs that say what a pipeline is supposed to read."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

SEARCH_URL = "https://api.tavily.com/search"


def search(query: str, max_results: int = 5, api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not set (see .env.example)")
    req = urllib.request.Request(
        SEARCH_URL,
        data=json.dumps(
            {"query": query, "max_results": max_results, "include_answer": True}
        ).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)
