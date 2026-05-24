#!/usr/bin/env python3
"""Guardrails for agent ergonomics: slim INDEX/SKILL and quick companions for large refs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SKILL = ROOT / "SKILL.md"
INDEX = ROOT / "references" / "INDEX.md"
REFERENCES = ROOT / "references"

MAX_SKILL_LINES = 150
MAX_INDEX_LINES = 80
MIN_LINES_FOR_QUICK = 1500

INDEX_FORBIDDEN_SECTION = "## Sections by file"


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    errors: list[str] = []

    if not SKILL.is_file():
        errors.append(f"Missing {SKILL.relative_to(ROOT)}")
    else:
        n = line_count(SKILL)
        if n > MAX_SKILL_LINES:
            errors.append(
                f"SKILL.md has {n} lines (max {MAX_SKILL_LINES}); "
                "move routing detail to references/workflows.md or INDEX.md"
            )

    if not INDEX.is_file():
        errors.append(f"Missing {INDEX.relative_to(ROOT)}")
    else:
        text = INDEX.read_text(encoding="utf-8")
        n = line_count(INDEX)
        if n > MAX_INDEX_LINES:
            errors.append(
                f"references/INDEX.md has {n} lines (max {MAX_INDEX_LINES}); "
                "move section anchors to references/INDEX-sections.md"
            )
        if INDEX_FORBIDDEN_SECTION in text:
            errors.append(
                "references/INDEX.md must not contain "
                f'"{INDEX_FORBIDDEN_SECTION}" (use INDEX-sections.md)'
            )

    for md in sorted(REFERENCES.glob("*.md")):
        name = md.name
        if name in ("INDEX.md", "INDEX-sections.md") or name.endswith("-quick.md"):
            continue
        lines = line_count(md)
        if lines >= MIN_LINES_FOR_QUICK:
            quick = REFERENCES / f"{md.stem}-quick.md"
            if not quick.is_file():
                errors.append(
                    f"{md.relative_to(ROOT)} has {lines} lines but "
                    f"missing {quick.relative_to(ROOT)}"
                )

    if errors:
        print("Ergonomics check failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"OK: SKILL.md<={MAX_SKILL_LINES}, INDEX.md<={MAX_INDEX_LINES}, "
        f"all references>={MIN_LINES_FOR_QUICK} lines have -quick.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
