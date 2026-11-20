
import win32gui
import win32process
import psutil
import time
import win32con

from functools import lru_cache


@lru_cache(maxsize=512)
def get_process_details(process_id):
    """
    Retrieve process information using user-mode APIs.
    """

    try:
        process = psutil.Process(process_id)

        with process.oneshot():
            return {
                "process_name": process.name(),
                "executable_path": process.exe()
            }

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):
        return {
            "process_name": None,
            "executable_path": None
        }


def get_window_info(hwnd):
    """
    Retrieve information about a top-level window.
    """

    if not win32gui.IsWindow(hwnd):
        return None

    if not win32gui.IsWindowVisible(hwnd):
        return None

    title = win32gui.GetWindowText(hwnd)

    if not title.strip():
        return None

    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)

        _, process_id = win32process.GetWindowThreadProcessId(hwnd)

        process_details = get_process_details(process_id)

        return {
            "handle": hwnd,
            "title": title,
            "process_id": process_id,

            "process_name": process_details["process_name"],
            "executable_path": process_details["executable_path"],

            "bounds": {
                "x": left,
                "y": top,
                "width": right - left,
                "height": bottom - top
            },

            "is_minimized": bool(win32gui.IsIconic(hwnd))
        }

    except Exception:
        return None


def list_open_windows():
    """
    Discover visible top-level windows.
    """

    windows = []

    def callback(hwnd, _):

        window_info = get_window_info(hwnd)

        if window_info:
            windows.append(window_info)

    win32gui.EnumWindows(callback, None)

    return sorted(
        windows,
        key=lambda window: window["title"].casefold()
    )


def get_foreground_window():
    """
    Retrieve the currently active window.
    """

    hwnd = win32gui.GetForegroundWindow()

    if not hwnd:
        return None

    return get_window_info(hwnd)


def find_windows_by_title(query, windows=None):
    """
    Find windows using a case-insensitive title search.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Window search query is required.")

    if windows is None:
        windows = list_open_windows()

    query = query.strip().casefold()

    return [
        window
        for window in windows
        if query in window["title"].casefold()
    ]

def activate_window(hwnd):
    """
    Restore and activate an existing application window.
    """

    if not win32gui.IsWindow(hwnd):
        raise ValueError("Invalid window handle.")

    # Restore if minimized
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    # Request foreground activation
    win32gui.SetForegroundWindow(hwnd)

    # Verify foreground status
    is_active = (
        win32gui.GetForegroundWindow() == hwnd
    )

    return {
        "handle": hwnd,
        "activated": is_active,
        "window": get_window_info(hwnd)
    }


def set_window_state(hwnd, state):
    """
    Minimize, maximize or restore a window.
    Uses documented Windows user-mode APIs.
    """

    if not win32gui.IsWindow(hwnd):
        raise ValueError("Invalid window handle.")

    commands = {
        "minimize": win32con.SW_MINIMIZE,
        "maximize": win32con.SW_MAXIMIZE,
        "restore": win32con.SW_RESTORE
    }

    if state not in commands:
        raise ValueError(
            "State must be minimize, maximize or restore."
        )

    # Change window state
    win32gui.ShowWindow(hwnd, commands[state])

    # Independently inspect actual state
    placement = win32gui.GetWindowPlacement(hwnd)

    show_command = placement[1]

    if show_command == win32con.SW_SHOWMINIMIZED:
        actual_state = "minimized"

    elif show_command == win32con.SW_SHOWMAXIMIZED:
        actual_state = "maximized"

    else:
        actual_state = "normal"
    # Verify requested state
    expected_states = {
        "minimize": "minimized",
        "maximize": "maximized",
        "restore": "normal"
    }

    return {
        "handle": hwnd,
        "window": win32gui.GetWindowText(hwnd),
        "requested_state": state,
        "actual_state": actual_state,
        "verified": actual_state == expected_states[state]
    }


if __name__ == "__main__":

    windows = find_windows_by_title("Brave")

    if len(windows) == 1:

        hwnd = windows[0]["handle"]

        # First maximize
        print(set_window_state(hwnd, "maximize"))

        time.sleep(2)

        # Then restore
        print(set_window_state(hwnd, "restore"))

    else:
        print("Expected exactly one Notepad window.")