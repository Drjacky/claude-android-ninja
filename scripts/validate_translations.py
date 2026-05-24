#!/usr/bin/env python3
"""Verify locale string/plural/array resource keys match the default values/ set."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RESOURCE_FILES = ("strings.xml", "plurals.xml", "arrays.xml")
TAGS_BY_FILE = {
    "strings.xml": {"string"},
    "plurals.xml": {"plurals"},
    "arrays.xml": {"string-array"},
}


def parse_resource_names(path: Path, filename: str) -> set[str]:
    if not path.is_file():
        return set()
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"{path}: invalid XML: {exc}") from exc

    tags = TAGS_BY_FILE[filename]
    names: set[str] = set()
    for elem in root.iter():
        if elem.tag in tags:
            name = elem.attrib.get("name")
            if name:
                names.add(name)
    return names


def collect_res_dirs(root: Path) -> list[Path]:
    dirs: set[Path] = set()
    for values_dir in root.rglob("values"):
        if values_dir.is_dir() and values_dir.parent.name == "res":
            dirs.add(values_dir.parent)
    return sorted(dirs)


def locale_value_dirs(res_dir: Path) -> list[Path]:
    locales: list[Path] = []
    for child in sorted(res_dir.iterdir()):
        if not child.is_dir() or not child.name.startswith("values-"):
            continue
        if any((child / name).is_file() for name in RESOURCE_FILES):
            locales.append(child)
    return locales


def validate_res_dir(res_dir: Path, strict_extra: bool) -> list[str]:
    errors: list[str] = []
    values_dir = res_dir / "values"
    if not values_dir.is_dir():
        return errors

    for filename in RESOURCE_FILES:
        base_path = values_dir / filename
        base_keys = parse_resource_names(base_path, filename)
        if not base_keys:
            continue

        for locale_dir in locale_value_dirs(res_dir):
            locale_path = locale_dir / filename
            if not locale_path.is_file():
                errors.append(
                    f"{locale_dir}: missing {filename} "
                    f"({len(base_keys)} key(s) in values/{filename})"
                )
                continue

            try:
                locale_keys = parse_resource_names(locale_path, filename)
            except ValueError as exc:
                errors.append(str(exc))
                continue

            for key in sorted(base_keys - locale_keys):
                errors.append(f"{locale_path}: missing key '{key}'")
            if strict_extra:
                for key in sorted(locale_keys - base_keys):
                    errors.append(f"{locale_path}: extra key '{key}' (not in values/{filename})")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that locale values-* resource files define the same keys as values/."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        type=Path,
        help="Project root to scan (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when a locale defines keys absent from the default values/ file",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    res_dirs = collect_res_dirs(root)
    if not res_dirs:
        print(f"No res/values directories under {root} (nothing to validate).")
        return 0

    all_errors: list[str] = []
    for res_dir in res_dirs:
        all_errors.extend(validate_res_dir(res_dir, args.strict))

    if all_errors:
        print("Translation validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        print(f"\n{len(all_errors)} problem(s) in {len(res_dirs)} res/ tree(s).", file=sys.stderr)
        return 1

    print(f"OK: {len(res_dirs)} res/ tree(s), locale keys match values/ defaults.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
