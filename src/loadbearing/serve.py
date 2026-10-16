"""The hosted demo: list targets, run a probe on one, serve the report.

Every run is cached as JSON and re-rendered on request, so a page view never
costs a run. With --readonly only free runs are allowed: a target with no keys,
on the local backend, with no model calls. Anything that would spend credits
(Sandboxes, Nemotron) is served as its recorded run instead, so a visitor can
run the free targets themselves and can never spend a credit. One probe runs at
a time; a second request waits for the first instead of doubling the bill.
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
        targets_dir: str | Path | list,
        cache_dir: str | Path,
        backend: str = "local",
        readonly: bool = False,
        classify_factory: Optional[Callable] = None,
    ) -> None:
        # Only targets found here can be named in a URL, so a path never comes from a request.
        dirs = [targets_dir] if isinstance(targets_dir, (str, Path)) else list(targets_dir)
        self.targets: dict[str, Path] = {}
        self.groups: list[tuple[str, list[str]]] = []
        for given in dirs:
            folder = Path(given)
            # A relative path reads well as a heading ("bench/cases"); an absolute one does not.
            label = str(given) if not folder.is_absolute() else folder.name
            names = []
            for p in sorted(folder.glob("*/target.json")):
                name = p.parent.name
                if name in self.targets:
                    raise ValueError(f"two targets are called {name!r}")
                self.targets[name] = p
                names.append(name)
            self.groups.append((label, names))
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)
        self.backend = backend
        self.readonly = readonly
        self.classify_factory = classify_factory
        self._lock = threading.Lock()

    def can_run(self, name: str) -> bool:
        """Read-only still runs what costs nothing: local, no keys, no model calls."""
        if not self.readonly:
            return True
        free = self.backend == "local" and self.classify_factory is None
        return free and not load_target(self.targets[name]).env

    def cached(self, name: str) -> Optional[dict]:
        """This backend's latest run, else a recorded run from another backend."""
        for backend in dict.fromkeys((self.backend, "sandbox", "local")):
            path = self.cache / f"{name}.{backend}.json"
            if path.is_file():
                try:
                    return report_json.load(path)
                except RuntimeError:
                    continue  # an old schema is treated as never run
        return None

    def run(self, name: str) -> dict:
        if not self.can_run(name):
            raise PermissionError(name)
        with self._lock:
            target = load_target(self.targets[name])
            classify = self.classify_factory() if self.classify_factory else None
            backend = make_backend(self.backend)
            try:
                result = probe(target, backend, classify=classify)
            finally:
                backend.close()
            return report_json.save(result, self.cache / f"{name}.{self.backend}.json")


Response = tuple[int, list[tuple[str, str]], bytes]

_HTML = "text/html; charset=utf-8"


def respond(demo: Demo, method: str, path: str, redirect: bool = True) -> Response:
    """One request, as (status, headers, body). The HTTP server and the WSGI app both use it.

    `redirect=False` answers a run with its report instead of a redirect to it: on a
    serverless host the next request may reach an instance that never saw the run."""
    path, _, query = path.partition("?")
    path = path.rstrip("/") or "/"
    if method == "GET":
        if path == "/":
            return _ok(_index(demo))
        if path == "/healthz":
            return _ok("ok", "text/plain")
        name, kind = _route(path)
        if name not in demo.targets:
            return _ok(_page("Not found", "<p>No such target.</p>"), status=HTTPStatus.NOT_FOUND)
        data = demo.cached(name)
        if kind == "json":
            if data is None:
                return _ok('{"error": "not run yet"}', "application/json", HTTPStatus.NOT_FOUND)
            return _ok(json.dumps(data, indent=2), "application/json")
        if data is None:
            return _ok(_not_run(name, not demo.can_run(name)))
        return _ok(_with_back(render_html(data)))
    if method == "POST":
        name, kind = _route(path)
        if kind != "run" or name not in demo.targets:
            return _ok(_page("Not found", "<p>No such target.</p>"), status=HTTPStatus.NOT_FOUND)
        if not demo.can_run(name):
            return _ok(
                _page("Recorded run only", "<p>This target calls paid services (Nebius Sandboxes "
                      "or Nemotron), so this demo shows its recorded run. The free targets can be "
                      "run from the index.</p>"),
                status=HTTPStatus.FORBIDDEN,
            )
        try:
            data = demo.run(name)
        except Exception as exc:  # the visitor sees why, the server keeps serving
            return _ok(_page("The probe failed", f"<pre>{escape(str(exc))}</pre>"),
                       status=HTTPStatus.INTERNAL_SERVER_ERROR)
        if "format=json" in query.split("&"):
            return _ok(json.dumps(data), "application/json")
        if not redirect:
            return _ok(_with_back(render_html(data)))
        return HTTPStatus.SEE_OTHER, [("Location", f"/t/{name}"), ("Content-Length", "0")], b""
    return _ok(_page("Not allowed", "<p>GET or POST only.</p>"), status=HTTPStatus.METHOD_NOT_ALLOWED)


def _with_back(page: str) -> str:
    """A served report links back to the demo; a saved one stays self-contained."""
    back = ('<a href="/" style="display:inline-block;margin:0 0 18px;font-weight:800;font-size:14px;'
            'color:var(--dim);text-decoration:none">← Back to the demo</a>')
    return page.replace("<main>", "<main>" + back, 1)


def _ok(body: str, kind: str = _HTML, status: int = HTTPStatus.OK) -> Response:
    raw = body.encode()
    return int(status), [("Content-Type", kind), ("Content-Length", str(len(raw)))], raw


def make_handler(demo: Demo) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "loadbearing"

        def do_GET(self) -> None:
            self._send(*respond(demo, "GET", self.path))

        def do_POST(self) -> None:
            self._send(*respond(demo, "POST", self.path))

        def _send(self, status: int, headers: list[tuple[str, str]], body: bytes) -> None:
            self.send_response(status)
            for key, value in headers:
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            pass  # quiet by default; a hosting platform logs requests anyway

    return Handler


def wsgi_app(demo: Demo) -> Callable:
    """The demo as a WSGI app, for hosts that run Python as functions rather than a server."""

    def app(environ: dict, start_response: Callable) -> list[bytes]:
        path = environ.get("PATH_INFO") or "/"
        if environ.get("QUERY_STRING"):
            path += "?" + environ["QUERY_STRING"]
        status, headers, body = respond(demo, environ.get("REQUEST_METHOD", "GET"), path, redirect=False)
        start_response(f"{status} {HTTPStatus(status).phrase}", headers)
        return [body]

    return app


class _Server(ThreadingHTTPServer):
    # The default listen backlog is 5; a few visitors at once would see refused connections.
    request_queue_size = 64
    daemon_threads = True


def serve(demo: Demo, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return _Server((host, port), make_handler(demo))


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
    from loadbearing.site import render_index

    return render_index(demo)


def _not_run(name: str, readonly: bool) -> str:
    body = f'<p class="lede">No recorded run yet.</p>{_run_button(name, readonly)}'
    return _page(name, body)


def _run_button(name: str, readonly: bool) -> str:
    if readonly:
        return ""
    return (
        f'<form method="post" action="/t/{escape(name)}/run" style="margin:0">'
        '<button class="btn">Run probe</button></form>'
    )


_INDEX_CSS = (
    "a{color:inherit}.idx{table-layout:fixed}.idx td{vertical-align:middle}.idx td:last-child{text-align:right}"
    ".idx form{display:inline}.tag{margin-left:10px;font-size:12px;font-weight:800;color:var(--dim);"
    "border:1px solid var(--line);border-radius:999px;padding:2px 8px;white-space:nowrap}"
    ".btn{display:inline-block;border:0;cursor:pointer;font:inherit;font-size:14px;font-weight:900;"
    "padding:8px 16px;border-radius:999px;background:var(--moved);color:#0b0b0c;text-decoration:none;white-space:nowrap}"
    ".btn.ghost{background:transparent;color:var(--text);border:1.5px solid var(--line)}"
    ".btn:hover{filter:brightness(1.08)}"
)


def _page(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title><style>{CSS}{_INDEX_CSS}</style></head><body><main>"
        '<div class="brand"><a href="/"><b>Loadbearing</b></a> · checkpoint once, fork per mutation</div>'
        f"<h1>{escape(title)}</h1>{body}</main></body></html>"
    )
