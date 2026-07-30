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

#### Method A: On-Demand Systemd Service (Recommended)

If your Linux distribution uses `systemd` user sessions (Fedora, Arch, Manjaro, openSUSE, Ubuntu, Debian, etc.), we strongly recommend using the provided systemd service:

```bash
mkdir -p ~/.config/systemd/user/
cp kitty-dropdown.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

**Why this is preferred:**
- **Zero Resource Overhead at Boot:** Kitty is **not** launched at desktop startup, consuming 0 RAM and CPU.
- **On-Demand Activation:** The first time you press the toggle shortcut (`Meta+F12`), the KWin script automatically starts the service via D-Bus.
- **Self-Healing:** If Kitty crashes or is closed, pressing the shortcut automatically re-launches it on demand.

#### Method B: Traditional Autostart File (Non-Systemd Environments)

If your system does not use `systemd` user sessions (e.g., Devuan, Gentoo/OpenRC, Void, Artix), you can launch Kitty automatically on desktop login using the provided `.desktop` file:

```bash
cp kitty-autostart.desktop ~/.config/autostart/
```

This launches Kitty minimized at desktop login so it is ready when you press the shortcut.

> [!NOTE]
> For non-systemd environments where Kitty was not autostarted on login, the script will attempt a fallback launch using KRunner when the shortcut is pressed. Please note that this fallback method has not been tested by the author.

**Note on Terminal Choice:** This project is built specifically for **Kitty** because it supports native **[Kittens (Python scripts)](https://sw.kovidgoyal.net/kitty/kittens/custom/)**. This allows us to handle complex window behaviors—like the "Smart EOF" logic—directly within the terminal's internal API, which is not possible with standard emulators.

### System Tray Integration (Optional)

An optional system tray icon application (`kitty_tray.py`) is provided for users who prefer toggling the terminal via a tray icon in their KDE Plasma Panel.

#### Prerequisites
`kitty_tray.py` requires **Python 3** and **PyQt6**:
- **Fedora / RHEL**: `sudo dnf install python3-pyqt6`
- **Arch Linux / Manjaro**: `sudo pacman -S python-pyqt6`
- **Ubuntu / Debian**: `sudo apt install python3-pyqt6`
- **openSUSE**: `sudo zypper install python3-PyQt6`

#### Enabling the System Tray Icon
To have the system tray icon start automatically upon desktop login, copy the provided autostart desktop entry:

```bash
cp ~/.local/share/kwin/scripts/org.kde.kitty-dropdown-plasma/kitty-tray-autostart.desktop ~/.config/autostart/
```

Left-clicking the tray icon toggles the drop-down terminal (and auto-launches Kitty if not currently running). Right-clicking opens a context menu with options to toggle or exit the tray application.

---

## 3. Window Positioning & Custom Overrides

By default, **no manual KDE Window Rules are required**. The KWin script natively strips window borders and dynamically calculates optimal positioning (**72% screen width**, **78% screen height**, 1px top offset) on any active display, automatically adjusting for multi-monitor setups, high-DPI scaling, and top Plasma panel offsets.

### Forcing Custom Window Rules (Optional)

If you prefer fixed pixel dimensions or custom placement over the script's default 72%/78% dynamic ratios:

#### Method A: Quick Auto-Capture via Window Menu (Recommended)
1. Press `Meta+F12` to open the Kitty drop-down terminal.
2. Press `Alt+F3` -> **More Actions** -> **Configure Special Window Settings...**.
3. Click **Add Property...** and add **Position** and **Size**.
4. Set both properties to **Force** (or **Force Temporarily**) and enter your preferred pixel coordinates.
5. Click **Apply** and **OK**.

#### Method B: Manual System Settings Rule
1. Navigate to **System Settings > Window Management > Window Rules**.
2. Create a new rule targeting **Window Class (exact match)**: `kitty-dropdown`.
3. Add properties **Position** and **Size**, set both to **Force**, and specify your values.

> [!NOTE]
> Setting **Position** and **Size** to **Force** is required if you want KWin to override the script's default dynamic geometry.

---

## 4. Smart EOF (Ctrl+D) Handling

To prevent the drop-down window from closing when the last tab receives an EOF (`Ctrl+D`), this project provides a Python kitten that manages window state natively.

### Installation
1. Move `dropdown_manager.py` to your kitty configuration directory:
```bash
cp dropdown_manager.py ~/.config/kitty/
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
