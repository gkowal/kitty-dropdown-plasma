#!/usr/bin/env bash
set -euo pipefail

KWN_SCRIPTS_DIR="$HOME/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma"
KCFG_DIR="$HOME/.config/kitty"
SYSTEMD_DIR="$HOME/.config/systemd/user"
AUTOSTART_DIR="$HOME/.config/autostart"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -e "$script_dir/.git" ]]; then
	mode="clone"
elif [[ "$script_dir" == "$KWN_SCRIPTS_DIR" ]]; then
	mode="installed"
else
	echo "error: cannot determine source directory from $script_dir" >&2
	echo "       run this script from the repository clone or from" >&2
	echo "       $KWN_SCRIPTS_DIR (KDE Store install)." >&2
	exit 1
fi

usage() {
	cat <<'EOF'
Usage: ./setup.sh <component> [<component> ...]

Links the companion components of Kitty Drop-Down Plasma into their install
locations as symlinks, so updates propagate when the source changes.

Components:
  kitten     dropdown_manager.py       -> ~/.config/kitty/
  service    kitty-dropdown.service    -> ~/.config/systemd/user/
  autostart  kitty-autostart.desktop   -> ~/.config/autostart/
  tray       kitty_tray.py             -> ~/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/
             kitty-tray-autostart.desktop -> ~/.config/autostart/

Note: 'service' and 'autostart' are mutually exclusive (only one launch
method). Requesting both is an error; linking one removes the other's link.
EOF
}

link_file() {
	local src="$1" target="$2" dir
	[[ -f "$src" ]] || { echo "warning: missing $src, skipping" >&2; return 1; }
	if [[ -e "$target" && ! -L "$target" ]]; then
		echo "warning: replacing regular file $target with a symlink" >&2
		echo "         (back up the file first if you modified it)" >&2
	fi
	dir="$(dirname "$target")"
	mkdir -p "$dir"
	ln -sfn "$src" "$target"
	echo "linked  $target"
}

# Remove a previously linked component only if it is a symlink into our source.
unlink_linked() {
	local target="$1" resolved
	if [[ -L "$target" ]]; then
		resolved="$(readlink -f "$target")"
		if [[ "$resolved" == "$script_dir"/* ]]; then
			rm -f "$target"
			echo "unlinked  $target"
		else
			echo "warning: $target is a symlink to $resolved (not from this source); leaving it" >&2
		fi
	elif [[ -e "$target" ]]; then
		echo "warning: $target exists as a regular file (not a symlink); leaving it" >&2
		echo "         remove it manually if you want a linked install" >&2
	fi
}

do_service() {
	unlink_linked "$AUTOSTART_DIR/kitty-autostart.desktop"
	link_file "$script_dir/kitty-dropdown.service" "$SYSTEMD_DIR/kitty-dropdown.service"
	systemctl --user daemon-reload
	echo "note: systemd unit registered; 'git pull' users: re-run 'systemctl --user daemon-reload' after pulling"
}

do_autostart() {
	unlink_linked "$SYSTEMD_DIR/kitty-dropdown.service"
	systemctl --user disable kitty-dropdown.service 2>/dev/null || true
	link_file "$script_dir/kitty-autostart.desktop" "$AUTOSTART_DIR/kitty-autostart.desktop"
	systemctl --user daemon-reload
}

do_kitten() {
	link_file "$script_dir/dropdown_manager.py" "$KCFG_DIR/dropdown_manager.py"
}

do_tray() {
	if [[ "$mode" == "clone" ]]; then
		if [[ ! -d "$KWN_SCRIPTS_DIR" ]]; then
			echo "warning: $KWN_SCRIPTS_DIR does not exist (kpackagetool6 --install not run yet);" >&2
			echo "         skipping the kitty_tray.py link" >&2
		else
			link_file "$script_dir/kitty_tray.py" "$KWN_SCRIPTS_DIR/kitty_tray.py"
		fi
	else
		echo "note: kitty_tray.py already lives in the installed package; updates come via 'kpackagetool6 --upgrade'"
	fi
	link_file "$script_dir/kitty-tray-autostart.desktop" "$AUTOSTART_DIR/kitty-tray-autostart.desktop"
}

if [[ $# -eq 0 ]]; then
	usage
	exit 1
fi

if [[ "$*" == *service* && "$*" == *autostart* ]]; then
	echo "error: 'service' and 'autostart' are mutually exclusive (only one launch method)" >&2
	echo "       choose one:  ./setup.sh service   |   ./setup.sh autostart" >&2
	exit 1
fi

if [[ "$mode" == "clone" ]]; then
	echo "Source: git clone at $script_dir"
else
	echo "Source: installed package at $script_dir"
fi

for arg in "$@"; do
	case "$arg" in
		kitten) do_kitten ;;
		service) do_service ;;
		autostart) do_autostart ;;
		tray) do_tray ;;
		*)
			echo "error: unknown component '$arg'" >&2
			usage
			exit 1
			;;
	esac
done
