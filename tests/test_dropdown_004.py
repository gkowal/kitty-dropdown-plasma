"""Regression test for AUDIT-004: uncertain foreground-process state must
fail safe by forwarding Ctrl+D, never sinking into close/hide logic."""
import os
import sys
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import FakeBoss, FakeTab, FakeWindow, dropdown_manager


class FailSafeForwardTest(unittest.TestCase):
    def setUp(self):
        self._orig_shortcut = dropdown_manager._invoke_shortcut

    def tearDown(self):
        dropdown_manager._invoke_shortcut = self._orig_shortcut

    def run_kitten(self, window, tabs=2):
        boss = FakeBoss(window=window, tabs_in_window=tabs)
        dropdown_manager._invoke_shortcut = lambda name: False
        dropdown_manager.handle_result(None, None, boss.wid, boss)
        return boss

    def assert_forwarded_only(self, window, boss):
        self.assertEqual(window.written, ["\x04"])
        self.assertEqual(boss.close_tab_calls, 0)
        self.assertEqual(boss.close_os_window_calls, 0)

    def test_empty_process_list_forwards(self):
        window = FakeWindow(fg=[], tab=FakeTab())
        self.assert_forwarded_only(window, self.run_kitten(window))

    def test_missing_attribute_forwards(self):
        window = FakeWindow(fg=[], tab=FakeTab())
        del window.child.foreground_processes
        self.assert_forwarded_only(window, self.run_kitten(window))

    def test_none_process_data_forwards(self):
        window = FakeWindow(fg=None, tab=FakeTab())
        window.child.foreground_processes = None
        self.assert_forwarded_only(window, self.run_kitten(window))

    def test_malformed_entries_forward(self):
        for fg in ([{}], [{"cmdline": []}], [{"cmdline": None}],
                   [{"cmdline": [123]}], ["not-a-dict"]):
            with self.subTest(fg=fg):
                window = FakeWindow(fg=fg, tab=FakeTab())
                self.assert_forwarded_only(window, self.run_kitten(window))

    def test_detection_exception_forwards(self):
        class RaisingChild:
            @property
            def foreground_processes(self):
                raise RuntimeError("kitty internals changed")
        window = FakeWindow(fg=[], tab=FakeTab())
        window.child = RaisingChild()
        self.assert_forwarded_only(window, self.run_kitten(window))

    def test_non_shell_forwards(self):
        window = FakeWindow(fg=[{"cmdline": ["ssh", "host"]}], tab=FakeTab())
        self.assert_forwarded_only(window, self.run_kitten(window))

    def test_identified_shell_proceeds_to_tab_logic(self):
        window = FakeWindow(fg=[{"cmdline": ["/bin/bash"]}], tab=FakeTab())
        boss = self.run_kitten(window, tabs=2)
        self.assertEqual(window.written, [])
        self.assertEqual(boss.close_tab_calls, 1)


if __name__ == "__main__":
    unittest.main()
