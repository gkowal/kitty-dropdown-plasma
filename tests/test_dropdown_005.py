"""Regression test for AUDIT-005: a stale target window id must abort
instead of acting on whichever window happens to be active."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import FakeBoss, FakeTab, FakeWindow, dropdown_manager


class StaleTargetTest(unittest.TestCase):
    def setUp(self):
        self._orig_shortcut = dropdown_manager._invoke_shortcut
        self.shortcut_calls = []
        dropdown_manager._invoke_shortcut = self.shortcut_calls.append

    def tearDown(self):
        dropdown_manager._invoke_shortcut = self._orig_shortcut

    def test_unknown_id_ignores_active_window(self):
        active = FakeWindow(fg=[{"cmdline": ["/bin/bash"]}], tab=FakeTab())
        boss = FakeBoss(window=None, tabs_in_window=2)
        boss.active_window = active
        dropdown_manager.handle_result(None, None, 9999, boss)
        self.assertEqual(active.written, [])
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(self.shortcut_calls, [])

    def test_window_without_tab_aborts(self):
        window = FakeWindow(fg=[{"cmdline": ["/bin/bash"]}], tab=None)
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(window.written, [])
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(self.shortcut_calls, [])

    def test_resolved_target_still_works(self):
        window = FakeWindow(fg=[{"cmdline": ["/bin/bash"]}], tab=FakeTab())
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(boss.close_tab_calls, 1)


if __name__ == "__main__":
    unittest.main()
