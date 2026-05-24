#!/usr/bin/env bash
# Verify internal markdown links under SKILL.md, references/, and related docs.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "${ROOT}/.github/scripts/check_skill_links.py" "$@"
