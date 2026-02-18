import subprocess
import shutil
from kittens.tui.handler import result_handler

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, result, target_window_id, boss):
    window = boss.active_window
    if not window:
        return

    # 1. Detect foreground process (SSH, Python, etc.)
    # If the active process is not the local shell, send a standard Ctrl+D (\x04)
    try:
        fg_processes = getattr(window.child, 'foreground_processes', [])
        for p in fg_processes:
            cmd = p.get('cmdline', [])
            if cmd:
                exe = cmd[0].split('/')[-1]
                if exe not in ('bash', 'zsh', 'fish', 'sh'):
                    window.write_to_child("\x04")
                    return
    except Exception:
        pass

    # 2. Get the current active tab and OS window
    tab = boss.active_tab
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
        qdbus_cmd = shutil.which("qdbus6") or shutil.which("qdbus-qt6")
        if qdbus_cmd:
            subprocess.run([
                qdbus_cmd,
                "org.kde.kglobalaccel",
                "/component/kwin",
                "org.kde.kglobalaccel.Component.invokeShortcut",
                "Window Minimize"
            ], check=False)
    else:
        # Multiple tabs: Close the active tab entirely
        try:
            boss.close_tab()
        except AttributeError:
            for w in list(tab.windows):
                w.close_window()
