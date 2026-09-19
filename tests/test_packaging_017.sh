#!/usr/bin/env bash
# Regression test for AUDIT-017: packaging hygiene for the service unit,
# autostart entries, and KWin metadata.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

# 1. No deprecated/empty keys in the kitty autostart entry.
for key in TerminalOptions MimeType X-KDE-SubstituteUID X-KDE-Username; do
	if grep -q "^$key" "$REPO/kitty-autostart.desktop"; then
		echo "FAIL: kitty-autostart.desktop still has $key"; fail=1
	else
		echo "ok: no $key in kitty-autostart.desktop"
	fi
done

# 2. desktop-file-validate is clean when available (warnings count as
# failures: the tool exits 0 even when warning).
if command -v desktop-file-validate >/dev/null 2>&1; then
	out="$(desktop-file-validate "$REPO/kitty-autostart.desktop" \
		"$REPO/kitty-tray-autostart.desktop" 2>&1)"
	if [ -z "$out" ]; then
		echo "ok: desktop-file-validate clean"
	else
		echo "FAIL: desktop-file-validate reported issues:"
		printf '%s\n' "$out"
		fail=1
	fi
else
	echo "ok: desktop-file-validate skipped (not installed)"
fi

# 3. Tray autostart does not depend on the exec bit/shebang.
if grep -q '^Exec=.*python3 ' "$REPO/kitty-tray-autostart.desktop"; then
	echo "ok: tray Exec uses an explicit python3 interpreter"
else
	echo "FAIL: tray Exec relies on shebang/exec bit"; fail=1
fi

# 4. Restart expectation documented in the unit.
if grep -q "on demand" "$REPO/kitty-dropdown.service"; then
	echo "ok: restart expectation documented"
else
	echo "FAIL: restart expectation not documented"; fail=1
fi
if command -v systemd-analyze >/dev/null 2>&1; then
	if systemd-analyze verify "$REPO/kitty-dropdown.service" >/dev/null 2>&1; then
		echo "ok: systemd-analyze verify clean"
	else
		echo "FAIL: systemd-analyze verify failed"; fail=1
	fi
else
	echo "ok: systemd-analyze skipped (not installed)"
fi

# 5. metadata.json parses and has no duplicate keys.
if python3 - "$REPO/metadata.json" <<'EOF'; then
import json, sys
dups = []
def hook(pairs):
    seen = set()
    for k, v in pairs:
        if k in seen:
            dups.append(k)
        seen.add(k)
    return dict(pairs)
with open(sys.argv[1], encoding="utf-8") as f:
    json.load(f, object_pairs_hook=hook)
if dups:
    print(f"duplicate keys: {dups}")
    sys.exit(1)
EOF
	echo "ok: metadata.json parses with no duplicate keys"
else
	echo "FAIL: metadata.json has duplicate keys or bad JSON"; fail=1
fi

exit $fail
