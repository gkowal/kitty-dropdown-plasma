"""Regression test for AUDIT-010: SettingsDialog must reject invalid
per-screen overrides JSON instead of saving it as a silent no-op."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_tray_008 import _load_tray_as  # noqa: F401  (reuses PyQt6 stubs)

import kitty_tray_under_test as tray_mod  # noqa: E402  (loaded by test_tray_008)


class _StubMessageIcon:
    Warning = 1
    Information = 2


if not hasattr(tray_mod.QSystemTrayIcon, "MessageIcon"):
    tray_mod.QSystemTrayIcon.MessageIcon = _StubMessageIcon


class ValidateOverridesTest(unittest.TestCase):
    def check(self, text, ok):
        result, reason = tray_mod._validate_screen_overrides(text)
        self.assertEqual(result, ok, f"{text!r}: {reason}")

    def test_empty_is_ok(self):
        self.check("", True)
        self.check("   ", True)

    def test_valid_examples_ok(self):
        self.check('{"eDP-1": {"width": 1286, "height": 705}}', True)
        self.check('{"eDP-1": {"widthRatio": 0.8, "heightRatio": 0.7}, '
                   '"HDMI-A-1": {"widthRatio": 0.72, "yOffset": 2}}', True)
        self.check('{"default": {"width": 800, "height": 600}}', True)

    def test_malformed_json_rejected(self):
        self.check("{bad", False)
        self.check('{"eDP-1": }', False)
        self.check("[1, 2]", False)
        self.check('"just a string"', False)
        self.check("42", False)

    def test_wrong_shapes_rejected(self):
        self.check('{"eDP-1": 5}', False)
        self.check('{"eDP-1": [1]}', False)
        self.check('{"eDP-1": {"depth": 3}}', False)

    def test_bad_values_rejected(self):
        self.check('{"eDP-1": {"width": 0}}', False)
        self.check('{"eDP-1": {"height": -5}}', False)
        self.check('{"eDP-1": {"widthRatio": 0}}', False)
        self.check('{"eDP-1": {"heightRatio": -0.5}}', False)
        self.check('{"eDP-1": {"yOffset": -1}}', False)
        self.check('{"eDP-1": {"width": true}}', False)
        self.check('{"eDP-1": {"width": "wide"}}', False)
        self.check('{"eDP-1": {"yOffset": 0}}', True)

    def test_non_finite_rejected(self):
        self.check('{"eDP-1": {"width": NaN}}', False)
        self.check('{"eDP-1": {"width": Infinity}}', False)
        self.check('{"eDP-1": {"width": -Infinity}}', False)
        self.check('{"eDP-1": {"width": 1e400}}', False)
        self.check('{"eDP-1": {"yOffset": NaN}}', False)

    def test_fractional_pixels_rejected(self):
        self.check('{"eDP-1": {"width": 1286.5}}', False)
        self.check('{"eDP-1": {"height": 705.25}}', False)
        self.check('{"eDP-1": {"yOffset": 1.5}}', False)
        self.check('{"eDP-1": {"width": 1286.0}}', True)
        self.check('{"eDP-1": {"widthRatio": 0.725}}', True)

    def test_apply_validates_before_writing(self):
        import inspect
        src = inspect.getsource(tray_mod.SettingsDialog._apply)
        self.assertIn("_validate_screen_overrides", src)
        self.assertLess(src.index("_validate_screen_overrides"),
                        src.index("_write_option"))

    def test_apply_rejects_invalid_without_writing(self):
        dialog = self._fake_dialog('{"eDP-1": {"width": 0}}')
        calls = self._record_writes()
        try:
            self.assertFalse(tray_mod.SettingsDialog._apply(dialog))
            self.assertEqual(calls, [])
            self.assertTrue(dialog.tray.messages)
        finally:
            self._restore_writes()

    def test_apply_accepts_valid_and_writes(self):
        dialog = self._fake_dialog('{"eDP-1": {"width": 1286}}')
        calls = self._record_writes()
        try:
            self.assertTrue(tray_mod.SettingsDialog._apply(dialog))
            self.assertTrue(any(k == "screenOverrides" for k, _, _ in calls))
        finally:
            self._restore_writes()

    class _FakeField:
        def __init__(self, value):
            self._value = value

        def text(self):
            return self._value

        def value(self):
            return self._value

        def isChecked(self):
            return self._value

    class _FakeTray:
        def __init__(self):
            self.messages = []

        def showMessage(self, *args):
            self.messages.append(args)

    def _fake_dialog(self, overrides):
        dialog = object.__new__(tray_mod.SettingsDialog)
        dialog.screen_overrides = self._FakeField(overrides)
        dialog.width_ratio = self._FakeField(0.72)
        dialog.height_ratio = self._FakeField(0.78)
        dialog.y_offset = self._FakeField(1)
        dialog.custom_width = self._FakeField(0)
        dialog.custom_height = self._FakeField(0)
        dialog.recenter_on_show = self._FakeField(False)
        dialog.tray = self._FakeTray()
        return dialog

    def _record_writes(self):
        calls = []

        class _Proc:
            returncode = 0

        def fake_write(key, value, type_=None):
            calls.append((key, value, type_))
            return _Proc()

        self._orig_write = tray_mod._write_option
        self._orig_refresh = tray_mod._refresh_kwin_scripts
        self._orig_reload = tray_mod._reload_kwin_script
        tray_mod._write_option = fake_write
        tray_mod._refresh_kwin_scripts = lambda tray: True
        tray_mod._reload_kwin_script = lambda tray: True
        return calls

    def _restore_writes(self):
        tray_mod._write_option = self._orig_write
        tray_mod._refresh_kwin_scripts = self._orig_refresh
        tray_mod._reload_kwin_script = self._orig_reload


if __name__ == "__main__":
    unittest.main()
