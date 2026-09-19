#!/usr/bin/env bash
# Regression test for AUDIT-007: ./setup.sh tray in clone mode without the
# KWin scripts dir must fail without installing a broken autostart entry;
# with the dir present it must install both links.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail=0

# 1. Missing KWin dir: nonzero exit, no autostart entry.
if HOME="$T" bash "$REPO/setup.sh" tray >/dev/null 2>&1; then
	echo "FAIL: tray succeeded without KWin scripts dir"
	fail=1
else
	echo "ok: tray without KWin scripts dir exits nonzero"
fi
if [ -e "$T/.config/autostart/kitty-tray-autostart.desktop" ]; then
	echo "FAIL: broken autostart entry was installed"
	fail=1
else
	echo "ok: no broken autostart entry installed"
fi

# 2. Present KWin dir: exit 0, both links in place.
mkdir -p "$T/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma"
if HOME="$T" bash "$REPO/setup.sh" tray >/dev/null 2>&1; then
	echo "ok: tray with KWin scripts dir exits 0"
else
	echo "FAIL: tray with KWin scripts dir failed"; fail=1
fi
[ -L "$T/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/kitty_tray.py" ] \
	&& echo "ok: tray script linked" \
	|| { echo "FAIL: tray script link missing"; fail=1; }
[ -L "$T/.config/autostart/kitty-tray-autostart.desktop" ] \
	&& echo "ok: tray autostart linked" \
	|| { echo "FAIL: tray autostart link missing"; fail=1; }

exit $fail
