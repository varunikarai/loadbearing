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
        for folder in map(Path, dirs):
            names = []
            for p in sorted(folder.glob("*/target.json")):
                name = p.parent.name
                if name in self.targets:
                    raise ValueError(f"two targets are called {name!r}")
                self.targets[name] = p
                names.append(name)
            self.groups.append((folder.name, names))
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
                return self._send(HTTPStatus.OK, _not_run(name, not demo.can_run(name)))
            return self._send(HTTPStatus.OK, render_html(data))

        def do_POST(self) -> None:
            name, kind = _route(self.path.rstrip("/"))
            if kind != "run" or name not in demo.targets:
                return self._send(HTTPStatus.NOT_FOUND, _page("Not found", "<p>No such target.</p>"))
            if not demo.can_run(name):
                return self._send(
                    HTTPStatus.FORBIDDEN,
                    _page("Recorded run only", "<p>This target calls paid services (Nebius Sandboxes "
                          "or Nemotron), so this demo shows its recorded run. The free targets can be "
                          "run from the index.</p>"),
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
    sections = []
    for label, names in demo.groups:
        rows = []
        for name in names:
            data = demo.cached(name)
            if data is None:
                status = '<span class="badge plain">not run yet</span>'
            elif data["defects"]:
                n = len(data["defects"])
                status = f'<span class="badge silent">{n} defect{"s" if n != 1 else ""}</span>'
            else:
                status = '<span class="badge plain">clean</span>'
            where = f' <span class="badge plain">recorded on {escape(data["backend"])}</span>' if (
                data and data["backend"] != demo.backend) else ""
            button = _run_button(name, not demo.can_run(name))
            rows.append(
                f'<tr><td class="f"><a href="/t/{escape(name)}">{escape(name)}</a></td>'
                f"<td>{status}{where}</td><td>{button}</td></tr>"
            )
        sections.append(f"<h2>{escape(label)} ({len(names)})</h2>"
                        f'<div class="panel"><table><tbody>{"".join(rows)}</tbody></table></div>')
    body = (
        '<p class="lede">Pick a pipeline. Loadbearing checkpoints it once, forks it once per '
        "mutated input, runs every fork in parallel, and tells you which inputs it really reads.</p>"
        + "".join(sections)
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
