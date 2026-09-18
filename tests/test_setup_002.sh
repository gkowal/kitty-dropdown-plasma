#!/usr/bin/env bash
# Regression test for AUDIT-002: ./setup.sh autostart (and service) must
# not fail when systemctl is absent (non-systemd target platforms).
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail=0

# Minimal PATH without systemctl: symlink the tools setup.sh needs.
STUB="$T/stubbin"
mkdir -p "$STUB"
for tool in bash sh mkdir ln dirname readlink date cp rm cat; do
	p="$(command -v "$tool" 2>/dev/null)" || continue
	ln -sf "$p" "$STUB/$tool"
done
if command -v systemctl >/dev/null 2>&1; then
	if [ -x "$STUB/systemctl" ] || [ -L "$STUB/systemctl" ]; then
		rm -f "$STUB/systemctl"
	fi
fi

# 1. autostart without systemctl: exit 0, link in place.
if PATH="$STUB" HOME="$T" bash "$REPO/setup.sh" autostart >/dev/null 2>&1; then
	echo "ok: autostart without systemctl exits 0"
else
	echo "FAIL: autostart without systemctl failed"; fail=1
fi
if [ -L "$T/.config/autostart/kitty-autostart.desktop" ]; then
	echo "ok: autostart link installed"
else
	echo "FAIL: autostart link missing"; fail=1
fi

# 2. service without systemctl: exit 0, link in place.
if PATH="$STUB" HOME="$T" bash "$REPO/setup.sh" service >/dev/null 2>&1; then
	echo "ok: service without systemctl exits 0"
else
	echo "FAIL: service without systemctl failed"; fail=1
fi
if [ -L "$T/.config/systemd/user/kitty-dropdown.service" ]; then
	echo "ok: service link installed"
else
	echo "FAIL: service link missing"; fail=1
fi

# 3. With a (fake) systemctl present, daemon-reload is still invoked.
FAKEBIN="$T/fakebin"
mkdir -p "$FAKEBIN"
cp -P "$STUB"/* "$FAKEBIN"/ 2>/dev/null || true
printf '#!/usr/bin/env bash\necho "$@" >> "$0.log"\nexit 0\n' > "$FAKEBIN/systemctl"
chmod +x "$FAKEBIN/systemctl"
rm -f "$FAKEBIN/systemctl.log"
if PATH="$FAKEBIN" HOME="$T" bash "$REPO/setup.sh" autostart >/dev/null 2>&1; then
	echo "ok: autostart with systemctl exits 0"
else
	echo "FAIL: autostart with systemctl failed"; fail=1
fi
if grep -q "disable" "$FAKEBIN/systemctl.log" 2>/dev/null; then
	echo "ok: disable invoked when systemctl exists"
else
	echo "FAIL: disable not invoked with systemctl present"; fail=1
fi
if grep -q "daemon-reload" "$FAKEBIN/systemctl.log" 2>/dev/null; then
	echo "ok: daemon-reload invoked when systemctl exists"
else
	echo "FAIL: daemon-reload not invoked with systemctl present"; fail=1
fi

# 4. service with systemctl present still reloads.
rm -f "$FAKEBIN/systemctl.log"
if PATH="$FAKEBIN" HOME="$T" bash "$REPO/setup.sh" service >/dev/null 2>&1; then
	echo "ok: service with systemctl exits 0"
else
	echo "FAIL: service with systemctl failed"; fail=1
fi
if grep -q "daemon-reload" "$FAKEBIN/systemctl.log" 2>/dev/null; then
	echo "ok: service daemon-reload invoked when systemctl exists"
else
	echo "FAIL: service daemon-reload not invoked"; fail=1
fi

exit $fail
