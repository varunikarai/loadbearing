"""Hold Ultra to the source it was given: number the lines it reads, check the lines it cites.

A model can quote the right line and still give it the wrong number. Ultra reads every
source with its line numbers, and each `file:line` its explanation cites is checked against
that file: the cited line must be one the explanation quotes. A citation that fails says
what the cited line really is and where the quoted line is, so a reader never has to trust
a number the model made up.
"""

from __future__ import annotations

import re

_CITATION = re.compile(r"([\w./-]+\.\w+):(\d+)")
MIN_QUOTE = 8  # shorter lines ("return x", "}") match too much to place a quote


def numbered(sources: dict[str, str]) -> str:
    """Every source under its path, each line prefixed with its number."""
    blocks = []
    for rel, text in sources.items():
        lines = text.splitlines()
        width = len(str(len(lines)))
        body = "\n".join(f"{i:>{width}}| {line}" for i, line in enumerate(lines, 1))
        blocks.append(f"--- {rel}\n{body}")
    return "\n\n".join(blocks)


def check(text: str, sources: dict[str, str]) -> list[str]:
    """One note per citation that does not hold; an empty list when every one does."""
    quoted = {line.strip() for line in text.splitlines() if line.strip()}
    notes = []
    for path, number in dict.fromkeys(_CITATION.findall(text)):
        rel = _source_for(path, sources)
        if rel is None:
            continue  # not a file Ultra was given (a URL with a port, a library path): nothing to check against
        lines = sources[rel].splitlines()
        n = int(number)
        cited = lines[n - 1].strip() if 1 <= n <= len(lines) else None
        if cited and cited in quoted:
            continue
        if cited is None:
            note = f"{rel}:{n} is past the end of the file, which has {len(lines)} lines"
        elif not cited:
            note = f"{rel}:{n} is a blank line"
        else:
            note = f"{rel}:{n} is `{cited}`, which the explanation does not quote"
        places = [i for i, line in enumerate(lines, 1) if len(line.strip()) >= MIN_QUOTE and line.strip() in quoted]
        if places:
            note += "; the line it quotes from that file is at " + ", ".join(f"{rel}:{i}" for i in places)
        notes.append(note)
    return notes


def _source_for(path: str, sources: dict[str, str]) -> str | None:
    if path in sources:
        return path
    named = [rel for rel in sources if rel.rsplit("/", 1)[-1] == path.rsplit("/", 1)[-1]]
    return named[0] if len(named) == 1 else None
