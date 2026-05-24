#!/usr/bin/env bash
# Verify reference line counts in skill markdown (INDEX-sections headings, anchors, ~N blurbs).
# Pass --fix to update stale counts locally (not used in CI).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "${ROOT}/.github/scripts/check_skill_index_line_counts.py" "$@"
