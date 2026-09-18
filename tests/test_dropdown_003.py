"""Regression test for AUDIT-003: when both KWin hide mechanisms fail on
the last tab, Ctrl+D must not destroy the OS window."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import FakeBoss, FakeTab, FakeWindow, dropdown_manager


def shell_fg(exe="bash"):
    return [{"cmdline": ["/bin/" + exe]}]


class CloseFallbackTest(unittest.TestCase):
    def setUp(self):
        self._orig_shortcut = dropdown_manager._invoke_shortcut

    def tearDown(self):
        dropdown_manager._invoke_shortcut = self._orig_shortcut

    def run_kitten(self, fg, tabs, shortcuts):
        window = FakeWindow(fg=fg, tab=FakeTab())
        boss = FakeBoss(window=window, tabs_in_window=tabs)
        dropdown_manager._invoke_shortcut = lambda name: shortcuts.get(name, False)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        return boss, window

    def test_last_tab_shortcuts_fail_leaves_window_intact(self):
        boss, window = self.run_kitten(
            shell_fg(), 1, {"Window Minimize": False, "Toggle Kitty": False})
        self.assertEqual(boss.close_os_window_calls, 0)
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(window.written, [])

    def test_last_tab_minimize_success_no_further_action(self):
        boss, window = self.run_kitten(
            shell_fg(), 1, {"Window Minimize": True, "Toggle Kitty": True})
        self.assertEqual(boss.close_os_window_calls, 0)
        self.assertEqual(boss.close_tab_calls, 0)

    def test_last_tab_toggle_shortcut_only(self):
        boss, window = self.run_kitten(
            shell_fg(), 1, {"Window Minimize": False, "Toggle Kitty": True})
        self.assertEqual(boss.close_os_window_calls, 0)
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(window.written, [])

    def test_multi_tab_still_closes_tab(self):
        boss, window = self.run_kitten(
            shell_fg(), 2, {"Window Minimize": False, "Toggle Kitty": False})
        self.assertEqual(boss.close_tab_calls, 1)
        self.assertEqual(boss.close_os_window_calls, 0)


if __name__ == "__main__":
    unittest.main()
