#!/bin/sh
# Preserve command failures and detect failures in legacy QA output.
set -eu
binary=$1
script=$2
log=$3
shift 3
mkdir -p "$(dirname "$log")"
status=0
"$binary" "$script" "$@" > "$log" 2>&1 || status=$?
cat "$log"
if [ "$status" -ne 0 ]; then exit "$status"; fi
if grep -Ei '(^ERR:|FAIL:|>>>.*(ERR|PROBLEM|failed)|=> nil|runtime error:|ERROR: AddressSanitizer)' "$log" >/dev/null; then
    echo "FAIL: $script reported a failure" >&2
    exit 1
fi
if ! grep -E 'SUC+ESSFUL' "$log" >/dev/null; then
    echo "FAIL: $script did not report completion" >&2
    exit 1
fi
