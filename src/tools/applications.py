
import os
import subprocess

from pathlib import Path
from .app_discovery import discover_application
from .app_discovery import discover_application
from .window_manager import list_open_windows
import time

from .window_manager import (
    list_open_windows,
    activate_window,
    get_foreground_window
)


def launch_application(application_name, arguments=None):
    """
    Discover and launch an installed Windows application.
    """

    if arguments is None:
        arguments = []

    if not isinstance(application_name, str) or not application_name.strip():
        raise ValueError("Application name is required.")

    if not isinstance(arguments, (list, tuple)):
        raise TypeError("Arguments must be a list or tuple.")

    if not all(isinstance(arg, str) for arg in arguments):
        raise TypeError("All arguments must be strings.")

    # 1. Discover the application
    discovery = discover_application(application_name)

    # 2. Handle discovery results
    if discovery["status"] == "not_found":
        raise FileNotFoundError(
            f"Application not found: {application_name}"
        )

    if discovery["status"] == "ambiguous":
        candidates = [
            item["executable_path"]
            for item in discovery["candidates"]
        ]

        raise RuntimeError(
            f"Multiple installations found: {candidates}"
        )

    # 3. Retrieve and validate executable path
    application_path = discovery["selected"]["executable_path"]

    if not os.path.isfile(application_path):
        raise FileNotFoundError(
            f"Executable no longer exists: {application_path}"
        )

    # 4. Launch application
    process = subprocess.Popen(
        [application_path, *arguments],
        shell=False
    )

    return {
        "action": "launch_application",
        "application": application_name,
        "executable_path": application_path,
        "process_id": process.pid,
        "discovery_sources": discovery["selected"]["sources"],
        "success": True
    }
def find_running_application(application_name):

    # 1. Discover the installed application
    discovery = discover_application(application_name)

    if discovery["status"] != "found":
        return {
            "status": discovery["status"],
            "application": application_name,
            "candidates": discovery["candidates"]
        }

    executable_path = os.path.normcase(
        os.path.realpath(
            discovery["selected"]["executable_path"]
        )
    )

    # 2. Retrieve currently open windows
    windows = list_open_windows()

    # 3. Match windows to the discovered executable
    matching_windows = []

    for window in windows:

        window_path = window.get("executable_path")

        if not window_path:
            continue

        window_path = os.path.normcase(
            os.path.realpath(window_path)
        )

        if window_path == executable_path:
            matching_windows.append(window)

    # 4. Return application status
    return {
        "application": application_name,
        "executable_path": executable_path,
        "status": (
            "running" if matching_windows else "not_running"
        ),
        "windows": matching_windows
    }


def open_application(
    application_name,
    arguments=None,
    window_timeout=10,
    poll_interval=0.25
):
    """
    Open an application intelligently.

    Reuse an existing window when possible.
    Otherwise launch the application and find its window.
    """

    # 1. Check whether the application is already running
    running = find_running_application(application_name)

    if running["status"] not in ("running", "not_running"):
        return running

    # Helper to choose the best available window
    def select_window(windows):

        if not windows:
            return None

        # Prefer an existing foreground window of this application
        foreground = get_foreground_window()

        if foreground:
            for window in windows:
                if window["handle"] == foreground["handle"]:
                    return window

        # Otherwise prefer a non-minimized window
        for window in windows:
            if not window["is_minimized"]:
                return window

        # Fall back to the first available window
        return windows[0]

    # 2. Reuse an existing window
    if running["status"] == "running":

        selected_window = select_window(running["windows"])

        if selected_window is None:
            return {
                "status": "uncertain",
                "reason": "Running application has no usable window."
            }

        activation = activate_window(
            selected_window["handle"]
        )

        return {
            "application": application_name,
            "status": (
                "already_running_activated"
                if activation["activated"]
                else "activation_failed"
            ),
            "window": activation["window"],
            "activation": activation
        }

    # 3. Launch if the application isn't running
    launch_result = launch_application(
        application_name,
        arguments
    )

    # 4. Wait for its window to appear
    if (
        isinstance(window_timeout, bool)
        or not isinstance(window_timeout, (int, float))
        or window_timeout <= 0
    ):
        raise ValueError("Invalid window timeout.")

    if (
        isinstance(poll_interval, bool)
        or not isinstance(poll_interval, (int, float))
        or poll_interval <= 0
    ):
        raise ValueError("Invalid polling interval.")

    deadline = time.monotonic() + window_timeout

    while time.monotonic() < deadline:

        current = find_running_application(application_name)

        if current["status"] == "running":

            selected_window = select_window(current["windows"])

            if selected_window:

                activation = activate_window(
                    selected_window["handle"]
                )

                return {
                    "application": application_name,
                    "status": (
                        "launched_and_activated"
                        if activation["activated"]
                        else "launched_but_activation_failed"
                    ),
                    "launch": launch_result,
                    "window": activation["window"],
                    "activation": activation
                }

        time.sleep(poll_interval)

    return {
        "application": application_name,
        "status": "launched_window_not_detected",
        "launch": launch_result
    }


if __name__ == "__main__":

    result = open_application("Spotify")

    print("\n========== APPLICATION OPEN RESULT ==========")
    print(result)