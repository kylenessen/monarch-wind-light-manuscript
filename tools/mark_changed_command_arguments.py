#!/usr/bin/env python3
"""Add visible LaTeX change markup inside manuscript metadata commands.

Latexdiff treats several MDPI front-matter and back-matter commands as opaque.
It may report a changed command in comments while rendering only the revised
argument. This script diffs the arguments as ordinary document text and inserts
that markup into an already generated and compileable marked manuscript.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


COMMANDS = (
    "Title",
    "simplesumm",
    "abstract",
    "authorcontributions",
    "dataavailability",
    "conflictsofinterest",
    "acknowledgments",
)


def command_span(source: str, command: str) -> tuple[int, int, str]:
    needle = f"\\{command}{{"
    search_from = 0
    while True:
        start = source.find(needle, search_from)
        if start < 0:
            raise ValueError(f"Could not find \\{command} in source")
        line_start = source.rfind("\n", 0, start) + 1
        line_prefix = source[line_start:start]
        percent_is_escaped = False
        comment_found = False
        for character in line_prefix:
            if character == "%" and not percent_is_escaped:
                comment_found = True
                break
            if character == "\\":
                percent_is_escaped = not percent_is_escaped
            else:
                percent_is_escaped = False
        if not comment_found:
            break
        search_from = start + len(needle)

    opening_brace = start + len(needle) - 1
    depth = 0
    escaped = False
    for index in range(opening_brace, len(source)):
        character = source[index]
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                argument = source[opening_brace + 1 : index]
                return start, index + 1, argument
    raise ValueError(f"Unbalanced braces in \\{command}")


def diff_argument(old_argument: str, new_argument: str) -> str:
    prefix = "\\documentclass{article}\n\\begin{document}\n"
    suffix = "\n\\end{document}\n"
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        old_path = directory / "old.tex"
        new_path = directory / "new.tex"
        old_path.write_text(prefix + old_argument + suffix, encoding="utf-8")
        new_path.write_text(prefix + new_argument + suffix, encoding="utf-8")
        result = subprocess.run(
            ["latexdiff", "--type=CFONT", str(old_path), str(new_path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    body_start = result.index("\\begin{document}") + len("\\begin{document}")
    body_end = result.rindex("\\end{document}")
    return result[body_start:body_end].strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("original", type=Path)
    parser.add_argument("revised", type=Path)
    parser.add_argument("marked", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    original = args.original.read_text(encoding="utf-8")
    revised = args.revised.read_text(encoding="utf-8")
    marked = args.marked.read_text(encoding="utf-8")

    for command in COMMANDS:
        _, _, old_argument = command_span(original, command)
        _, _, new_argument = command_span(revised, command)
        if old_argument == new_argument:
            continue
        start, end, _ = command_span(marked, command)
        replacement = f"\\{command}{{{diff_argument(old_argument, new_argument)}}}"
        marked = marked[:start] + replacement + marked[end:]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(marked, encoding="utf-8")


if __name__ == "__main__":
    main()
