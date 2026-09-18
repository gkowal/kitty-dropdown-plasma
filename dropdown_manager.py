import subprocess
import shutil
from kittens.tui.handler import result_handler

KNOWN_SHELLS = ('bash', 'zsh', 'fish', 'sh', 'nu', 'dash', 'tcsh', 'csh', 'ksh', 'elvish', 'pwsh', 'powershell', 'xonsh', 'oil', 'ion')

def _invoke_shortcut(name):
    qdbus_cmd = shutil.which("qdbus6") or shutil.which("qdbus-qt6") or shutil.which("qdbus")
    if not qdbus_cmd:
        return None
    try:
        proc = subprocess.run([
            qdbus_cmd,
            "org.kde.kglobalaccel",
            "/component/kwin",
            "org.kde.kglobalaccel.Component.invokeShortcut",
            name
        ], capture_output=True, text=True, check=False)
        return proc.returncode == 0
    except Exception:
        return None

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
            if cmd[0].split('/')[-1] not in KNOWN_SHELLS:
                break
        else:
            forward_eof = False
    except Exception as e:
        print(f"dropdown_manager: foreground process detection failed: {e}")
    if forward_eof:
        window.write_to_child("\x04")
        return

    # 2. Get the tab of the target window (no active-tab fallback).
    tab = getattr(window, 'tab', None)
    if not tab:
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
        # Multiple tabs: Close the active tab entirely
        try:
            boss.close_tab()
        except AttributeError:
            print("dropdown_manager: failed to close the active tab")
