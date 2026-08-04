# Kitty Drop-Down Plasma

**Kitty Drop-Down Plasma** is a productivity-focused KWin script designed for **KDE Plasma 6**. It provides a Quake-style, drop-down terminal experience using [**Kitty**](https://sw.kovidgoyal.net/kitty/), a fast, feature-rich, GPU-based terminal emulator. You can explore the source code or contribute to its development on the [Kitty GitHub repository](https://github.com/kovidgoyal/kitty).

This project combines KWin window management logic with shell-level integration to ensure your terminal is always available and protected from accidental closure.

[![kde-store](https://img.shields.io/badge/KDE%20Store-download-blue?logo=KDE)](https://store.kde.org/p/2348115)
[![Kitty Terminal](https://img.shields.io/badge/Terminal-Kitty-green?logo=kitty&logoColor=white)](https://sw.kovidgoyal.net/kitty/)

---

## 1. Installation Guide

Installing this script requires a few steps to register it within the KDE Plasma environment and ensure the terminal starts with the correct identifiers.

### Step 1: Obtain the Source Code

First, you need to download the script files to your local machine. You can do this by cloning the repository from GitHub:

```
git clone https://github.com/gkowal/kitty-dropdown-plasma.git
cd kitty-dropdown-plasma
```

Alternatively, download the ZIP archive from the repository and unpack it locally.

### Step 2: Install via KPackageTool

KDE Plasma uses the `kpackagetool6` utility to manage KWin scripts. Open a terminal inside the unpacked directory and run the following command to register the script with your system:

```
kpackagetool6 --type KWin/Script --install .
```

This command packages the files and moves them to the appropriate local directory so KWin can recognize them as an available extension.

### Step 3: Enable the Script

Once installed, the script must be activated within your system settings.

1. Open **System Settings**.
2. Navigate to **Window Management > KWin Scripts**.
3. Locate **Kitty Drop-Down Plasma** in the list and check the box to enable it.
4. Click **Apply**.

---

## 2. Configuration & Integration

### Custom Kitty Profile

While not strictly required, using a dedicated configuration file allows you to style the drop-down terminal independently of your main Kitty windows. Create a file at `~/.config/kitty/kitty-dropdown.conf` with your preferred settings (e.g., transparency or specific fonts).

### Launch Methods: Systemd Service vs. Autostart File

You can choose between two methods to manage the Kitty process:

> [!NOTE]
> **Linked installs.** The commands below install the companion components as **symlinks** into your home directory, so the installed files always follow the repository (or the KDE Store package). Run `./setup.sh` from the repository root — or, if you installed the script from the KDE Store, run the same commands from `~/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/`, where the script auto-detects its installed location. Only **one** launch method may be installed (`service` **or** `autostart`); `setup.sh` enforces this and automatically switches between them. The plain `cp` installs documented in earlier releases remain a valid alternative if you do not want symlinks.

#### Method A: On-Demand Systemd Service (Recommended)

If your Linux distribution uses `systemd` user sessions (Fedora, Arch, Manjaro, openSUSE, Ubuntu, Debian, etc.), we strongly recommend using the provided systemd service:

```bash
./setup.sh service
```

If you prefer not to use the script, link the file by hand:

```bash
mkdir -p ~/.config/systemd/user/
ln -sf "$(pwd)/kitty-dropdown.service" ~/.config/systemd/user/
systemctl --user daemon-reload
```

> [!NOTE]
> Because the unit file is symlinked, `git pull` updates it in place. After a pull, re-run `systemctl --user daemon-reload` (and restart the unit with `systemctl --user restart kitty-dropdown.service` if it is running) so systemd picks up the changes.

**Why this is preferred:**
- **Zero Resource Overhead at Boot:** Kitty is **not** launched at desktop startup, consuming 0 RAM and CPU.
- **On-Demand Activation:** The first time you press the toggle shortcut (`Meta+F12`), the KWin script automatically starts the service via D-Bus.
- **Self-Healing:** If Kitty crashes or is closed, pressing the shortcut automatically re-launches it on demand.
- **Optional Enable at Boot:** The service includes an `[Install]` section, so you may run `systemctl --user enable kitty-dropdown.service` if you prefer Kitty to start automatically at login instead of on-demand.

> [!NOTE]
> Both launch methods use Kitty's `--hold` flag, which keeps the terminal window open if the shell process exits (e.g., crashes on a segfault or is OOM-killed). This prevents the window from disappearing unexpectedly, allowing you to inspect the state. The trade-off is that a crashed shell leaves a frozen terminal window — press `Meta+F12` again to re-launch.

#### Method B: Traditional Autostart File (Non-Systemd Environments)

If your system does not use `systemd` user sessions (e.g., Devuan, Gentoo/OpenRC, Void, Artix), you can launch Kitty automatically on desktop login using the provided `.desktop` file:

```bash
./setup.sh autostart
```

If you prefer not to use the script, link the file by hand:

```bash
ln -sf "$(pwd)/kitty-autostart.desktop" ~/.config/autostart/
```

This launches Kitty minimized at desktop login so it is ready when you press the shortcut.

> [!NOTE]
> For non-systemd environments where Kitty was not autostarted on login, the script will attempt a fallback launch using KRunner when the shortcut is pressed. Please note that this fallback method has not been tested by the author.

**Note on Terminal Choice:** This project is built specifically for **Kitty** because it supports native **[Kittens (Python scripts)](https://sw.kovidgoyal.net/kitty/kittens/custom/)**. This allows us to handle complex window behaviors—like the "Smart EOF" logic—directly within the terminal's internal API, which is not possible with standard emulators.

### System Tray Integration (Optional)

An optional system tray icon application (`kitty_tray.py`) is provided for users who prefer toggling the terminal via a tray icon in their KDE Plasma Panel.

> [!NOTE]
> The system tray autostart entry (`kitty-tray-autostart.desktop`) references the default KPackage install path (`~/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/`). It will only work with user-level installs via `kpackagetool6`. If you have installed the script system-wide, you will need to edit the `Exec` line in the copied `.desktop` file to point to the correct location.

#### Prerequisites
`kitty_tray.py` requires **Python 3** and **PyQt6**:
- **Fedora / RHEL**: `sudo dnf install python3-pyqt6`
- **Arch Linux / Manjaro**: `sudo pacman -S python-pyqt6`
- **Ubuntu / Debian**: `sudo apt install python3-pyqt6`
- **openSUSE**: `sudo zypper install python3-PyQt6`

#### Enabling the System Tray Icon
To have the system tray icon start automatically upon desktop login, link the provided autostart desktop entry:

```bash
./setup.sh tray
```

`setup.sh tray` links both `kitty_tray.py` into the KWin scripts directory and `kitty-tray-autostart.desktop` into `~/.config/autostart/`.

> [!NOTE]
> After `kpackagetool6 --upgrade` reinstalls the package, `kitty_tray.py` is recreated as a regular file (breaking the symlink), so re-run `./setup.sh tray`.

If you prefer not to use the script, link the files by hand:

```bash
ln -sf "$(pwd)/kitty_tray.py" ~/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/
ln -sf "$(pwd)/kitty-tray-autostart.desktop" ~/.config/autostart/
```

Left-clicking the tray icon toggles the drop-down terminal (and auto-launches Kitty if not currently running). Right-clicking opens a context menu with:

- **Toggle Kitty** — show/hide the drop-down terminal (same as left-click).
- **Settings...** — open the tray settings dialog (see below).
- **Exit** — quit the tray application.

#### Tray Settings Dialog

The **Settings...** entry opens a dialog mirroring the KWin script's configuration page ([Configuration Options & Defaults](#configuration-options--defaults)) — window geometry, per-screen overrides, and re-center behavior — without opening System Settings.

Clicking **Apply** (or **OK**):

1. Writes the values to `kwinrc` under `[Script-org.kde.kitty-dropdown-plasma]` via `kwriteconfig6`.
2. Refreshes KWin's script configuration (`org.kde.kwin.Scripting.start()`) so the running script reads the new values.
3. Reloads the KWin script, re-applying the geometry to the current window immediately — the drop-down resizes in place, with no logout or manual script re-enable required.

---

## 3. Window Positioning & Configuration

By default, **no manual KDE Window Rules are required**. The KWin script natively strips window borders and dynamically calculates optimal positioning (**72% screen width**, **78% screen height**, 1px top offset) on any active display, automatically adjusting for multi-monitor setups, high-DPI scaling, and top Plasma panel offsets.

### Graphical Configuration System (Plasma 6)

The script includes a native KDE configuration interface accessible directly in system settings:

1. Open **System Settings > Window Management > KWin Scripts**.
2. Locate **Kitty Drop-Down Plasma**.
3. Click the **Configure (Gear Icon)** button next to it.
4. Adjust your preferred ratios or per-screen settings, then click **Apply**.

> [!NOTE]
> **Wayland Initial Pointer Tracking:** Right after logging in to KDE Plasma Wayland—before moving your physical mouse—KWin reports the active screen based on initial Plasma session startup focus. Moving your mouse pointer even 1 pixel updates KWin's active screen tracker to the display containing your cursor for all subsequent toggles.

---

### Configuration Options & Defaults

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **`widthRatio`** | Double | `0.72` | Screen width percentage ($0.10 \dots 1.00$, where `0.72` = 72% of screen width). |
| **`heightRatio`** | Double | `0.78` | Screen height percentage ($0.10 \dots 1.00$, where `0.78` = 78% of screen height). |
| **`yOffset`** | Integer | `1` | Top-edge offset in pixels from the top of the monitor. |
| **`customWidth`** | Integer | `0` | Explicit width in pixels (`0` = use `widthRatio`). |
| **`customHeight`** | Integer | `0` | Explicit height in pixels (`0` = use `heightRatio`). |
| **`screenOverrides`** | String (JSON) | `""` | Per-monitor JSON overrides keyed by output name. |
| **`recenterOnShow`** | Bool | `false` | Re-apply the default position every time the window is shown (`false` keeps a manually moved position across toggles). |

---

### Finding Monitor Output Names (`kscreen-doctor`)

To find the exact output names of your connected displays (e.g. `eDP-1`, `HDMI-A-1`, `DP-1`), run:

```bash
kscreen-doctor -o
```

Look for lines starting with `Output: 1 eDP-1` or `Output: 2 HDMI-A-1`.

---

### Per-Screen Overrides (`screenOverrides`)

The `screenOverrides` setting accepts a JSON object mapping monitor names to custom settings:

* **Explicit Pixels on Laptop Screen (`eDP-1`):**
  ```json
  {"eDP-1": {"width": 1286, "height": 705}}
  ```
* **Different Ratios for Laptop (`eDP-1`) and External Monitor (`HDMI-A-1`):**
  ```json
  {"eDP-1": {"widthRatio": 0.80, "heightRatio": 0.70}, "HDMI-A-1": {"widthRatio": 0.72, "heightRatio": 0.78}}
  ```
* **Mixing Explicit Pixels and Dynamic Ratios:**
  ```json
  {"eDP-1": {"width": 1286, "height": 705}, "HDMI-A-1": {"widthRatio": 0.75, "heightRatio": 0.80, "yOffset": 2}}
  ```

---

### Command-Line Configuration (`~/.config/kwinrc`)

For dotfile managers or command-line configuration, settings can be set via `kwriteconfig6`:

```bash
# Set a custom global width ratio
kwriteconfig6 --file kwinrc --group Script-org.kde.kitty-dropdown-plasma --key widthRatio 0.80

# Set per-monitor JSON overrides
kwriteconfig6 --file kwinrc --group Script-org.kde.kitty-dropdown-plasma --key screenOverrides '{"eDP-1": {"width": 1286, "height": 705}}'

# Always re-center the window on show
kwriteconfig6 --file kwinrc --group Script-org.kde.kitty-dropdown-plasma --key recenterOnShow true

# Apply changes instantly
qdbus6 org.kde.KWin /KWin reconfigure
```

> [!NOTE]
> **Applying config changes.** KWin caches `kwinrc` in memory, so run `reconfigure` after editing the file so the running script reads the new values. The window geometry is only re-applied when the script re-runs its setup, so to see the change immediately reload the script — toggle it off/on in **System Settings > Window Management > KWin Scripts**, log out and back in, or use the tray's **Settings...** dialog, which writes, refreshes, and reloads automatically.

---

### Customizing Toggle Animations & Desktop Effects

Show/hide transitions for drop-down windows are managed natively by KDE Plasma's C++ GPU Desktop Effects engine:

- **Desktop Effects**: Window state animations (such as **Slide**, **Squish**, or **Scale**) can be configured in **System Settings > Animations** (or **System Settings > Desktop Effects** in earlier Plasma versions).
- **Animation Speed**: Global animation speed can be adjusted via the speed slider in **System Settings > Animations** (or **System Settings > Desktop Effects**).

### Known Limitation: One-Frame Flicker on Multi-Monitor Toggles

When the drop-down is toggled open onto a **different monitor** than the one it was last shown on, the window may appear for a single frame on the previous monitor before appearing on the active one. This affects only cross-monitor toggles; toggling on the same monitor is unaffected.

The cause is KWin window-manager behavior: geometry changes applied to a **minimized** window are deferred by KWin and only applied after the window is unminimized, so the window maps for one frame at its previous position before moving. KWin's scripting API offers no way to suppress this per-window transition, so it cannot be avoided from the script while the window is hidden by minimizing.

The flicker is purely cosmetic — window content and final position are unaffected. This script intentionally avoids alternative hiding strategies (such as keeping the window mapped and parked off-screen) because they keep the window composited and rendering at all times, consuming CPU/GPU while hidden. If this limitation matters for your setup, a configurable off-screen hiding mode is a candidate future enhancement.

---

## 4. Smart EOF (Ctrl+D) Handling

To prevent the drop-down window from closing when the last tab receives an EOF (`Ctrl+D`), this project provides a Python kitten that manages window state natively.

### Installation
1. Link `dropdown_manager.py` to your kitty configuration directory:
```bash
./setup.sh kitten
```

If you prefer not to use the script, link the file by hand:

```bash
ln -sf "$(pwd)/dropdown_manager.py" ~/.config/kitty/
```

2. Add the following mapping to your `kitty-dropdown.conf`:
```conf
map ctrl+d kitten dropdown_manager.py
```

### How it Works

Unlike standard shell bindings, this script is process-aware:

* **Local Shell:** If you are at a local prompt, `Ctrl+D` will **minimize** the window if it's the last tab, or **close** the tab if others are open.
* **SSH & Apps:** If you are running `ssh`, `python`, `vim`, or other interactive tools, it sends a standard EOF signal, allowing the program to exit normally without minimizing your terminal.

---

## 5. Usage

* **Toggle Terminal:** Press `Meta+F12` to slide the terminal in and out of view.


* **Rebind Shortcut:** Change the hotkey in **System Settings > Keyboard > Shortcuts > System Services > Window Management** under **"Toggle Kitty Drop-Down"**.
