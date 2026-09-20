#!/usr/bin/env bash
# Build the KDE Store upload artifact for kitty-dropdown-plasma.
#
# The archive contains ONLY the install payload, selected by an explicit
# include list (never archive the repo root):
#   - the full contents/ tree
#   - metadata.json
#   - LICENSE
#   - README.md
#   - setup.sh
#   - dropdown_manager.py
#   - kitty_tray.py
#   - kitty-autostart.desktop
#   - kitty-tray-autostart.desktop
#   - kitty-dropdown.service
# In particular this excludes: tests/, __pycache__/, .git/,
# package-kwinscript.sh itself, docs other than README.md.
#
# VERSION is read from metadata.json (KPlugin.Version).
set -euo pipefail

cd "$(dirname "$0")"

# Read KPlugin.Version from metadata.json; fail loudly if missing/empty.
if command -v python3 >/dev/null 2>&1; then
    VERSION="$(python3 -c 'import json,sys; print(json.load(open("metadata.json")).get("KPlugin", {}).get("Version", ""))')"
else
    VERSION="$(sed -n 's/.*"Version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' metadata.json | head -n 1)"
fi
if [ -z "${VERSION:-}" ]; then
    echo "error: could not read KPlugin.Version from metadata.json (missing or empty)" >&2
    exit 1
fi

# Sanity-check the payload inputs.
for f in contents metadata.json LICENSE README.md setup.sh dropdown_manager.py kitty_tray.py kitty-autostart.desktop kitty-tray-autostart.desktop kitty-dropdown.service; do
    if [ ! -e "$f" ]; then
        echo "error: required payload '$f' not found in repo root" >&2
        exit 1
    fi
done

ARTIFACT="kitty-dropdown-plasma-v${VERSION}.kwinscript"
rm -f "$ARTIFACT"

if command -v zip >/dev/null 2>&1; then
    zip -r "$ARTIFACT" contents metadata.json LICENSE README.md setup.sh dropdown_manager.py kitty_tray.py kitty-autostart.desktop kitty-tray-autostart.desktop kitty-dropdown.service
else
    if ! command -v python3 >/dev/null 2>&1; then
        echo "error: neither 'zip' nor 'python3' is available to build the archive" >&2
        exit 1
    fi
    ARTIFACT="$ARTIFACT" python3 -c '
import os, zipfile
artifact = os.environ["ARTIFACT"]
with zipfile.ZipFile(artifact, "w", zipfile.ZIP_DEFLATED) as z:
    z.write("metadata.json", "metadata.json")
    z.write("LICENSE", "LICENSE")
    z.write("README.md", "README.md")
    z.write("setup.sh", "setup.sh")
    z.write("dropdown_manager.py", "dropdown_manager.py")
    z.write("kitty_tray.py", "kitty_tray.py")
    z.write("kitty-autostart.desktop", "kitty-autostart.desktop")
    z.write("kitty-tray-autostart.desktop", "kitty-tray-autostart.desktop")
    z.write("kitty-dropdown.service", "kitty-dropdown.service")
    for root, dirs, files in os.walk("contents"):
        for name in sorted(files):
            path = os.path.join(root, name)
            z.write(path, path)
'
fi

echo "Built: $ARTIFACT"
echo "Verify with: unzip -l $ARTIFACT"
