#!/usr/bin/env bash
# Regression test for AUDIT-009: an unpacked archive (source tree without
# .git, outside the KWin scripts dir) must be accepted like a clone.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail=0

SRC="$T/kitty-dropdown-plasma"
mkdir -p "$SRC/contents/code"
for f in setup.sh dropdown_manager.py kitty_tray.py kitty-dropdown.service \
	kitty-autostart.desktop kitty-tray-autostart.desktop; do
	cp "$REPO/$f" "$SRC/$f"
done
cp "$REPO/contents/code/main.js" "$SRC/contents/code/main.js"
chmod +x "$SRC/setup.sh"
[ -e "$SRC/.git" ] && { echo "FAIL: fixture unexpectedly has .git"; fail=1; }

# 1. kitten links from the archive tree.
if HOME="$T" bash "$SRC/setup.sh" kitten >/dev/null 2>&1; then
	echo "ok: archive kitten exits 0"
else
	echo "FAIL: archive kitten failed"; fail=1
fi
if [ -L "$T/.config/kitty/dropdown_manager.py" ]; then
	echo "ok: archive kitten link installed"
else
	echo "FAIL: archive kitten link missing"; fail=1
fi

# 2. Source is reported as an unpacked archive, not an error.
out="$(HOME="$T" bash "$SRC/setup.sh" kitten 2>&1)"
echo "$out" | grep -q "unpacked archive" \
	&& echo "ok: source reported as unpacked archive" \
	|| { echo "FAIL: source not reported as unpacked archive"; fail=1; }

# 3. Archive-mode tray links both files when the KWin dir exists.
mkdir -p "$T/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma"
if HOME="$T" bash "$SRC/setup.sh" tray >/dev/null 2>&1; then
	echo "ok: archive tray exits 0"
else
	echo "FAIL: archive tray failed"; fail=1
fi
[ -L "$T/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/kitty_tray.py" ] \
	&& echo "ok: archive tray script linked" \
	|| { echo "FAIL: archive tray script link missing"; fail=1; }

# 4. A directory with none of the payload is still rejected.
mkdir -p "$T/empty"
cp "$REPO/setup.sh" "$T/empty/setup.sh"
if HOME="$T" bash "$T/empty/setup.sh" kitten >/dev/null 2>&1; then
	echo "FAIL: payload-less dir unexpectedly accepted"; fail=1
else
	echo "ok: payload-less dir still rejected"
fi

# 5. A partial payload (missing one probed file) is still rejected.
mkdir -p "$T/partial/contents/code"
cp "$REPO/setup.sh" "$REPO/dropdown_manager.py" "$REPO/kitty_tray.py" "$T/partial/"
cp "$REPO/contents/code/main.js" "$T/partial/contents/code/main.js"
if HOME="$T" bash "$T/partial/setup.sh" kitten >/dev/null 2>&1; then
	echo "FAIL: partial payload unexpectedly accepted"; fail=1
else
	echo "ok: partial payload still rejected"
fi

exit $fail
