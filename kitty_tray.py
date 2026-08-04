#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtDBus import QDBusConnection, QDBusMessage

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
        tray.showMessage("Kitty Dropdown", msg, QSystemTrayIcon.Warning, 5000)
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
        tray.showMessage("Kitty Dropdown", f"Failed to toggle: {err}", QSystemTrayIcon.Warning, 5000)

def main():
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
    toggle_action = menu.addAction("Toggle Drop-Down Terminal")
    toggle_action.triggered.connect(lambda: toggle_kitty(tray))
    menu.addSeparator()
    quit_action = menu.addAction("Exit")
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)

    tray.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
