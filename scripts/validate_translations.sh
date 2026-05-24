#!/usr/bin/env bash
# Compare values-*/strings.xml (and plurals/arrays) keys against res/values/ defaults.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "${ROOT}/scripts/validate_translations.py" "$@"
