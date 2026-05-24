#!/usr/bin/env bash
# Validate Agent Skills frontmatter (skills-ref) and internal markdown links.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT}"

echo "==> Reference line counts (INDEX-sections headings, anchors, ~N blurbs)"
"${ROOT}/.github/scripts/check-skill-index-line-counts.sh"

echo "==> Internal markdown links"
"${ROOT}/.github/scripts/check-skill-links.sh"

echo "==> Agent ergonomics (INDEX/SKILL size, -quick.md coverage)"
"${ROOT}/.github/scripts/check-skill-ergonomics.sh"

echo "==> Skill-doc voice"
"${ROOT}/.github/scripts/check-skill-voice.sh"

echo "==> Markdown typography (ASCII punctuation and spaces)"
"${ROOT}/.github/scripts/check-skill-typography.sh"

run_skills_ref() {
  # skills-ref requires the path basename to match `name:` in frontmatter (not ".").
  skills-ref validate "${ROOT}"
}

if command -v skills-ref >/dev/null 2>&1; then
  echo "==> Agent Skills frontmatter (skills-ref)"
  run_skills_ref
  echo "Skill validation passed."
  exit 0
fi

if command -v uv >/dev/null 2>&1; then
  echo "==> Agent Skills frontmatter (skills-ref via uv)"
  uv tool run --from "skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref" \
    skills-ref validate "${ROOT}"
  echo "Skill validation passed."
  exit 0
fi

echo "WARN: skills-ref not found; skipped frontmatter check." >&2
echo "Install: uv tool install \"skills-ref @ git+https://github.com/agentskills/agentskills.git#subdirectory=skills-ref\"" >&2
echo "Link check passed."
