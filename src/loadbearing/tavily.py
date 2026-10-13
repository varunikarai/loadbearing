"""Tavily: find and read the upstream docs that say what a pipeline is supposed to read.

`search` finds pages for a query; `extract` reads pages whose URLs are already
known. Both return Tavily's JSON unchanged.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from loadbearing.net import fetch_json

BASE_URL = "https://api.tavily.com/"


def search(
    query: str,
    max_results: int = 5,
    include_raw_content: bool = True,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Results carry `url`, `title`, `content` (a snippet) and, when asked, `raw_content` (the page)."""
    body = {
        "query": query,
        "max_results": max_results,
        "include_answer": True,
        "include_raw_content": include_raw_content,
    }
    return _post("search", body, api_key)


def extract(urls: list[str], api_key: str | None = None) -> dict[str, Any]:
    """Results carry `url` and `raw_content`; pages that could not be read are in `failed_results`."""
    return _post("extract", {"urls": list(urls)}, api_key)


def _post(path: str, body: dict, api_key: str | None) -> dict[str, Any]:
    key = api_key or os.environ.get("TAVILY_API_KEY")
    if not key:
        raise RuntimeError("TAVILY_API_KEY is not set (see .env.example)")
    req = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    return fetch_json(req, timeout=60)
