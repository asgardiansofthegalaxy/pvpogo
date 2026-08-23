#!/usr/bin/env bash
# Claude Code Stop hook: refuse to end a turn while the verification gate is red.
#
# Reads the hook payload on stdin. Exits 0 (silent) when the tree is green.
# When it is red, prints {"decision":"block","reason":...} so the failure is fed
# back to the model instead of the turn ending on a broken tree.
set -uo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 0

payload=$(cat)

# Guard against a block loop: if this stop was already blocked once and the
# model still could not get to green, let the turn end so a human can look.
if command -v jq >/dev/null 2>&1; then
  if [[ "$(printf '%s' "$payload" | jq -r '.stop_hook_active // false')" == "true" ]]; then
    exit 0
  fi
fi

if ! output=$(npm run --silent verify 2>&1); then
  reason="The verification gate is failing, so this turn was not allowed to end.

$(printf '%s' "$output" | tail -60)

Fix the failures above, then re-run: npm run verify"
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg reason "$reason" '{decision: "block", reason: $reason}'
  else
    # Without jq, fall back to a non-blocking warning rather than emitting
    # malformed JSON (which would be ignored anyway).
    printf 'verify gate failed:\n%s\n' "$output" >&2
  fi
  exit 0
fi

exit 0
