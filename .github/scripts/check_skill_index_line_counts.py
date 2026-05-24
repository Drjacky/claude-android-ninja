#!/usr/bin/env python3
"""Verify declared reference line counts in skill markdown match actual file sizes.

Matches:
- INDEX-sections headings: ### foo.md (1234 lines)
- INDEX-sections anchors: INDEX-sections.md#foomd-1234-lines
- Quick/full guide blurbs: [foo.md](foo.md) (~1230 lines)  (nearest 10)

Scans references/**/*.md and assets/convention/*.md. Skips README.md and SKILL.md.

CI runs check-only. Refresh locally:

  ./.github/scripts/check-skill-index-line-counts.sh --fix

Rewrites files on disk; commit yourself (no auto-commit in Actions).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
REFERENCES = ROOT / "references"

SCAN_GLOBS = (
    "references/**/*.md",
    "assets/convention/*.md",
)
SKIP_FILES = {
    ROOT / "README.md",
    ROOT / "SKILL.md",
}

HEADING_RE = re.compile(
    r"^### (?P<file>[^\s()]+\.md) \((?P<count>\d+) lines\)$",
    re.MULTILINE,
)
ANCHOR_RE = re.compile(
    r"INDEX-sections\.md#(?P<slug>[\w-]+?md)-(?P<count>\d+)-lines"
)
APPROX_RE = re.compile(
    r"\[(?P<file>[^\]]+\.md)\]\([^)]+\) \(~(?P<count>\d+) lines\)"
)


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def approximate_line_count(actual: int) -> int:
    return round(actual / 10) * 10


def slug_to_filename(slug: str) -> str:
    if slug.endswith("md"):
        return f"{slug[:-2]}.md"
    return f"{slug}.md"


def ref_path_for(filename: str) -> Path:
    return REFERENCES / Path(filename).name


def collect_markdown_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        files.update(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(path for path in files if path not in SKIP_FILES)


def actual_for(filename: str, cache: dict[str, int]) -> int | None:
    name = Path(filename).name
    if name not in cache:
        path = ref_path_for(name)
        if not path.is_file():
            cache[name] = -1
        else:
            cache[name] = line_count(path)
    count = cache[name]
    return None if count < 0 else count


def process_file(
    md_path: Path,
    *,
    fix: bool,
    cache: dict[str, int],
) -> tuple[list[str], int, bool]:
    errors: list[str] = []
    fixed = 0
    rel = md_path.relative_to(ROOT)
    text = md_path.read_text(encoding="utf-8")
    changed = False

    def fail(message: str) -> None:
        errors.append(f"{rel}: {message}")

    def replace_heading(match: re.Match[str]) -> str:
        nonlocal fixed, changed
        filename = match.group("file")
        declared = int(match.group("count"))
        actual = actual_for(filename, cache)
        if actual is None:
            fail(f"{filename} ({declared} lines) - missing {ref_path_for(filename).relative_to(ROOT)}")
            return match.group(0)
        if declared != actual:
            if fix:
                fixed += 1
                changed = True
                return f"### {filename} ({actual} lines)"
            fail(f"{filename} declared {declared} lines, actual {actual}")
        return match.group(0)

    def replace_anchor(match: re.Match[str]) -> str:
        nonlocal fixed, changed
        slug = match.group("slug")
        declared = int(match.group("count"))
        filename = slug_to_filename(slug)
        actual = actual_for(filename, cache)
        if actual is None:
            fail(
                f"INDEX-sections.md#{slug}-{declared}-lines - "
                f"missing {ref_path_for(filename).relative_to(ROOT)}"
            )
            return match.group(0)
        if declared != actual:
            if fix:
                fixed += 1
                changed = True
                return f"INDEX-sections.md#{slug}-{actual}-lines"
            fail(
                f"INDEX-sections.md#{slug}-{declared}-lines - "
                f"{filename} actual {actual} lines"
            )
        return match.group(0)

    def replace_approx(match: re.Match[str]) -> str:
        nonlocal fixed, changed
        filename = match.group("file")
        declared = int(match.group("count"))
        actual = actual_for(filename, cache)
        if actual is None:
            fail(f"[{filename}](...) (~{declared} lines) - missing reference file")
            return match.group(0)
        expected = approximate_line_count(actual)
        if declared != expected:
            if fix:
                fixed += 1
                changed = True
                link_target = match.group(0).split("](", 1)[1].split(")", 1)[0]
                return f"[{filename}]({link_target}) (~{expected} lines)"
            fail(
                f"[{filename}](...) (~{declared} lines) - "
                f"expected ~{expected} from actual {actual}"
            )
        return match.group(0)

    new_text = HEADING_RE.sub(replace_heading, text)
    new_text = ANCHOR_RE.sub(replace_anchor, new_text)
    new_text = APPROX_RE.sub(replace_approx, new_text)

    if fix and changed:
        md_path.write_text(new_text, encoding="utf-8")

    return errors, fixed, changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite stale counts in skill markdown (local use only)",
    )
    args = parser.parse_args()

    cache: dict[str, int] = {}
    all_errors: list[str] = []
    total_fixed = 0
    files_changed = 0
    files_checked = 0

    for md_path in collect_markdown_files():
        files_checked += 1
        errors, fixed, changed = process_file(md_path, fix=args.fix, cache=cache)
        all_errors.extend(errors)
        total_fixed += fixed
        if changed:
            files_changed += 1

    if args.fix and files_changed:
        print(f"Updated {total_fixed} line count(s) across {files_changed} file(s).")

    if all_errors and not args.fix:
        print("Reference line count check failed:", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        print(
            "Run: ./.github/scripts/check-skill-index-line-counts.sh --fix",
            file=sys.stderr,
        )
        return 1

    if all_errors and args.fix:
        print(
            f"WARN: {len(all_errors)} issue(s) could not be auto-fixed.",
            file=sys.stderr,
        )
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.fix and total_fixed:
        print(
            f"OK: {files_checked} markdown file(s) checked, "
            f"{total_fixed} count(s) refreshed."
        )
        return 0

    print(f"OK: {files_checked} markdown file(s), reference line counts match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
