#!/usr/bin/env python3
"""Fail on voice violations in SKILL.md and references/.

Directive-first prose for agent skill docs: no tutorial framing, meta references
to "this guide/skill", emoji good/bad markers, or legacy // Bad:/// Good: comments.

Scans SKILL.md and references/*.md. README.md is excluded (GitHub-facing).
Extend LINE_PATTERNS and PROSE_PATTERNS below when adding new bans.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Every line (including inside fenced samples — comment conventions only).
LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"//\s*Bad\b", re.I), "use // WRONG: in sample comments"),
    (re.compile(r"//\s*Good\b", re.I), "use // CORRECT: in sample comments"),
    (re.compile(r"//\s*✅|//\s*❌"), "emoji in // comments"),
    (re.compile(r"//\s*Copy this into", re.I), "tutorial // Copy this into"),
]

# Markdown prose only (outside ``` fences).
PROSE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"❌|✅|🔴|🟡|🟢"), "emoji good/bad or severity markers"),
    (re.compile(r"\*\*Bad:\*\*|\*\*Good:\*\*", re.I), "use **Wrong:** / **Correct:**"),
    (re.compile(r">\s*\*\*Warning:\*\*", re.I), "blockquote **Warning:** (use **Required:** / **Forbidden:**)"),
    (re.compile(r"\(Recommended\)", re.I), "(Recommended) label"),
    (re.compile(r"\*\*Preferred:\*\*|\*\*Alternative:\*\*", re.I), "**Preferred:** / **Alternative:** framing"),
    (re.compile(r"\bthis guide\b", re.I), "meta: this guide"),
    (re.compile(r"\bthis skill\b|\bthis skillset\b", re.I), "meta: this skill / skillset"),
    (re.compile(r"\bthis codebase\b", re.I), "meta: this codebase"),
    (re.compile(r"\bthe modern\b", re.I), "the modern (delete adjective)"),
    (re.compile(r"\*\*P0\s*—|\*\*P1\s*—|\*\*P2\s*—|\*\*Blocker:\*\*", re.I), "P0/P1/P2/Blocker label in prose"),
    (re.compile(r"Related Guides|When to Use This Guide", re.I), "meta section title"),
    (
        re.compile(r"(?:^|[\s(\"'])(?:we|our|us)\b", re.I),
        "first-person plural (we/our/us)",
    ),
    (re.compile(r"^\s*Note:\s", re.I), "Note: label (promote to directive)"),
    (re.compile(r"Step-by-Step", re.I), "Step-by-Step tutorial framing"),
]


def iter_voice_files() -> list[Path]:
    files = [ROOT / "SKILL.md"]
    ref = ROOT / "references"
    if ref.is_dir():
        files.extend(sorted(ref.glob("*.md")))
    return [p for p in files if p.is_file()]


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_fence = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        for pattern, label in LINE_PATTERNS:
            if pattern.search(line):
                errors.append(f"{path.relative_to(ROOT)}:{line_no}: {label}")
        if not in_fence:
            for pattern, label in PROSE_PATTERNS:
                if pattern.search(line):
                    errors.append(f"{path.relative_to(ROOT)}:{line_no}: {label}")
    return errors


def main() -> int:
    files = iter_voice_files()
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(check_file(path))

    if all_errors:
        print("Skill voice check failed:", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        print(
            f"\n{len(all_errors)} violation(s). "
            "Fix the line or add an exception in .github/scripts/check_skill_voice.py.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: voice check passed ({len(files)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
