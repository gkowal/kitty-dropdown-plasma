"""Regression test for the v1.7-followup Ctrl+D regression: kitty's
Window exposes its tab only via `.tabref()` (there is no `.tab`
attribute), so tab resolution must use it. A window shaped like the
real API must reach tab handling; a detached one (tabref() is None)
must abort without touching anything."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import (
    FakeBoss,
    FakeTab,
    RealShapeWindow,
    dropdown_manager,
)


def shell_fg(exe="bash"):
    return [{"cmdline": ["/bin/" + exe]}]


class TabrefResolutionTest(unittest.TestCase):
    def setUp(self):
        self._orig_shortcut = dropdown_manager._invoke_shortcut
        dropdown_manager._invoke_shortcut = lambda name: False

    def tearDown(self):
        dropdown_manager._invoke_shortcut = self._orig_shortcut

    def test_real_shaped_window_reaches_tab_logic(self):
        tab = FakeTab()
        window = RealShapeWindow(fg=shell_fg(), tab=tab)
        self.assertFalse(hasattr(window, "tab"))
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(boss.close_tab_calls, 1)
        self.assertIs(boss.closed_tab, tab)
        self.assertEqual(window.written, [])

    def test_real_shaped_last_tab_hides_without_destroying(self):
        window = RealShapeWindow(fg=shell_fg(), tab=FakeTab())
        boss = FakeBoss(window=window, tabs_in_window=1)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(boss.close_os_window_calls, 0)

    def test_detached_window_aborts_silently(self):
        window = RealShapeWindow(fg=shell_fg(), tab=None)
        boss = FakeBoss(window=window, tabs_in_window=2)
        boss.active_window = RealShapeWindow(fg=shell_fg(), tab=FakeTab())
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(window.written, [])

    def test_window_without_tabref_aborts(self):
        window = RealShapeWindow(fg=shell_fg(), tab=FakeTab())
        window.tabref = None
        boss = FakeBoss(window=window, tabs_in_window=2)
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        self.assertEqual(boss.close_tab_calls, 0)


if __name__ == "__main__":
    unittest.main()
