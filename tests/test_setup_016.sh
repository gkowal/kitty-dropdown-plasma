#!/usr/bin/env bash
# Behavioral half of AUDIT-016: switching launch methods removes only
# links created by this source; hand-installed files are left alone.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail=0

STUB="$T/stubbin"
mkdir -p "$STUB"
for tool in bash sh mkdir ln dirname readlink date cp rm; do
	p="$(command -v "$tool" 2>/dev/null)" || continue
	ln -sf "$p" "$STUB/$tool"
done

AUTOSTART="$T/.config/autostart/kitty-autostart.desktop"
SERVICE="$T/.config/systemd/user/kitty-dropdown.service"

# 1. Own symlink at the conflicting path is removed on switch.
mkdir -p "$T/.config/autostart" "$T/.config/systemd/user"
ln -sf "$REPO/kitty-autostart.desktop" "$AUTOSTART"
PATH="$STUB" HOME="$T" bash "$REPO/setup.sh" service >/dev/null 2>&1
[ ! -e "$AUTOSTART" ] \
	&& echo "ok: own conflicting symlink removed on switch" \
	|| { echo "FAIL: own conflicting symlink kept"; fail=1; }
[ -L "$SERVICE" ] \
	&& echo "ok: requested service link installed" \
	|| { echo "FAIL: service link missing"; fail=1; }

# 2. Regular file at the conflicting path is left untouched.
# (Remove the symlink first: writing through it would hit the repo file.)
rm -f "$AUTOSTART" "$SERVICE"
echo "hand installed" > "$AUTOSTART"
PATH="$STUB" HOME="$T" bash "$REPO/setup.sh" service >/dev/null 2>&1
[ -f "$AUTOSTART" ] && [ ! -L "$AUTOSTART" ] \
	&& echo "ok: regular conflicting file left untouched" \
	|| { echo "FAIL: regular conflicting file removed"; fail=1; }

# 3. Foreign symlink at the conflicting path is left untouched.
rm -f "$AUTOSTART"
echo "foreign" > "$T/foreign.desktop"
ln -sf "$T/foreign.desktop" "$AUTOSTART"
PATH="$STUB" HOME="$T" bash "$REPO/setup.sh" service >/dev/null 2>&1
[ "$(readlink "$AUTOSTART")" = "$T/foreign.desktop" ] \
	&& echo "ok: foreign conflicting symlink left untouched" \
	|| { echo "FAIL: foreign conflicting symlink removed"; fail=1; }

exit $fail
