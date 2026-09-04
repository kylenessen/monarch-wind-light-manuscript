#!/usr/bin/env python3
"""Create paste-ready plain-text responses for the MDPI revision portal."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWERS = ROOT / "reviewers"
OUTPUT = REVIEWERS / "portal"
MANUSCRIPT_TITLE = (
    "Does Wind Disrupt Overwintering Monarch Butterfly Clusters? "
    "An Observational Study of Western Monarchs"
)


def parse_bracket_group(source: str, start: int) -> tuple[str, int]:
    if source[start] != "[":
        raise ValueError(f"Expected '[' at offset {start}")
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        character = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return source[start + 1 : index], index + 1
    raise ValueError("Unclosed bracket group")


def clean_typst(value: str) -> str:
    value = re.sub(
        r'#link\("([^"]+)"\)\[([^]]+)\]',
        lambda match: f"{match.group(2)} ({match.group(1)})",
        value,
    )
    value = value.replace("\\\n", " ")
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", value.strip()):
        paragraphs.append(re.sub(r"\s+", " ", paragraph).strip())
    return "\n\n".join(paragraphs)


def parse_entries(source: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    position = 0
    while True:
        marker = source.find("#entry(", position)
        if marker < 0:
            break
        cursor = marker + len("#entry(")
        groups: list[str] = []
        for _ in range(3):
            while cursor < len(source) and source[cursor] in " \t\r\n,":
                cursor += 1
            group, cursor = parse_bracket_group(source, cursor)
            groups.append(clean_typst(group))
        entries.append((groups[0], groups[1], groups[2]))
        position = cursor
    if len(entries) != 35:
        raise RuntimeError(f"Expected 35 response entries, found {len(entries)}")
    return entries


def without_heading(source: str) -> str:
    return re.sub(r"^# .*?\n+", "", source.strip(), count=1)


def split_numbered(source: str) -> list[str]:
    blocks = re.split(r"\n(?=\d+\. )", source.strip())
    return [re.sub(r"^\d+\.\s*", "", block.strip()) for block in blocks if block.strip()]


def academic_editor_comments() -> list[str]:
    source = without_heading((REVIEWERS / "academic-editor.md").read_text(encoding="utf-8"))
    first, *bullets = source.split("\n- ")
    comments = [first.strip(), *(bullet.strip() for bullet in bullets)]
    if len(comments) != 3:
        raise RuntimeError(f"Expected 3 Academic Editor comments, found {len(comments)}")
    return comments


def reviewer_one_comments() -> list[str]:
    source = without_heading((REVIEWERS / "reviewer-1.md").read_text(encoding="utf-8"))
    general, remainder = source.split("\nSpecific Comments\n", maxsplit=1)
    specific, minor = remainder.split("\nMinor Comments\n", maxsplit=1)
    comments = [general.removeprefix("General Comments\n").strip()]
    comments.extend(split_numbered(specific))
    comments.extend(split_numbered(minor))
    if len(comments) != 16:
        raise RuntimeError(f"Expected 16 Reviewer 1 comments, found {len(comments)}")
    return comments


def reviewer_two_comments() -> tuple[str, list[str]]:
    source = without_heading((REVIEWERS / "reviewer-2.md").read_text(encoding="utf-8"))
    preface, numbered = source.split("\n1. ", maxsplit=1)
    comments = split_numbered("1. " + numbered)
    if len(comments) != 4:
        raise RuntimeError(f"Expected 4 Reviewer 2 comments, found {len(comments)}")
    return preface.strip(), comments


def format_response(
    recipient: str,
    comments: list[str],
    entries: list[tuple[str, str, str]],
    reviewer_preface: str | None = None,
    preserve_entry_labels: bool = False,
) -> str:
    if len(comments) != len(entries):
        raise RuntimeError(
            f"Comment and response counts differ for {recipient}: "
            f"{len(comments)} comments and {len(entries)} responses"
        )

    lines = [
        f"AUTHOR'S REPLY TO {recipient.upper()}",
        "",
        f"Revised manuscript title: {MANUSCRIPT_TITLE}",
        "",
        "Thank you for the careful and constructive review. We have addressed each comment below. "
        "The complete marked manuscript is included with the resubmission.",
    ]
    if reviewer_preface:
        lines.extend(
            [
                "",
                "Reviewer's opening assessment",
                reviewer_preface,
                "",
                "Response",
                "We thank the reviewer for this positive assessment and for the constructive comments that follow.",
            ]
        )

    for number, (comment, entry) in enumerate(zip(comments, entries, strict=True), start=1):
        title, _, answer = entry
        comment_heading = f"Comment {number}. {title}"
        response_heading = f"Response {number}"
        if preserve_entry_labels:
            if title.casefold() == "general comments":
                comment_heading = "General comments"
                response_heading = "Response to general comments"
            elif match := re.match(r"Comment (\d+)\.", title):
                comment_heading = title
                response_heading = f"Response {match.group(1)}"
            elif match := re.match(r"Minor comment (\d+)\.", title):
                comment_heading = title
                response_heading = f"Response to minor comment {match.group(1)}"
        lines.extend(
            [
                "",
                comment_heading,
                comment,
                "",
                response_heading,
                answer,
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    entries = parse_entries((REVIEWERS / "response-letter.typ").read_text(encoding="utf-8"))
    editor_entries = entries[:3]
    reviewer_one_entries = entries[3:19]
    reviewer_two_entries = entries[19:23]

    reviewer_two_preface, reviewer_two = reviewer_two_comments()
    files = {
        "academic-editor.txt": format_response(
            "the Academic Editor", academic_editor_comments(), editor_entries
        ),
        "reviewer-1.txt": format_response(
            "Reviewer 1",
            reviewer_one_comments(),
            reviewer_one_entries,
            preserve_entry_labels=True,
        ),
        "reviewer-2.txt": format_response(
            "Reviewer 2",
            reviewer_two,
            reviewer_two_entries,
            reviewer_preface=reviewer_two_preface,
            preserve_entry_labels=True,
        ),
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (OUTPUT / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
