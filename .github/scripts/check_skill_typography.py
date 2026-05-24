#!/usr/bin/env python3
"""Fail on non-ASCII typography in skill markdown (SKILL.md, references/, convention docs).

Use plain ASCII in prose:
- hyphen-minus `-` for dashes (not en/em dash or Unicode minus)
- ASCII `'` and `"`
- ASCII space (U+0020)
- three periods `...` (not ellipsis character)
- keyboard operators `*`, `/`, `<=`, `>=`, `!=` (not x, division, inequality symbols)
- `-` or `*` for list markers (not bullet glyphs)

Skips content inside fenced code blocks. Extend FORBIDDEN_CHARS when adding rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

SCAN_GLOBS = (
    "SKILL.md",
    "references/**/*.md",
    "assets/convention/*.md",
    "README.md",
)

# (character, short label, ASCII replacement hint)
FORBIDDEN_CHARS: tuple[tuple[str, str, str], ...] = (
    # Dashes (use ASCII hyphen-minus)
    ("\u2010", "HYPHEN", "-"),
    ("\u2011", "NON-BREAKING HYPHEN", "-"),
    ("\u2012", "FIGURE DASH", "-"),
    ("\u2013", "EN DASH", "-"),
    ("\u2014", "EM DASH", "-"),
    ("\u2015", "HORIZONTAL BAR", "-"),
    ("\u2212", "MINUS SIGN", "-"),
    ("\u2053", "SWUNG DASH", "-"),
    ("\u301c", "WAVE DASH", "-"),
    ("\u3030", "WAVY DASH", "-"),
    ("\u2e3a", "TWO-EM DASH", "-"),
    ("\u2e3b", "THREE-EM DASH", "-"),
    ("\u2e40", "DOUBLE HYPHEN", "-"),
    # Apostrophe-like (use ASCII ')
    ("\u2018", "LEFT SINGLE QUOTATION MARK", "'"),
    ("\u2019", "RIGHT SINGLE QUOTATION MARK", "'"),
    ("\u02bb", "MODIFIER LETTER TURNED COMMA", "'"),
    ("\u02bc", "MODIFIER LETTER APOSTROPHE", "'"),
    ("\u00b4", "ACUTE ACCENT", "'"),
    ("\u02ca", "MODIFIER LETTER ACUTE ACCENT", "'"),
    ("\u02cb", "MODIFIER LETTER GRAVE ACCENT", "'"),
    ("\uff07", "FULLWIDTH APOSTROPHE", "'"),
    ("\u2032", "PRIME", "'"),
    ("\u2035", "REVERSED PRIME", "'"),
    # Double quotes (use ASCII ")
    ("\u201c", "LEFT DOUBLE QUOTATION MARK", '"'),
    ("\u201d", "RIGHT DOUBLE QUOTATION MARK", '"'),
    ("\u201e", "DOUBLE LOW-9 QUOTATION MARK", '"'),
    ("\u201f", "DOUBLE HIGH-REVERSED-9 QUOTATION MARK", '"'),
    ("\u2033", "DOUBLE PRIME", '"'),
    ("\u2036", "REVERSED DOUBLE PRIME", '"'),
    ("\u301d", "REVERSED DOUBLE PRIME QUOTATION MARK", '"'),
    ("\u301e", "DOUBLE PRIME QUOTATION MARK", '"'),
    ("\u301f", "LOW DOUBLE PRIME QUOTATION MARK", '"'),
    ("\uff02", "FULLWIDTH QUOTATION MARK", '"'),
    ("\u3003", "DITTO MARK", '"'),
    # Spaces (use ASCII space)
    ("\u00a0", "NO-BREAK SPACE", "space"),
    ("\u2000", "EN QUAD", "space"),
    ("\u2001", "EM QUAD", "space"),
    ("\u2002", "EN SPACE", "space"),
    ("\u2003", "EM SPACE", "space"),
    ("\u2004", "THREE-PER-EM SPACE", "space"),
    ("\u2005", "FOUR-PER-EM SPACE", "space"),
    ("\u2006", "SIX-PER-EM SPACE", "space"),
    ("\u2007", "FIGURE SPACE", "space"),
    ("\u2008", "PUNCTUATION SPACE", "space"),
    ("\u2009", "THIN SPACE", "space"),
    ("\u200a", "HAIR SPACE", "space"),
    ("\u202f", "NARROW NO-BREAK SPACE", "space"),
    ("\u205f", "MEDIUM MATHEMATICAL SPACE", "space"),
    ("\u3000", "IDEOGRAPHIC SPACE", "space"),
    ("\u2145", "DOUBLE-STRUCK ITALIC CAPITAL D", "space"),
    # Ellipsis (use ...)
    ("\u2026", "HORIZONTAL ELLIPSIS", "..."),
    # Mathematical operators
    ("\u00d7", "MULTIPLICATION SIGN", "*"),
    ("\u00f7", "DIVISION SIGN", "/"),
    ("\u2264", "LESS-THAN OR EQUAL", "<="),
    ("\u2265", "GREATER-THAN OR EQUAL", ">="),
    ("\u2260", "NOT EQUAL", "!="),
    # List bullets
    ("\u2022", "BULLET", "- or *"),
    ("\u25e6", "WHITE BULLET", "- or *"),
    ("\u25aa", "BLACK SMALL SQUARE", "- or *"),
    ("\u25fc", "BLACK MEDIUM SQUARE", "- or *"),
)

CHAR_LOOKUP: dict[str, tuple[str, str]] = {
    ch: (name, hint) for ch, name, hint in FORBIDDEN_CHARS
}


def collect_markdown_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(ROOT.glob(pattern))
    return sorted({path for path in files if path.is_file()})


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    in_fence = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for col, char in enumerate(line, 1):
            if char not in CHAR_LOOKUP:
                continue
            name, hint = CHAR_LOOKUP[char]
            code = f"U+{ord(char):04X}"
            errors.append(
                f"{path.relative_to(ROOT)}:{line_no}:{col}: {name} {code} (use {hint})"
            )
    return errors


def main() -> int:
    files = collect_markdown_files()
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(check_file(path))

    if all_errors:
        print("Typography check failed:", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        print(
            f"\n{len(all_errors)} violation(s). "
            "Fix the character or extend .github/scripts/check_skill_typography.py.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: typography check passed ({len(files)} markdown files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
