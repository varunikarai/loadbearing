"""V6: scan every version of every file before the repository goes public.

    python3 scripts/audit.py

Reads the whole history on every branch, not only the current files: a key
deleted in a later commit is still public once the repository is. Prints each
finding with the file it is in, ends with "go" or "no-go", and exits 1 on
no-go. Needs only git and the standard library.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Shapes of real credentials. Short placeholders such as "tvly-test" in the
# tests do not match: every shape needs the length a real key has.
KEY_SHAPES = {
    "JWT-shaped token": re.compile(r"eyJ[A-Za-z0-9_-]{20,}"),
    "Tavily key": re.compile(r"tvly-[A-Za-z0-9-]{16,}"),
    "NVIDIA key": re.compile(r"nvapi-[A-Za-z0-9_-]{20,}"),
    "sk- key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "key assigned a value": re.compile(
        r"(?i)\b[A-Z_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)\s*[:=]\s*['\"]?[A-Za-z0-9_.\-]{20,}"
    ),
}


@dataclass(frozen=True)
class Finding:
    kind: str
    where: str
    text: str


def git(*args: str, repo: Path = ROOT, stdin: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=repo, input=stdin, capture_output=True, check=True
    ).stdout


def file_versions(repo: Path = ROOT) -> dict[str, str]:
    """Every blob reachable from any ref, mapped to a path it was committed at."""
    paths: dict[str, str] = {}
    for line in git("rev-list", "--all", "--objects", repo=repo).decode().splitlines():
        sha, _, path = line.partition(" ")
        if path:
            paths.setdefault(sha, path)
    if not paths:
        return {}
    kinds = git("cat-file", "--batch-check", repo=repo, stdin="\n".join(paths).encode() + b"\n")
    return {
        sha: paths[sha]
        for sha, kind, _ in (row.split() for row in kinds.decode().splitlines())
        if kind == "blob"
    }


def read_blobs(shas: list[str], repo: Path = ROOT) -> dict[str, str]:
    """The contents of each blob, decoded leniently, read in one git call."""
    if not shas:
        return {}
    out = git("cat-file", "--batch", repo=repo, stdin="\n".join(shas).encode() + b"\n")
    contents, pos = {}, 0
    while pos < len(out):
        header_end = out.index(b"\n", pos)
        sha, _, size = out[pos:header_end].decode().split()
        start = header_end + 1
        contents[sha] = out[start:start + int(size)].decode("utf-8", errors="replace")
        pos = start + int(size) + 1  # each object is followed by a newline
    return contents


def scan_keys(versions: dict[str, str], contents: dict[str, str]) -> list[Finding]:
    found = set()
    for sha, path in versions.items():
        for line in contents[sha].splitlines():
            for kind, shape in KEY_SHAPES.items():
                match = shape.search(line)
                if match:
                    found.add(Finding(kind, f"{path} ({sha[:7]})", match.group(0)[:24] + "..."))
    return sorted(found, key=lambda f: (f.where, f.kind))


def audit(repo: Path = ROOT) -> tuple[list[Finding], dict[str, int]]:
    versions = file_versions(repo)
    contents = read_blobs(list(versions), repo)
    findings = scan_keys(versions, contents)
    commits = len(git("rev-list", "--all", repo=repo).decode().split())
    return findings, {"commits": commits, "file versions": len(versions)}


def main() -> int:
    findings, counts = audit()
    for f in findings:
        print(f"{f.kind}: {f.where}: {f.text}")
    scanned = ", ".join(f"{n} {what}" for what, n in counts.items())
    if findings:
        print(f"no-go: {len(findings)} finding(s) in {scanned}")
        return 1
    print(f"go: nothing found in {scanned}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
