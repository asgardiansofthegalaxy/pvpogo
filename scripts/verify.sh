#!/usr/bin/env bash
# One gate for the whole repo.
#
#   scripts/verify.sh              fast gate: lint, types, unit tests (~20s)
#   scripts/verify.sh --with-e2e   also builds the app and runs Playwright
#
# The fast gate is what the Claude Code Stop hook and pre-push run. CI runs
# --with-e2e. Keep the fast path fast: a slow gate gets switched off.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
ROOT="$PWD"
WITH_E2E=0
[[ "${1:-}" == "--with-e2e" ]] && WITH_E2E=1

# Prefer the project venv so the gate matches CI; fall back to whatever python
# is on PATH rather than failing outright.
PY="$ROOT/pypogo/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3 || true)"
  if [[ -z "$PY" ]]; then
    echo "FAIL  no python found. Run: python3 -m venv pypogo/.venv && pypogo/.venv/bin/pip install -r pypogo/requirements-dev.txt -e pypogo" >&2
    exit 1
  fi
  echo "note  pypogo/.venv missing, falling back to $PY"
fi

FAILED=()
run() {
  local name="$1"; shift
  printf '\n\033[1m=== %s ===\033[0m\n' "$name"
  if "$@"; then
    printf '\033[32mok    %s\033[0m\n' "$name"
  else
    printf '\033[31mFAIL  %s\033[0m\n' "$name"
    FAILED+=("$name")
  fi
}

run "eslint"      npm run --silent lint
run "tsc"         npm run --silent typecheck
run "ruff"        "$PY" -m ruff check pypogo
run "mypy"        env -C "$ROOT/pypogo" "$PY" -m mypy
run "pytest"      env -C "$ROOT/pypogo" "$PY" -m pytest -q

if [[ $WITH_E2E -eq 1 ]]; then
  run "playwright" npx playwright test
fi

printf '\n'
if [[ ${#FAILED[@]} -eq 0 ]]; then
  printf '\033[32mall checks passed\033[0m\n'
  exit 0
fi
printf '\033[31m%d check(s) failed: %s\033[0m\n' "${#FAILED[@]}" "${FAILED[*]}"
exit 1
