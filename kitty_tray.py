#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from PyQt6.QtCore import QLockFile
from PyQt6.QtDBus import QDBusConnection, QDBusMessage
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMenu,
    QSpinBox,
    QSystemTrayIcon,
)

KCFG_GROUP = "Script-org.kde.kitty-dropdown-plasma"
KWN_SCRIPT_PLUGIN = "org.kde.kitty-dropdown-plasma"
KWN_SCRIPT_PATH = os.path.join(
    os.path.expanduser("~"),
    ".local",
    "share",
    "kwin",
    "scripts",
    "org.kde.kitty-dropdown-plasma",
    "contents",
    "code",
    "main.js",
)

def _shortcut_exists():
    msg = QDBusMessage.createMethodCall(
        "org.kde.kglobalaccel",
        "/component/kwin",
        "org.kde.kglobalaccel.Component",
        "allShortcutInfos"
    )
    reply = QDBusConnection.sessionBus().call(msg)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        return None
    infos = reply.arguments()
    if not infos or not isinstance(infos[0], list):
        return None
    for info in infos[0]:
        if isinstance(info, (tuple, list)) and info:
            try:
                if str(info[0]) == "Toggle Kitty":
                    return True
            except Exception:
                pass
    return False

def toggle_kitty(tray):
    exists = _shortcut_exists()
    if exists is False:
        msg = "The 'Toggle Kitty' shortcut is not registered - is the KWin script loaded/enabled?"
        print(f"kitty_tray: {msg}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.MessageIcon.Warning, 5000)
        return
    msg = QDBusMessage.createMethodCall(
        "org.kde.kglobalaccel",
        "/component/kwin",
        "org.kde.kglobalaccel.Component",
        "invokeShortcut"
    )
    msg.setArguments(["Toggle Kitty"])
    reply = QDBusConnection.sessionBus().call(msg)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        err = f"{reply.errorName()}: {reply.errorMessage()}"
        print(f"kitty_tray: toggle failed: {err}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", f"Failed to toggle: {err}", QSystemTrayIcon.MessageIcon.Warning, 5000)

def _config_tool(tool, *args):
    return subprocess.run(
        [tool, "--file", "kwinrc", "--group", KCFG_GROUP, *args],
        capture_output=True,
        text=True,
    )

def _read_option(key, default):
    proc = _config_tool("kreadconfig6", "--key", key)
    if proc.returncode != 0:
        return default
    value = proc.stdout.strip()
    return value if value else default

def _write_option(key, value, type_=None):
    args = ["--key", key]
    if type_:
        args += ["--type", type_]
    args.append(str(value))
    return _config_tool("kwriteconfig6", *args)

def _parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def _parse_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _refresh_kwin_scripts(tray):
    return _dbus_call(tray, "/Scripting", "org.kde.kwin.Scripting", "start") is not None

def _dbus_call(tray, path, interface, method, args=()):
    msg = QDBusMessage.createMethodCall(
        "org.kde.KWin",
        path,
        interface,
        method,
    )
    if args:
        msg.setArguments(list(args))
    reply = QDBusConnection.sessionBus().call(msg)
    if reply.type() == QDBusMessage.MessageType.ErrorMessage:
        err = f"{reply.errorName()}: {reply.errorMessage()}"
        print(f"kitty_tray: {method} failed: {err}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", f"Failed to reload script: {err}", QSystemTrayIcon.MessageIcon.Warning, 5000)
        return None
    return reply

def _reload_kwin_script(tray):
    reply = _dbus_call(tray, "/Scripting", "org.kde.kwin.Scripting", "isScriptLoaded", [KWN_SCRIPT_PLUGIN])
    if reply is None:
        return False
    if not reply.arguments() or reply.arguments()[0] != True:
        msg = "The KWin script is not loaded - is it enabled?"
        print(f"kitty_tray: {msg}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.MessageIcon.Warning, 5000)
        return False

    reply = _dbus_call(tray, "/Scripting", "org.kde.kwin.Scripting", "unloadScript", [KWN_SCRIPT_PLUGIN])
    if reply is None:
        return False
    if not reply.arguments() or reply.arguments()[0] != True:
        msg = "Failed to unload the KWin script"
        print(f"kitty_tray: {msg}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.MessageIcon.Warning, 5000)
        return False

    for _ in range(50):
        reply = _dbus_call(tray, "/Scripting", "org.kde.kwin.Scripting", "isScriptLoaded", [KWN_SCRIPT_PLUGIN])
        if reply is None:
            return False
        if not reply.arguments() or reply.arguments()[0] != True:
            break
        time.sleep(0.02)
    else:
        msg = "Timed out unloading the KWin script"
        print(f"kitty_tray: {msg}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.MessageIcon.Warning, 5000)
        return False

    reply = _dbus_call(tray, "/Scripting", "org.kde.kwin.Scripting", "loadScript", [KWN_SCRIPT_PATH, KWN_SCRIPT_PLUGIN])
    if reply is None:
        return False
    if not reply.arguments() or reply.arguments()[0] < 0:
        msg = "Failed to load the KWin script"
        print(f"kitty_tray: {msg}", file=sys.stderr)
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.MessageIcon.Warning, 5000)
        return False
    script_id = reply.arguments()[0]

    reply = _dbus_call(tray, f"/Scripting/Script{script_id}", "org.kde.kwin.Script", "run")
    if reply is None:
        return False
    return True

class SettingsDialog(QDialog):
    def __init__(self, tray, parent=None):
        super().__init__(parent)
        self.tray = tray
        self.setWindowTitle("Kitty Dropdown Settings")
        self.setMinimumWidth(360)

        form = QFormLayout(self)

        self.width_ratio = QDoubleSpinBox()
        self.width_ratio.setRange(0.10, 1.00)
        self.width_ratio.setSingleStep(0.05)
        self.width_ratio.setDecimals(2)

        self.height_ratio = QDoubleSpinBox()
        self.height_ratio.setRange(0.10, 1.00)
        self.height_ratio.setSingleStep(0.05)
        self.height_ratio.setDecimals(2)

        self.y_offset = QSpinBox()
        self.y_offset.setRange(0, 500)

        self.custom_width = QSpinBox()
        self.custom_width.setRange(0, 10000)

        self.custom_height = QSpinBox()
        self.custom_height.setRange(0, 10000)

        self.screen_overrides = QLineEdit()
        self.screen_overrides.setPlaceholderText('{"eDP-1": {"width": 1286, "height": 705}}')

        self.recenter_on_show = QCheckBox("Re-center window on show")

        form.addRow("Width Ratio (0.1 - 1.0):", self.width_ratio)
        form.addRow("Height Ratio (0.1 - 1.0):", self.height_ratio)
        form.addRow("Top Offset (pixels):", self.y_offset)
        form.addRow("Custom Width (0 = use ratio):", self.custom_width)
        form.addRow("Custom Height (0 = use ratio):", self.custom_height)
        form.addRow("Per-Screen Overrides (JSON):", self.screen_overrides)
        form.addRow(self.recenter_on_show)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._apply_and_accept)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)
        form.addRow(buttons)

        self._load()

    def _load(self):
        self.width_ratio.setValue(_parse_float(_read_option("widthRatio", "0.72"), 0.72))
        self.height_ratio.setValue(_parse_float(_read_option("heightRatio", "0.78"), 0.78))
        self.y_offset.setValue(_parse_int(_read_option("yOffset", "1"), 1))
        self.custom_width.setValue(_parse_int(_read_option("customWidth", "0"), 0))
        self.custom_height.setValue(_parse_int(_read_option("customHeight", "0"), 0))
        self.screen_overrides.setText(_read_option("screenOverrides", ""))
        self.recenter_on_show.setChecked(_read_option("recenterOnShow", "false") == "true")

    def _apply(self):
        writes = [
            ("widthRatio", None, str(self.width_ratio.value())),
            ("heightRatio", None, str(self.height_ratio.value())),
            ("yOffset", None, str(self.y_offset.value())),
            ("customWidth", None, str(self.custom_width.value())),
            ("customHeight", None, str(self.custom_height.value())),
            ("screenOverrides", None, self.screen_overrides.text()),
            ("recenterOnShow", "bool", "true" if self.recenter_on_show.isChecked() else "false"),
        ]
        for key, type_, value in writes:
            proc = _write_option(key, value, type_)
            if proc.returncode != 0:
                err = f"kwriteconfig6 failed ({proc.returncode}) writing {key}"
                print(f"kitty_tray: {err}", file=sys.stderr)
                self.tray.showMessage("Kitty Dropdown", err, QSystemTrayIcon.MessageIcon.Warning, 5000)
                return False
        if not _refresh_kwin_scripts(self.tray):
            return False
        if not _reload_kwin_script(self.tray):
            return False
        self.tray.showMessage("Kitty Dropdown", "Settings applied", QSystemTrayIcon.MessageIcon.Information, 3000)
        return True

    def _apply_and_accept(self):
        if self._apply():
            self.accept()

def main():
    lock_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    lock = QLockFile(os.path.join(lock_dir, "kitty-dropdown-tray.lock"))
    if not lock.tryLock(100):
        print("kitty_tray: another instance is already running", file=sys.stderr)
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon = QIcon.fromTheme("utilities-terminal")
    if icon.isNull():
        icon = QIcon.fromTheme("terminal")
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Toggle Kitty Dropdown")
    tray.activated.connect(
        lambda reason: toggle_kitty(tray) if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )

    menu = QMenu()
    toggle_action = menu.addAction("Toggle Kitty")
    toggle_action.triggered.connect(lambda: toggle_kitty(tray))
    menu.addSeparator()
    settings_action = menu.addAction("Settings...")
    settings_action.triggered.connect(lambda: SettingsDialog(tray).exec())
    menu.addSeparator()
    quit_action = menu.addAction("Exit")
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)

    tray.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
