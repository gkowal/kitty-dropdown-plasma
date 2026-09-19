# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `setup.sh --force/-f`: replaces an existing regular file with a symlink
  after keeping a uniquely named timestamped backup.
- `setup.sh` accepts unpacked release archives (e.g. ZIP downloads) as
  source trees, detected by payload instead of `.git` presence.
- Regression suites: shell tests for the installer (`tests/test_setup_*`),
  node harnesses for the KWin geometry/launch logic (`tests/test_main_*`),
  and mocked unit tests for the kitten and tray (`tests/test_dropdown_*`,
  `tests/test_tray_*`).

### Removed
- Non-functional KRunner launch fallback: `App.query()` only fills the
  runner UI and never launches anything, so a failed systemd `StartUnit`
  request now surfaces via KWin's own D-Bus error log instead. Install
  the autostart entry on non-systemd systems so Kitty is ready on toggle.

### Fixed
- Installer no longer silently replaces customized regular files; it
  refuses by default and installs the new link before removing the old
  launch method, so a refused switch leaves the previous setup intact.
- `./setup.sh autostart`/`service` no longer abort when `systemctl` is
  absent (the non-systemd audience); `daemon-reload` is skipped there.
- `./setup.sh tray` refuses when the KWin scripts directory is missing
  instead of installing an autostart entry pointing at nothing.
- Smart EOF (`Ctrl+D`) never destroys the OS window, fails safe by
  forwarding EOF on unknown foreground-process state, aborts on stale
  window ids instead of acting on the active terminal, recognizes login
  shells (`-zsh`), and bounds the D-Bus call with a timeout.
- `yOffset` is clamped against the work area so oversized offsets cannot
  push the dropdown off-screen.
- With several matching dropdown windows, toggling prefers the one on
  the active screen; missing-window toggles keep retrying instead of
  risking a wedged launch guard.
- Tray Settings dialog validates per-screen overrides JSON (finite whole
  pixels, positive sizes/ratios, known keys) before saving.
- Tray Settings reload now loads `main.js` from the package containing
  `kitty_tray.py` instead of a hardcoded user-local path, so it works
  for system-wide installs too.
- Tray robustness: missing `kreadconfig6`/`kwriteconfig6` now degrade to
  defaults/abort-with-warning instead of tracebacks, the unload wait
  pumps Qt events, the single-instance lock is per-user on `/tmp`, and
  a non-numeric `loadScript` reply fails gracefully.
- README no longer overclaims launch-method switching, `--hold`
  re-launch, or system-wide tray paths.
- Packaging: dropped deprecated/empty desktop keys, the tray autostart
  entry uses an explicit `python3` interpreter, and the service unit
  documents its on-demand restart expectation.

## [v1.7] - 2026-08-04

### Added
- **Tray Settings dialog**: adjust window ratios, per-screen JSON overrides, and
  re-center behavior. Apply/OK write `kwinrc`, refresh KWin's script config, and
  reload the script so geometry re-applies in place.
- **`recenterOnShow`** config option (default off).
- **`setup.sh`** post-install symlink helper: links the kitten, systemd service,
  autostart, and tray components into their install locations. Auto-detects a git
  clone vs. an installed KDE Store package, enforces service/autostart
  exclusivity, and is idempotent.
- Single-instance guard for the tray via `QLockFile`.

### Fixed
- **Autostart**: replace the invalid `\$HOME` escape with `~`
  (`sh -c "exec ~/..."`); the systemd autostart generator rejected/mangled the old
  Exec line so the tray never started at login. Applies to both the tray and
  kitty autostart entries.
- Tray toggling: surface failures and verify the shortcut is registered; run the
  tray directly instead of via `exec()`; fall back to a generic tray icon.
- Kitten: add a `main` entry point (fixes `KeyError: 'main'`), correct the
  `invokeShortcut` return check, log `close_tab`/process-detection failures, hoist
  `KNOWN_SHELLS`.
- `main.js`: sanitize config values at read time, validate `screenOverrides`,
  apply geometry on screen change with a fit fallback, recompute only the
  overflowing dimension, refit off-screen dropdowns on show, use output
  geometry/work area to detect misplaced windows, prevent a show–minimize loop,
  make kitty launch retry robust (incl. KRunner fallback with `~` expansion).

### Changed
- Remove irrelevant terminal-emulator metadata from `kitty-autostart.desktop`.

### Docs
- Document the systemd `[Install]` section and launch-method tradeoffs, and the
  one-frame flicker when toggling between monitors.
- Ignore `__pycache__` in the repository.

## [v1.6] - 2026-08-01

### Added
- Native GUI configuration (Plasma 6 config page) and multi-monitor scaling.

### Changed
- Kitten: target a specific window ID and expand the shell whitelist.
- Improve shell detection, `qdbus` fallback, and window matching.

### Docs
- Correct animation-settings references in the README.

## [v1.5] - 2026-07-30

### Fixed
- Preserve custom KWin Window Rules on startup and toggle.

## [v1.4] - 2026-07-30

### Added
- Dynamic geometry positioning and a native borderless setup.

### Docs
- Document toggle animations and desktop-effects customization.

## [v1.3] - 2026-07-28

### Added
- Optional system tray icon applet (PyQt6.QtDBus).
- Auto-launch Kitty on demand via a systemd D-Bus service.

### Docs
- Add KDE Store badge and official Kitty references.

## [v1.2] - 2026-02-18

### Changed
- Autodetect the `qdbus` command for the KDE minimize action.
- Switch the KPlugin Id to reverse-DNS format.

## [v1.1] - 2026-02-14

### Added
- Add `dropdown_manager.py` for native window management (Smart EOF).

### Docs
- Update Smart EOF instructions.
- Remove obsolete `kitty-dropdown.sh`.

## [v1.0] - 2026-02-04

### Added
- Initial release: KWin script and configuration, autostart entry, README, metadata.