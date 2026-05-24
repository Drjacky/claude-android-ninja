#!/usr/bin/env python3
"""Rewrite ](/references/foo.md) to ](foo.md) inside references/*.md."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCES = ROOT / "references"
OLD = "](/references/"
NEW = "]("


def main() -> int:
    changed_files = 0
    replacements = 0
    for path in sorted(REFERENCES.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if OLD not in text:
            continue
        updated = text.replace(OLD, NEW)
        count = text.count(OLD)
        path.write_text(updated, encoding="utf-8")
        changed_files += 1
        replacements += count
        print(f"{path.relative_to(ROOT)}: {count} link(s)")

    if replacements == 0:
        print("No /references/ absolute links found under references/.")
        return 0

    print(f"Normalized {replacements} link(s) in {changed_files} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
