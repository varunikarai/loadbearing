"""The hosted demo: list targets, run a probe on one, serve the report.

Every run is cached as JSON and re-rendered on request, so a page view never
costs a run. With --readonly nothing new can be run at all, which is how the
public demo keeps paid Sandboxes credits alive through judging. One probe
runs at a time; a second request waits for the first instead of doubling the
bill.
"""

from __future__ import annotations

import json
import threading
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional

from loadbearing import report as report_json
from loadbearing.backends import make_backend
from loadbearing.html_report import CSS, render_html
from loadbearing.probe import probe
from loadbearing.target import load_target


class Demo:
    def __init__(
        self,
        targets_dir: str | Path,
        cache_dir: str | Path,
        backend: str = "local",
        readonly: bool = False,
        classify_factory: Optional[Callable] = None,
    ) -> None:
        # Only targets found here can be named in a URL, so a path never comes from a request.
        self.targets = {
            p.parent.name: p for p in sorted(Path(targets_dir).glob("*/target.json"))
        }
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.backend = backend
        self.readonly = readonly
        self.classify_factory = classify_factory
        self._lock = threading.Lock()

    def cached(self, name: str) -> Optional[dict]:
        path = self._cache_path(name)
        if not path.is_file():
            return None
        try:
            return report_json.load(path)
        except RuntimeError:
            return None  # an old schema is treated as never run

    def run(self, name: str) -> dict:
        with self._lock:
            target = load_target(self.targets[name])
            classify = self.classify_factory() if self.classify_factory else None
            backend = make_backend(self.backend)
            try:
                result = probe(target, backend, classify=classify)
            finally:
                backend.close()
            return report_json.save(result, self._cache_path(name))

    def _cache_path(self, name: str) -> Path:
        return self.cache / f"{name}.{self.backend}.json"


def make_handler(demo: Demo) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "loadbearing"

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0].rstrip("/") or "/"
            if path == "/":
                return self._send(HTTPStatus.OK, _index(demo))
            if path == "/healthz":
                return self._send(HTTPStatus.OK, "ok", "text/plain")
            name, kind = _route(path)
            if name not in demo.targets:
                return self._send(HTTPStatus.NOT_FOUND, _page("Not found", "<p>No such target.</p>"))
            data = demo.cached(name)
            if kind == "json":
                if data is None:
                    return self._send(HTTPStatus.NOT_FOUND, '{"error": "not run yet"}', "application/json")
                return self._send(HTTPStatus.OK, json.dumps(data, indent=2), "application/json")
            if data is None:
                return self._send(HTTPStatus.OK, _not_run(name, demo.readonly))
            return self._send(HTTPStatus.OK, render_html(data))

        def do_POST(self) -> None:
            name, kind = _route(self.path.rstrip("/"))
            if kind != "run" or name not in demo.targets:
                return self._send(HTTPStatus.NOT_FOUND, _page("Not found", "<p>No such target.</p>"))
            if demo.readonly:
                return self._send(
                    HTTPStatus.FORBIDDEN,
                    _page("Read only", "<p>This demo serves recorded runs only.</p>"),
                )
            try:
                demo.run(name)
            except Exception as exc:  # the visitor sees why, the server keeps serving
                return self._send(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    _page("The probe failed", f"<pre>{escape(str(exc))}</pre>"),
                )
            self.send_response(HTTPStatus.SEE_OTHER)
            self.send_header("Location", f"/t/{name}")
            self.end_headers()

        def _send(self, status: int, body: str, kind: str = "text/html; charset=utf-8") -> None:
            raw = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, fmt: str, *args) -> None:
            pass  # quiet by default; a hosting platform logs requests anyway

    return Handler


def serve(demo: Demo, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(demo))


def _route(path: str) -> tuple[str, str]:
    """/t/<name> -> (name, page) · /t/<name>.json -> (name, json) · /t/<name>/run -> (name, run)."""
    if not path.startswith("/t/"):
        return "", ""
    rest = path[3:]
    if rest.endswith("/run"):
        return rest[:-4], "run"
    if rest.endswith(".json"):
        return rest[:-5], "json"
    return rest, "page"


def _index(demo: Demo) -> str:
    rows = []
    for name in demo.targets:
        data = demo.cached(name)
        if data is None:
            status = '<span class="badge plain">not run yet</span>'
        elif data["defects"]:
            n = len(data["defects"])
            status = f'<span class="badge silent">{n} defect{"s" if n != 1 else ""}</span>'
        else:
            status = '<span class="badge plain">clean</span>'
        rows.append(
            f'<tr><td class="f"><a href="/t/{escape(name)}">{escape(name)}</a></td>'
            f"<td>{status}</td><td>{_run_button(name, demo.readonly)}</td></tr>"
        )
    body = (
        '<p class="lede">Pick a pipeline. Loadbearing checkpoints it once, forks it once per '
        "mutated input, runs every fork in parallel, and tells you which inputs it really reads.</p>"
        f'<div class="panel"><table><tbody>{"".join(rows)}</tbody></table></div>'
    )
    return _page("Loadbearing", body)


def _not_run(name: str, readonly: bool) -> str:
    body = f'<p class="lede">No recorded run yet.</p>{_run_button(name, readonly)}'
    return _page(name, body)


def _run_button(name: str, readonly: bool) -> str:
    if readonly:
        return ""
    return (
        f'<form method="post" action="/t/{escape(name)}/run" style="margin:0">'
        '<button class="badge silent" style="border:0;cursor:pointer;font:inherit;'
        'font-weight:900;padding:8px 16px">Run probe</button></form>'
    )


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title><style>{CSS}a{{color:inherit}}</style></head><body><main>"
        '<div class="brand"><a href="/"><b>Loadbearing</b></a> · checkpoint once, fork per mutation</div>'
        f"<h1>{escape(title)}</h1>{body}</main></body></html>"
    )
