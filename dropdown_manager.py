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
    window = boss.window_id_map.get(target_window_id) or boss.active_window
    if not window:
        return

    # 1. Detect foreground process (SSH, Python, Vim, etc.)
    # If active process is not a local shell, send a standard Ctrl+D (\x04)
    try:
        fg_processes = getattr(window.child, 'foreground_processes', [])
        for p in fg_processes:
            cmd = p.get('cmdline', [])
            if cmd:
                exe = cmd[0].split('/')[-1]
                if exe not in KNOWN_SHELLS:
                    window.write_to_child("\x04")
                    return
    except Exception as e:
        print(f"dropdown_manager: foreground process detection failed: {e}")

    # 2. Get the current active tab and OS window
    tab = getattr(window, 'tab', None) or boss.active_tab
    if not tab:
        return

    os_window = boss.os_window_map.get(tab.os_window_id)
    if not os_window:
        return

    # 3. Count ONLY the tabs in this window
    tab_count = len(os_window.tabs)

    # 4. Handle the logic purely at the Tab level
    if tab_count == 1:
        # Last tab: Minimize the window natively via KDE Plasma D-Bus
        if _invoke_shortcut("Window Minimize"):
            return
        if _invoke_shortcut("Toggle Kitty"):
            return
        try:
            boss.close_os_window()
        except AttributeError:
            print("dropdown_manager: failed to hide the window")
    else:
        # Multiple tabs: Close the active tab entirely
        try:
            boss.close_tab()
        except AttributeError:
            print("dropdown_manager: failed to close the active tab")
