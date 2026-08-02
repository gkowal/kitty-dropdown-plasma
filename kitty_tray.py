#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtDBus import QDBusConnection, QDBusMessage

def toggle_kitty():
    msg = QDBusMessage.createMethodCall(
        "org.kde.kglobalaccel",
        "/component/kwin",
        "org.kde.kglobalaccel.Component",
        "invokeShortcut"
    )
    msg.setArguments(["Toggle Kitty"])
    QDBusConnection.sessionBus().send(msg)

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon = QIcon.fromTheme("utilities-terminal")
    if icon.isNull():
        icon = QIcon.fromTheme("terminal")
    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Toggle Kitty Dropdown")
    tray.activated.connect(
        lambda reason: toggle_kitty() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
    )

    menu = QMenu()
    toggle_action = menu.addAction("Toggle Drop-Down Terminal")
    toggle_action.triggered.connect(toggle_kitty)
    menu.addSeparator()
    quit_action = menu.addAction("Exit")
    quit_action.triggered.connect(app.quit)
    tray.setContextMenu(menu)

    tray.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
