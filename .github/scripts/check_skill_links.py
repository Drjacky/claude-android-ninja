#!/usr/bin/env python3
"""Verify internal markdown links in the skill package resolve to existing files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LINK_RE = re.compile(r"\]\(([^)]+)\)")
FORBIDDEN_ABS_REF = "](/references/"
SCAN_GLOBS = (
    "SKILL.md",
    "references/**/*.md",
    "assets/convention/*.md",
    "README.md",
)


def is_external(url: str) -> bool:
    lowered = url.lower()
    return lowered.startswith(("http://", "https://", "mailto:", "javascript:"))


def resolve_target(source: Path, target: str) -> Path:
    path_part, _, _ = target.partition("#")
    path_part = path_part.strip()
    if not path_part:
        return source
    if path_part.startswith("/"):
        return (ROOT / path_part.lstrip("/")).resolve()
    return (source.parent / path_part).resolve()


def collect_markdown_files() -> list[Path]:
    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(ROOT.glob(pattern))
    return sorted({path for path in files if path.is_file()})


def check_file(md_path: Path) -> list[str]:
    errors: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    if md_path.parent == ROOT / "references" and FORBIDDEN_ABS_REF in text:
        errors.append(
            f"{md_path.relative_to(ROOT)}: use relative links (foo.md), not {FORBIDDEN_ABS_REF}..."
        )
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or is_external(target):
            continue
        resolved = resolve_target(md_path, target)
        if not resolved.exists():
            rel_source = md_path.relative_to(ROOT)
            errors.append(f"{rel_source}: broken link -> {target}")
    return errors


def main() -> int:
    all_errors: list[str] = []
    for md_path in collect_markdown_files():
        all_errors.extend(check_file(md_path))

    if all_errors:
        print("Broken internal markdown links:", file=sys.stderr)
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        print(f"\n{len(all_errors)} broken link(s).", file=sys.stderr)
        return 1

    scanned = len(collect_markdown_files())
    print(f"OK: {scanned} markdown file(s), all internal links resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
