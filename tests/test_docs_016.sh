#!/usr/bin/env bash
# Regression test for AUDIT-016: README must not overclaim launch-method
# exclusivity, --hold re-launch, or system-wide tray paths.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Join wrapped lines so normal Markdown re-wrapping cannot break matches.
TEXT="$(tr '\n' ' ' < "$REPO/README.md")"
fail=0

if printf '%s' "$TEXT" | grep -q "automatically switches between them"; then
	echo "FAIL: README still claims automatic switching"
	fail=1
else
	echo "ok: no automatic-switching overclaim"
fi

if printf '%s' "$TEXT" | grep -q "remove those manually"; then
	echo "ok: manual-file removal documented"
else
	echo "FAIL: manual-file removal not documented"
	fail=1
fi

if printf '%s' "$TEXT" | grep -q "again to re-launch"; then
	echo "FAIL: README still promises --hold re-launch"
	fail=1
else
	echo "ok: no --hold re-launch promise"
fi

if printf '%s' "$TEXT" | grep -q "follows the tray script itself"; then
	echo "ok: system-wide reload path documented"
else
	echo "FAIL: system-wide reload path not documented"
	fail=1
fi

exit $fail
