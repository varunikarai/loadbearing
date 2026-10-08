"""Run the README quickstart exactly as written, and check it prints what the README shows.

Used by the clean-clone CI job inside a fresh clone. The first bash block under
"## Quickstart" is run line by line, except the clone itself, which CI has just
done. The text block after it is the promised output; it must match the real
output exactly, apart from the timing line, whose numbers change every run.
A probe exits 1 when it finds defects, and the quickstart's example has two,
so exit codes 0 and 1 both count as success.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TIMING = re.compile(r"^checkpoint [\d.]+s, then \d+ runs in [\d.]+s wall .*$", re.M)


def quickstart(readme: str) -> tuple[list[str], str]:
    section = readme.split("## Quickstart", 1)[1]
    blocks = re.findall(r"```(\w*)\n(.*?)```", section, re.S)
    commands = next(body for lang, body in blocks if lang == "bash")
    shown = next(body for lang, body in blocks if lang == "")
    lines = [
        line for line in commands.splitlines()
        if line.strip() and not line.startswith(("git clone", "cd loadbearing"))
    ]
    return lines, shown


def main() -> int:
    lines, shown = quickstart(Path("README.md").read_text())
    output = ""
    for line in lines:
        print(f"$ {line}", flush=True)
        proc = subprocess.run(line, shell=True, capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode not in (0, 1):
            print(f"README command failed with exit code {proc.returncode}: {line}")
            return 1
        output += proc.stdout
    expected, actual = TIMING.sub("<timing>", shown).strip(), TIMING.sub("<timing>", output).strip()
    if expected != actual:
        print("The README shows output the quickstart no longer prints.\n--- README\n"
              f"{expected}\n--- actual\n{actual}")
        return 1
    print("README quickstart: commands ran, output matches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
