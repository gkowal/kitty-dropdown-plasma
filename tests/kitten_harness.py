"""Shared harness for dropdown_manager.py regression tests (AUDIT-003+).

Stubs the `kittens.tui.handler` import (kitty is not installed here) and
provides minimal fakes for Boss/Window/Tab/OS-window objects.
"""
import os
import sys
import types

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

_handler_mod = types.ModuleType("kittens.tui.handler")


def _result_handler(no_ui=True):
    def deco(fn):
        fn._no_ui = no_ui
        return fn
    return deco


_handler_mod.result_handler = _result_handler
_tui_mod = types.ModuleType("kittens.tui")
_tui_mod.handler = _handler_mod
_kittens_mod = types.ModuleType("kittens")
_kittens_mod.tui = _tui_mod
sys.modules.setdefault("kittens", _kittens_mod)
sys.modules.setdefault("kittens.tui", _tui_mod)
sys.modules.setdefault("kittens.tui.handler", _handler_mod)

import dropdown_manager  # noqa: E402


class FakeChild:
    def __init__(self, fg):
        self.foreground_processes = fg


class FakeWindow:
    def __init__(self, fg=None, tab=None):
        self.child = FakeChild(fg if fg is not None else [])
        self.tab = tab
        self.written = []

    def tabref(self):
        # Mirrors kitty's Window: the tab is exposed only as a weakref.
        return self.tab

    def write_to_child(self, data):
        self.written.append(data)


class RealShapeWindow:
    """Window shaped like kitty's real Window: no `.tab` attribute at
    all, tab available only via `.tabref()` (see kitty/window.py)."""
    def __init__(self, fg=None, tab=None):
        self.child = FakeChild(fg if fg is not None else [])
        self._tab = tab
        self.written = []

    def tabref(self):
        return self._tab

    def write_to_child(self, data):
        self.written.append(data)


class FakeTab:
    def __init__(self, os_window_id=1):
        self.os_window_id = os_window_id


class FakeOSWindow:
    def __init__(self, ntabs):
        self.tabs = [object() for _ in range(ntabs)]


class FakeBoss:
    def __init__(self, window=None, wid=7, tabs_in_window=1):
        self.window_id_map = {wid: window} if window is not None else {}
        self.active_window = None
        self.active_tab = FakeTab()
        self.os_window_map = {1: FakeOSWindow(tabs_in_window)}
        self.wid = wid
        self.close_tab_calls = 0
        self.close_os_window_calls = 0
        self.closed_tab = None

    def close_tab(self, tab=None):
        self.close_tab_calls += 1
        self.closed_tab = tab

    def close_os_window(self):
        self.close_os_window_calls += 1
