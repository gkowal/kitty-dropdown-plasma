"""Regression test for AUDIT-014: _invoke_shortcut() must always return
a bool and never hang longer than its timeout."""
import os
import subprocess
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitten_harness import dropdown_manager


class InvokeShortcutTest(unittest.TestCase):
    def test_missing_binary_returns_false(self):
        with mock.patch.object(dropdown_manager.shutil, "which",
                               return_value=None):
            self.assertIs(dropdown_manager._invoke_shortcut("X"), False)

    def test_success_returns_true(self):
        proc = mock.Mock(returncode=0)
        with mock.patch.object(dropdown_manager.shutil, "which",
                               return_value="/usr/bin/qdbus6"), \
             mock.patch.object(dropdown_manager.subprocess, "run",
                               return_value=proc) as run:
            self.assertIs(dropdown_manager._invoke_shortcut("X"), True)
            self.assertEqual(run.call_args.kwargs.get("timeout"), 3)

    def test_nonzero_exit_returns_false(self):
        proc = mock.Mock(returncode=1)
        with mock.patch.object(dropdown_manager.shutil, "which",
                               return_value="/usr/bin/qdbus6"), \
             mock.patch.object(dropdown_manager.subprocess, "run",
                               return_value=proc):
            self.assertIs(dropdown_manager._invoke_shortcut("X"), False)

    def test_timeout_returns_false_quickly(self):
        def hang(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="qdbus6",
                                            timeout=kwargs.get("timeout"))
        start = time.monotonic()
        with mock.patch.object(dropdown_manager.shutil, "which",
                               return_value="/usr/bin/qdbus6"), \
             mock.patch.object(dropdown_manager.subprocess, "run",
                               side_effect=hang):
            self.assertIs(dropdown_manager._invoke_shortcut("X"), False)
        self.assertLess(time.monotonic() - start, 3)

    def test_run_error_returns_false(self):
        with mock.patch.object(dropdown_manager.shutil, "which",
                               return_value="/usr/bin/qdbus6"), \
             mock.patch.object(dropdown_manager.subprocess, "run",
                               side_effect=OSError("noexec")):
            self.assertIs(dropdown_manager._invoke_shortcut("X"), False)


if __name__ == "__main__":
    unittest.main()
