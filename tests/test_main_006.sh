#!/usr/bin/env bash
# Regression test for AUDIT-006: no KRunner query fallback in launchKitty();
# the systemd StartUnit request is preserved; failure handling does not
# pretend a dead branch can observe D-Bus errors (KWin never invokes the
# callback on error, and a successful StartUnit reply is always truthy).
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAIN="$REPO/contents/code/main.js"
README="$REPO/README.md"
fail=0

if grep -q "org.kde.krunner" "$MAIN"; then
	echo "FAIL: contents/code/main.js still references org.kde.krunner"
	fail=1
else
	echo "ok: no org.kde.krunner reference"
fi

# No functional KRunner usage outside comments (the explanatory comment
# in launchKitty deliberately names the removed fallback).
if grep -v '^[[:space:]]*//' "$MAIN" | grep -qi "krunner"; then
	echo "FAIL: contents/code/main.js still uses krunner outside comments"
	fail=1
else
	echo "ok: no krunner fallback"
fi

if grep -q "kitty-dropdown.service" "$MAIN" && grep -q '"replace"' "$MAIN"; then
	echo "ok: StartUnit service and mode preserved"
else
	echo "FAIL: StartUnit service/mode not preserved"
	fail=1
fi

# The old dead failure branch must be gone: KWin invokes the callback
# only on success, so `if (!res)` could never fire.
if grep -q "if (!res)" "$MAIN"; then
	echo "FAIL: contents/code/main.js still has unreachable if (!res) branch"
	fail=1
else
	echo "ok: no unreachable if (!res) branch"
fi

if grep -qi "fallback launch using KRunner" "$README"; then
	echo "FAIL: README still promises a KRunner fallback launch"
	fail=1
else
	echo "ok: README no longer promises a KRunner fallback"
fi

if command -v node >/dev/null 2>&1; then
	if node --check "$MAIN" >/dev/null 2>&1; then
		echo "ok: node --check passes"
	else
		echo "FAIL: node --check failed"
		fail=1
	fi
else
	echo "ok: node --check skipped (node not found)"
fi

exit $fail
