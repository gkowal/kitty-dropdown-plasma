"""Regression test for AUDIT-015: tray robustness gaps.

Covers: missing kread/kwriteconfig6 degrades to a failed result (no
traceback, readers fall back to defaults); loadScript with a
non-numeric reply fails gracefully instead of raising TypeError;
the single-instance lock path is per-user on the /tmp fallback;
the unload poll keeps pumping Qt events.
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_tray_008 import _load_tray_as  # noqa: F401  (reuses PyQt6 stubs)

import kitty_tray_under_test as tray_mod  # noqa: E402  (loaded by test_tray_008)


class _StubMessageIcon:
    Warning = 1
    Information = 2


if not hasattr(tray_mod.QSystemTrayIcon, "MessageIcon"):
    tray_mod.QSystemTrayIcon.MessageIcon = _StubMessageIcon

if not hasattr(tray_mod.QApplication, "processEvents"):
    tray_mod.QApplication.processEvents = staticmethod(lambda *a, **k: None)


class FakeReply:
    def __init__(self, args):
        self._args = args

    def arguments(self):
        return self._args


class FakeTray:
    def __init__(self):
        self.messages = []

    def showMessage(self, *args):
        self.messages.append(args)


class ConfigToolTest(unittest.TestCase):
    def test_missing_tool_returns_failed_result(self):
        with mock.patch.object(tray_mod.shutil, "which", return_value=None):
            proc = tray_mod._config_tool("kwriteconfig6", "--key", "k")
        self.assertEqual(proc.returncode, 127)
        self.assertIn("kwriteconfig6", proc.stderr)

    def test_missing_reader_falls_back_to_default(self):
        with mock.patch.object(tray_mod.shutil, "which", return_value=None):
            self.assertEqual(
                tray_mod._read_option("widthRatio", "0.72"), "0.72")

    def test_truly_missing_binary_degrades(self):
        # No mocks: with the real PATH lookup this name cannot exist, so
        # the pre-fix code raised FileNotFoundError while the fixed code
        # returns a failed result.
        proc = tray_mod._config_tool("definitely-not-a-real-tool-xyz",
                                     "--key", "k")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("definitely-not-a-real-tool-xyz", proc.stderr)

    def test_exec_failure_degrades(self):
        # Tool resolves but cannot be executed.
        with mock.patch.object(tray_mod.shutil, "which",
                               return_value="/usr/bin/kwriteconfig6"), \
             mock.patch.object(tray_mod.subprocess, "run",
                               side_effect=FileNotFoundError("noexec")):
            proc = tray_mod._config_tool("kwriteconfig6", "--key", "k")
        self.assertEqual(proc.returncode, 127)

    def test_present_tool_still_invoked(self):
        with mock.patch.object(tray_mod.shutil, "which",
                               return_value="/usr/bin/kreadconfig6"), \
             mock.patch.object(tray_mod.subprocess, "run") as run:
            tray_mod._config_tool("kreadconfig6", "--key", "k")
            run.assert_called_once()


class ReloadScriptTest(unittest.TestCase):
    def _run_reload(self, load_args):
        calls = []
        state = {"loaded": True}

        def fake_dbus(tray, path, interface, method, args=()):
            calls.append(method)
            if method == "isScriptLoaded":
                # Loaded on first check, gone after the unload.
                loaded = state["loaded"]
                state["loaded"] = False
                return FakeReply([loaded])
            if method == "unloadScript":
                return FakeReply([True])
            if method == "loadScript":
                return FakeReply(load_args)
            if method == "run":
                return FakeReply([])
            if method == "start":
                return FakeReply([])
            raise AssertionError(f"unexpected {method}")

        with mock.patch.object(tray_mod, "_dbus_call",
                               side_effect=fake_dbus):
            result = tray_mod._reload_kwin_script(FakeTray())
        return result, calls

    def test_non_numeric_script_id_fails_gracefully(self):
        result, calls = self._run_reload(["oops"])
        self.assertFalse(result)
        self.assertIn("loadScript", calls)
        self.assertNotIn("run", calls)

    def test_negative_script_id_fails(self):
        result, _ = self._run_reload([-1])
        self.assertFalse(result)

    def test_numeric_script_id_proceeds_to_run(self):
        result, calls = self._run_reload([3])
        self.assertTrue(result)
        self.assertIn("run", calls)

    def test_unload_wait_pumps_qt_events(self):
        pumped = []
        polls = {"n": 0}

        def fake_dbus(tray, path, interface, method, args=()):
            if method == "isScriptLoaded":
                # Stay loaded for two polls so the wait loop iterates.
                polls["n"] += 1
                return FakeReply([polls["n"] <= 2])
            if method == "unloadScript":
                return FakeReply([True])
            if method == "loadScript":
                return FakeReply([3])
            if method == "run":
                return FakeReply([])
            raise AssertionError(f"unexpected {method}")

        with mock.patch.object(tray_mod, "_dbus_call",
                               side_effect=fake_dbus), \
             mock.patch.object(tray_mod.QApplication, "processEvents",
                               side_effect=lambda *a, **k: pumped.append(1)), \
             mock.patch.object(tray_mod.time, "sleep", return_value=None):
            result = tray_mod._reload_kwin_script(FakeTray())
        self.assertTrue(result)
        self.assertTrue(pumped, "wait loop must pump Qt events")


class LockPathTest(unittest.TestCase):
    def test_xdg_path_unchanged(self):
        with mock.patch.dict(os.environ, {"XDG_RUNTIME_DIR": "/run/user/1000"}):
            self.assertEqual(tray_mod._tray_lock_path(),
                             "/run/user/1000/kitty-dropdown-tray.lock")

    def test_tmp_fallback_carries_uid(self):
        env = {k: v for k, v in os.environ.items() if k != "XDG_RUNTIME_DIR"}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(tray_mod.os, "getuid", return_value=1001,
                               create=True):
            self.assertEqual(tray_mod._tray_lock_path(),
                             "/tmp/kitty-dropdown-tray-1001.lock")

    def test_unload_poll_pumps_events(self):
        import inspect
        src = inspect.getsource(tray_mod._reload_kwin_script)
        loop = src[src.index("for _ in range(50)"):]
        self.assertIn("processEvents", loop)

    def test_apply_aborts_with_no_writes_without_tools(self):
        dialog = self._fake_dialog()
        runs = []
        with mock.patch.object(tray_mod.shutil, "which", return_value=None), \
             mock.patch.object(tray_mod.subprocess, "run",
                               side_effect=lambda *a, **k: runs.append(a)):
            result = tray_mod.SettingsDialog._apply(dialog)
        self.assertFalse(result)
        self.assertEqual(runs, [])
        self.assertTrue(dialog.tray.messages)

    class _FakeField:
        def __init__(self, value):
            self._value = value

        def text(self):
            return self._value

        def value(self):
            return self._value

        def isChecked(self):
            return self._value

    class _FakeDialogTray:
        def __init__(self):
            self.messages = []

        def showMessage(self, *args):
            self.messages.append(args)

    def _fake_dialog(self):
        dialog = object.__new__(tray_mod.SettingsDialog)
        dialog.screen_overrides = self._FakeField("")
        dialog.width_ratio = self._FakeField(0.72)
        dialog.height_ratio = self._FakeField(0.78)
        dialog.y_offset = self._FakeField(1)
        dialog.custom_width = self._FakeField(0)
        dialog.custom_height = self._FakeField(0)
        dialog.recenter_on_show = self._FakeField(False)
        dialog.tray = self._FakeDialogTray()
        return dialog


if __name__ == "__main__":
    unittest.main()
