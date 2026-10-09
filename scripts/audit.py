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

# Made-up values that look like keys on purpose. Each is listed with where it
# lives, so a reviewer can check it is still a fake and not a real key.
KNOWN_FAKES = {
    "lb-secret-value-6f1c": "tests/test_secrets.py, the A2 test's stand-in secret",
}


@dataclass(frozen=True, order=True)
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
                if match and not any(fake in line for fake in KNOWN_FAKES):
                    found.add(Finding(kind, f"{path} ({sha[:7]})", match.group(0)[:24] + "..."))
    return sorted(found, key=lambda f: (f.where, f.kind))


SECRET_FILES = re.compile(r"(?:^|/)(?:\.env(?:\.[^/]+)?|\.envrc|[^/]+\.pem|id_(?:rsa|dsa|ecdsa|ed25519)|\.netrc)$")
SAFE_FILES = {".env.example"}


def every_path(repo: Path = ROOT) -> set[str]:
    """Every path any commit on any ref has added or changed, including deleted ones."""
    out = git("log", "--all", "--name-only", "--format=", repo=repo).decode()
    return {line for line in out.splitlines() if line}


def scan_paths(paths: set[str]) -> list[Finding]:
    return sorted(
        Finding("secrets file committed", path, Path(path).name)
        for path in paths
        if SECRET_FILES.search(path) and Path(path).name not in SAFE_FILES
    )


EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
EXAMPLE_DOMAINS = {"example.com", "example.org", "example.net"}


def identities(repo: Path = ROOT) -> dict[str, int]:
    """Every author and committer on any ref, with how many commits carry it."""
    out = git("log", "--all", "--format=%an <%ae>%x00%cn <%ce>", repo=repo).decode()
    counts: dict[str, int] = {}
    for line in out.splitlines():
        for who in set(line.split("\0")):  # once per commit, even when author and committer match
            counts[who] = counts.get(who, 0) + 1
    return counts


def scan_emails(versions: dict[str, str], contents: dict[str, str], ours: set[str]) -> list[Finding]:
    """Addresses in any file version that are neither a commit identity nor an example domain."""
    found = set()
    for sha, path in versions.items():
        for address in EMAIL.findall(contents[sha]):
            domain = address.rsplit("@", 1)[1].lower()
            if address.lower() not in ours and domain not in EXAMPLE_DOMAINS:
                found.add(Finding("email address", f"{path} ({sha[:7]})", address))
    return sorted(found)


# Git trailers such as "Signed-off-by:" add a name the commit's author did not
# choose to publish. The rule here is that each person commits only as themselves.
TRAILER = re.compile(r"^[A-Z][A-Za-z]*(?:-[A-Za-z]+)*-by:\s", re.M)


def messages(repo: Path = ROOT) -> dict[str, str]:
    """Every commit message on any ref, keyed by commit."""
    out = git("log", "--all", "--format=%H%x00%B%x01", repo=repo).decode("utf-8", errors="replace")
    return dict(
        entry.strip("\n").split("\0", 1) for entry in out.split("\x01") if entry.strip()
    )


def scan_messages(by_commit: dict[str, str]) -> list[Finding]:
    found = set()
    for sha, text in by_commit.items():
        for line in text.splitlines():
            if TRAILER.match(line):
                found.add(Finding("trailer in a commit message", f"commit {sha[:7]}", line.strip()))
            for kind, shape in KEY_SHAPES.items():
                match = shape.search(line)
                if match:
                    found.add(Finding(kind, f"commit {sha[:7]} message", match.group(0)[:24] + "..."))
    return sorted(found)


def audit(repo: Path = ROOT) -> tuple[list[Finding], dict[str, int]]:
    versions = file_versions(repo)
    contents = read_blobs(list(versions), repo)
    ours = {who.rsplit("<", 1)[1].rstrip(">").lower() for who in identities(repo)}
    findings = (
        scan_keys(versions, contents)
        + scan_paths(every_path(repo))
        + scan_emails(versions, contents, ours)
        + scan_messages(messages(repo))
    )
    commits = len(git("rev-list", "--all", repo=repo).decode().split())
    return findings, {"commits": commits, "file versions": len(versions)}


def main() -> int:
    findings, counts = audit()
    # Not findings: the names and addresses that go public with every commit.
    # Each should be one of the builders, as they meant to appear.
    for who, n in sorted(identities().items()):
        print(f"identity, check it is meant to be public: {who} on {n} commits")
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
