"""Regression test for AUDIT-008: the KWin script path must resolve next
to kitty_tray.py (clone / store / system-wide layouts), falling back to
the user-local KPackage path only when no shipped main.js is present."""
import os
import sys
import types
import unittest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)


def _load_tray_as(name, path):
    added = [mod for mod in ("PyQt6", "PyQt6.QtCore", "PyQt6.QtDBus",
                             "PyQt6.QtGui", "PyQt6.QtWidgets")
             if mod not in sys.modules]
    for mod in added:
        sys.modules[mod] = types.ModuleType(mod)
    qtcore = sys.modules["PyQt6.QtCore"]
    if not hasattr(qtcore, "QLockFile"):
        qtcore.QLockFile = type("QLockFile", (), {})
    qtdbus = sys.modules["PyQt6.QtDBus"]
    if not hasattr(qtdbus, "QDBusConnection"):
        qtdbus.QDBusConnection = type("QDBusConnection", (), {})
    if not hasattr(qtdbus, "QDBusMessage"):
        qtdbus.QDBusMessage = type("QDBusMessage", (), {})
    qtgui = sys.modules["PyQt6.QtGui"]
    if not hasattr(qtgui, "QIcon"):
        qtgui.QIcon = type("QIcon", (), {})
    qtwidgets = sys.modules["PyQt6.QtWidgets"]
    for attr in ("QApplication", "QCheckBox", "QDialog", "QDialogButtonBox",
                 "QDoubleSpinBox", "QFormLayout", "QLineEdit", "QMenu",
                 "QSpinBox", "QSystemTrayIcon"):
        if not hasattr(qtwidgets, attr):
            setattr(qtwidgets, attr, type(attr, (), {}))
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    def _cleanup():
        sys.modules.pop(name, None)
        for mod in added:
            sys.modules.pop(mod, None)
    unittest.addModuleCleanup(_cleanup)
    return module


tray = _load_tray_as("kitty_tray_under_test",
                     os.path.join(REPO_ROOT, "kitty_tray.py"))


class ScriptPathTest(unittest.TestCase):
    def test_resolves_next_to_module(self):
        expected = os.path.join(REPO_ROOT, "contents", "code", "main.js")
        self.assertEqual(tray.KWN_SCRIPT_PATH, expected)

    def test_falls_back_without_shipped_main_js(self):
        orig = tray.__file__
        try:
            tray.__file__ = os.path.join("/nonexistent-tray-dir", "kitty_tray.py")
            self.assertEqual(tray._default_script_path(),
                             tray._user_script_path())
        finally:
            tray.__file__ = orig

    def test_relocated_tree_resolves_inside_tree(self):
        import shutil
        import tempfile
        tmp = tempfile.mkdtemp()
        try:
            pkg = os.path.join(tmp, "pkg")
            target = os.path.join(pkg, "contents", "code")
            os.makedirs(target)
            shutil.copy(os.path.join(REPO_ROOT, "contents", "code", "main.js"),
                        os.path.join(target, "main.js"))
            orig = tray.__file__
            try:
                tray.__file__ = os.path.join(pkg, "kitty_tray.py")
                self.assertEqual(tray._default_script_path(),
                                 os.path.join(target, "main.js"))
            finally:
                tray.__file__ = orig
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
