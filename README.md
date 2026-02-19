# Kitty Drop-Down Plasma

**Kitty Drop-Down Plasma** is a productivity-focused KWin script designed for **KDE Plasma 6**. It provides a Quake-style, drop-down terminal experience using the high-performance **Kitty** terminal emulator. This project combines KWin window management logic with shell-level integration to ensure your terminal is always available and protected from accidental closure.

[![kde-store](https://img.shields.io/badge/KDE%20Store-download-blue?logo=KDE)](https://store.kde.org/p/2348115)

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

### Autostart Setup

To have the terminal ready upon login, move the provided `kitty-autostart.desktop` file to your autostart directory:

```bash
cp kitty-autostart.desktop ~/.config/autostart/
```

The `--app-id kitty-dropdown` flag in this file is critical for the KWin script to identify the window.

---

## 3. KDE Window Rules

To ensure the terminal appears borderless and correctly positioned, you must create a Window Rule in **System Settings > Window Management > Window Rules**.

* **Target Window Class:** `kitty kitty-dropdown` 
* **Window Types:** Normal Window 
* **No titlebar and frame:** Force -> Yes 


### Scaling & Dimensions

The positioning depends on your specific monitor resolution and KDE scaling. **Users are highly encouraged to experiment with these values** to find the perfect fit for their specific display environment, especially when using fractional scaling on Wayland. 

| Resolution | Scaling | Recommended Position | Recommended Size |
| --- | --- | --- | --- |
| **3840x2160** | **150%** | `280,1` | `2000,1030` |
| **1920x1080** | **125%** | `125,1` | `1286,705` |

**IMPORTANT**: Both **Position** and **Size** properties must be set to **Force** in the Window Rule settings to prevent the terminal from being automatically resized or moved by KWin.

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
