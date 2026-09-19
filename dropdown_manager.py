import subprocess
import shutil
from kittens.tui.handler import result_handler

KNOWN_SHELLS = ('bash', 'zsh', 'fish', 'sh', 'nu', 'dash', 'tcsh', 'csh', 'ksh', 'elvish', 'pwsh', 'powershell', 'xonsh', 'oil', 'ion')

def _shell_exe_name(cmd0):
    # Basename with one login-shell leading dash stripped, so `-zsh`
    # and `-bash` classify as shells. Anything else (versioned app
    # binaries, wrappers such as sudo/tmux) intentionally stays
    # non-shell: forwarding Ctrl+D there is the safe direction.
    return cmd0.split('/')[-1].removeprefix('-')

def _invoke_shortcut(name):
    qdbus_cmd = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
    if not qdbus_cmd:
        return False
    try:
        proc = subprocess.run([
            qdbus_cmd,
            "org.kde.kglobalaccel",
            "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut",
            name
        ], capture_output=True, text=True, check=False, timeout=3)
        # A local qdbus call answers in milliseconds; anything slower is
        # treated as failure so one Ctrl+D can never hang the terminal.
        return proc.returncode == 0
    except Exception:
        return False

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    # Never fall back to whichever window happens to be active: a stale
    # target id must abort instead of acting on an unrelated terminal.
    window = boss.window_id_map.get(target_window_id)
    if not window:
        return

    # 1. Detect foreground process (SSH, Python, Vim, etc.)
    # If active process is not a local shell, send a standard Ctrl+D (\x04).
    # Smart-EOF handling below only runs after positively identifying a
    # local shell: any missing or unparseable process data fails safe by
    # forwarding Ctrl+D unchanged instead of closing or hiding anything.
    forward_eof = True
    try:
        fg_processes = getattr(window.child, 'foreground_processes', None)
        if not fg_processes:
            raise ValueError("no foreground process data")
        for p in fg_processes:
            cmd = p.get('cmdline', []) or []
            if not cmd or not isinstance(cmd[0], str):
                raise ValueError("unparseable foreground process entry")
            if _shell_exe_name(cmd[0]) not in KNOWN_SHELLS:
                break
        else:
            forward_eof = False
    except Exception as e:
        print(f"dropdown_manager: foreground process detection failed: {e}")
    if forward_eof:
        window.write_to_child("\x04")
        return

    # 2. Resolve the tab of the target window. Kitty's Window has no
    # `.tab` attribute -- only the `.tabref()` weak reference -- so look
    # it up exactly that way. A missing reference means a detached
    # window; abort instead of guessing (no active-tab fallback: that
    # could close or hide an unrelated terminal).
    tabref = getattr(window, 'tabref', None)
    tab = tabref() if callable(tabref) else None
    if tab is None:
        return

    os_window = boss.os_window_map.get(tab.os_window_id)
    if not os_window:
        return

    # 3. Count ONLY the tabs in this window
    tab_count = len(os_window.tabs)

    # 4. Handle the logic purely at the Tab level
    if tab_count == 1:
        # Last tab: hide the window via KWin. Never destroy the OS
        # window here: losing the hide mechanisms must not turn a
        # harmless Ctrl+D into session loss.
        if _invoke_shortcut("Window Minimize"):
            return
        if _invoke_shortcut("Toggle Kitty"):
            return
        print("dropdown_manager: unable to hide the window; leaving it intact")
    else:
        # Multiple tabs: close the target tab explicitly (not merely
        # the active one, in case focus moved since Ctrl+D).
        try:
            boss.close_tab(tab)
        except (AttributeError, TypeError):
            print("dropdown_manager: failed to close the target tab")
