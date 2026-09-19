"""Regression test for AUDIT-013: login shells (`-zsh`, `-bash`) must
classify as shells; versioned app binaries and wrappers must stay
non-shell (forwarding Ctrl+D there is the safe direction)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import FakeBoss, FakeTab, FakeWindow, dropdown_manager


class ShellNameTest(unittest.TestCase):
    def setUp(self):
        self._orig_shortcut = dropdown_manager._invoke_shortcut

    def tearDown(self):
        dropdown_manager._invoke_shortcut = self._orig_shortcut

    def test_login_shell_names(self):
        self.assertEqual(dropdown_manager._shell_exe_name("-zsh"), "zsh")
        self.assertEqual(dropdown_manager._shell_exe_name("-bash"), "bash")
        self.assertEqual(dropdown_manager._shell_exe_name("/bin/-sh"), "sh")

    def test_plain_names_unchanged(self):
        self.assertEqual(dropdown_manager._shell_exe_name("/bin/bash"), "bash")
        self.assertEqual(dropdown_manager._shell_exe_name("fish"), "fish")
        self.assertEqual(dropdown_manager._shell_exe_name("python3"), "python3")
        self.assertEqual(dropdown_manager._shell_exe_name("sudo"), "sudo")
        # Degenerate dashes stay non-shell (safe forward direction).
        self.assertEqual(dropdown_manager._shell_exe_name("-"), "")
        self.assertEqual(dropdown_manager._shell_exe_name("--"), "-")

    def test_login_shell_reaches_tab_logic(self):
        window = FakeWindow(fg=[{"cmdline": ["-zsh"]}], tab=FakeTab())
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager._invoke_shortcut = lambda name: False
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(window.written, [])
        self.assertEqual(boss.close_tab_calls, 1)

    def test_wrapper_still_forwards(self):
        window = FakeWindow(fg=[{"cmdline": ["sudo", "vim"]}], tab=FakeTab())
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager._invoke_shortcut = lambda name: False
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(window.written, ["\x04"])
        self.assertEqual(boss.close_tab_calls, 0)


if __name__ == "__main__":
    unittest.main()
