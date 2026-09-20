#!/usr/bin/env bash
# Regression test: the KDE Store bundle (.kwinscript) contains exactly the
# intended payload and none of the excluded paths.
set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0
ARTIFACT=""
cleanup() {
	if [ -n "$ARTIFACT" ] && [ -e "$ARTIFACT" ]; then
		rm -f "$ARTIFACT"
	fi
}
trap cleanup EXIT

# Listing needs `unzip -l` or a python3 zipfile listing; the builder needs
# `zip` or python3. Skip gracefully if we can neither build nor list.
if ! command -v unzip >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
	echo "SKIP: neither unzip nor python3 available to list the bundle"
	exit 0
fi
if ! command -v zip >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
	echo "SKIP: neither zip nor python3 available to build the bundle"
	exit 0
fi

# Build the artifact into the repo root.
if ! (cd "$REPO" && ./package-kwinscript.sh); then
	echo "FAIL: package-kwinscript.sh failed to build"
	exit 1
fi
echo "ok: package-kwinscript.sh built the artifact"

# Resolve the built artifact (version comes from metadata.json).
if command -v python3 >/dev/null 2>&1; then
	VERSION="$(python3 -c 'import json; print(json.load(open("'"$REPO"'/metadata.json")).get("KPlugin", {}).get("Version", ""))')"
else
	VERSION="$(sed -n 's/.*"Version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$REPO/metadata.json" | head -n 1)"
fi
ARTIFACT="$REPO/kitty-dropdown-plasma-v${VERSION}.kwinscript"
if [ ! -f "$ARTIFACT" ]; then
	echo "FAIL: expected artifact $ARTIFACT not found"
	exit 1
fi
echo "ok: found artifact $(basename "$ARTIFACT")"

# List archive members, one path per line.
if command -v unzip >/dev/null 2>&1; then
	LISTING="$(unzip -l "$ARTIFACT" | awk 'NR>3 {print $4}' | sed -e '/^$/d' -e '/^----/d' -e '/^Archive/d' -e '/files$/d' -e '/^Name$/d')"
else
	LISTING="$(python3 -c 'import sys,zipfile; print("\n".join(zipfile.ZipFile(sys.argv[1]).namelist()))' "$ARTIFACT")"
fi
if [ -z "$LISTING" ]; then
	echo "FAIL: empty archive listing for $(basename "$ARTIFACT")"
	exit 1
fi

# The intended payload: every file below must be present, and no other
# file may be in the archive (directory entries are ignored).
EXPECTED="contents/code/main.js
contents/config/main.xml
contents/ui/config.ui
metadata.json
LICENSE
README.md
setup.sh
dropdown_manager.py
kitty_tray.py
kitty-autostart.desktop
kitty-tray-autostart.desktop
kitty-dropdown.service"

for f in $EXPECTED; do
	if printf '%s\n' "$LISTING" | grep -qx "$f"; then
		echo "ok: bundle contains $f"
	else
		echo "FAIL: bundle missing $f"
		fail=1
	fi
done

# Excluded paths must not appear.
for pat in "tests/" "__pycache__" ".git" "package-kwinscript.sh" "CHANGELOG.md" "AUDIT.md"; do
	if printf '%s\n' "$LISTING" | grep -q "$pat"; then
		echo "FAIL: bundle contains excluded entry matching '$pat'"
		fail=1
	else
		echo "ok: no '$pat' entries in bundle"
	fi
done

# Nothing beyond the intended set (ignoring directory entries).
while IFS= read -r entry; do
	[ -n "$entry" ] || continue
	case "$entry" in
		*/) continue ;; # directory entry from `zip -r`
	esac
	if ! printf '%s\n' "$EXPECTED" | grep -qx "$entry"; then
		echo "FAIL: unexpected entry in bundle: $entry"
		fail=1
	fi
done <<< "$LISTING"
if [ "$fail" -eq 0 ]; then
	echo "ok: bundle holds exactly the intended file set"
fi

exit $fail
