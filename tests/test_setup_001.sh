#!/usr/bin/env bash
# Regression test for AUDIT-001: link_file() must not silently replace
# an existing regular file; --force replaces it keeping a backup.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
fail=0

check() { # <desc> <condition-cmd...>
	local desc="$1"; shift
	if "$@"; then echo "ok: $desc"; else echo "FAIL: $desc"; fail=1; fi
}

mkdir -p "$T/.config/kitty"
echo "user customized content" > "$T/.config/kitty/dropdown_manager.py"

# 1. Without --force: must refuse, keep the regular file untouched.
if HOME="$T" bash "$REPO/setup.sh" kitten >/dev/null 2>&1; then
	echo "FAIL: setup.sh kitten succeeded despite regular file"
	fail=1
else
	echo "ok: setup.sh kitten refuses regular file"
fi
check "regular file content preserved" \
	test "$(cat "$T/.config/kitty/dropdown_manager.py")" = "user customized content"
check "regular file not a symlink" test ! -L "$T/.config/kitty/dropdown_manager.py"

# 2. With --force: symlink installed, timestamped backup keeps content.
HOME="$T" bash "$REPO/setup.sh" --force kitten >/dev/null 2>&1
check "--force exits 0" test $? -eq 0
check "--force installs symlink" test -L "$T/.config/kitty/dropdown_manager.py"
backup=( "$T"/.config/kitty/dropdown_manager.py.bak-* )
check "--force keeps backup" test -f "${backup[0]}"
check "backup has original content" \
	test "$(cat "${backup[0]}")" = "user customized content"

# 3. Fresh destination links without --force.
rm -rf "$T/.config/kitty"
HOME="$T" bash "$REPO/setup.sh" kitten >/dev/null 2>&1
check "fresh link exits 0" test $? -eq 0
check "fresh link is symlink" test -L "$T/.config/kitty/dropdown_manager.py"

# 4. --force alone (no component) is a usage error.
if HOME="$T" bash "$REPO/setup.sh" --force >/dev/null 2>&1; then
	echo "FAIL: --force without component unexpectedly succeeded"
	fail=1
else
	echo "ok: --force without component is a usage error"
fi

# 5. Short flag -f and trailing position both enable force, and repeated
# --force runs keep distinct backups (no same-second clobber).
rm -f "$T"/.config/kitty/dropdown_manager.py*
echo "second version" > "$T/.config/kitty/dropdown_manager.py"
HOME="$T" bash "$REPO/setup.sh" kitten -f >/dev/null 2>&1
check "trailing -f replaces with backup" test -L "$T/.config/kitty/dropdown_manager.py"
rm -f "$T/.config/kitty/dropdown_manager.py"
echo "third version" > "$T/.config/kitty/dropdown_manager.py"
HOME="$T" bash "$REPO/setup.sh" -f kitten >/dev/null 2>&1
nbackups=( "$T"/.config/kitty/dropdown_manager.py.bak-* )
check "two backups coexist (no same-second clobber)" test "${#nbackups[@]}" -eq 2
check "first backup kept second version" \
	grep -q "second version" "$T"/.config/kitty/dropdown_manager.py.bak-*

# 6. Existing symlink is still overwritten without --force.
HOME="$T" bash "$REPO/setup.sh" kitten >/dev/null 2>&1
check "symlink overwrite without --force exits 0" test $? -eq 0

# 7. Unknown component and service/autostart conflict still error.
if HOME="$T" bash "$REPO/setup.sh" bogus >/dev/null 2>&1; then
	echo "FAIL: unknown component unexpectedly succeeded"; fail=1
else
	echo "ok: unknown component is an error"
fi
if HOME="$T" bash "$REPO/setup.sh" service autostart >/dev/null 2>&1; then
	echo "FAIL: service+autostart unexpectedly succeeded"; fail=1
else
	echo "ok: service+autostart conflict is an error"
fi

exit $fail
