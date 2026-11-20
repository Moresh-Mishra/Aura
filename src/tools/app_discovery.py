
import os
import re
import shutil
import winreg

from pathlib import Path


APP_PATHS_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\App Paths"
)


# Known application names and their executable names
APP_ALIASES = {
    "brave": {
        "executables": ["brave.exe"],
        "names": ["Brave", "Brave Browser"]
    },

    "bravebrowser": {
        "executables": ["brave.exe"],
        "names": ["Brave", "Brave Browser"]
    },

    "notepad": {
        "executables": ["notepad.exe"],
        "names": ["Notepad"]
    },

    "visualstudiocode": {
        "executables": ["code.exe"],
        "names": ["Visual Studio Code", "VS Code"]
    },

    "vscode": {
        "executables": ["code.exe"],
        "names": ["Visual Studio Code", "VS Code"]
    }
}


def normalize_name(name):
    """Normalize names for case-insensitive matching."""

    return re.sub(r"[^a-z0-9]", "", name.casefold())


def get_application_identifiers(application_name):
    """Generate executable and shortcut names to search for."""

    normalized = normalize_name(application_name)

    config = APP_ALIASES.get(normalized)

    if config:
        executables = config["executables"]
        names = config["names"]
    else:
        filename = Path(application_name).name

        if not filename.lower().endswith(".exe"):
            filename += ".exe"

        executables = [filename]
        names = [application_name]

    shortcut_names = {
        normalize_name(name)
        for name in names
    }

    shortcut_names.add(normalized)

    executable_names = {
        normalize_name(Path(name).stem)
        for name in executables
    }

    return executables, shortcut_names, executable_names


def add_candidate(candidates, path, source, display_name=None,
                  shortcut_path=None):

    """Validate and store a discovered executable."""

    if not path:
        return

    path = os.path.expandvars(
        os.path.expanduser(str(path).strip().strip('"'))
    )

    executable = Path(path)

    if not executable.is_absolute():
        return

    if not executable.is_file():
        return

    key = os.path.normcase(str(executable.resolve()))

    if key not in candidates:
        candidates[key] = {
            "name": display_name or executable.stem,
            "executable_path": key,
            "sources": [],
            "shortcut_path": shortcut_path
        }

    if source not in candidates[key]["sources"]:
        candidates[key]["sources"].append(source)


def search_registry(executables, candidates):
    """Search per-user and system-wide App Paths entries."""

    roots = [
        winreg.HKEY_CURRENT_USER,
        winreg.HKEY_LOCAL_MACHINE
    ]

    views = [
        0,
        getattr(winreg, "KEY_WOW64_32KEY", 0),
        getattr(winreg, "KEY_WOW64_64KEY", 0)
    ]

    for root in roots:

        for executable in executables:

            key_path = APP_PATHS_KEY + "\\" + executable

            for view in set(views):

                try:
                    with winreg.OpenKey(
                        root,
                        key_path,
                        0,
                        winreg.KEY_READ | view
                    ) as key:

                        executable_path, _ = winreg.QueryValueEx(
                            key, ""
                        )

                        add_candidate(
                            candidates,
                            executable_path,
                            "registry_app_paths",
                            Path(executable).stem
                        )

                except OSError:
                    continue


def search_start_menu(
    application_names,
    executable_names,
    candidates
):
    """Search user and system Start Menu shortcuts."""

    appdata = Path(
        os.environ.get("APPDATA", "")
    )

    programdata = Path(
        os.environ.get("PROGRAMDATA", r"C:\ProgramData")
    )

    start_menu_locations = [
        appdata / "Microsoft/Windows/Start Menu/Programs",
        programdata / "Microsoft/Windows/Start Menu/Programs"
    ]

    try:
        import win32com.client

        shell = win32com.client.Dispatch("WScript.Shell")

    except ImportError:
        return

    for location in start_menu_locations:

        if not location.is_dir():
            continue

        try:
            shortcuts = location.rglob("*.lnk")

            for shortcut in shortcuts:

                shortcut_name = normalize_name(shortcut.stem)

                try:
                    shortcut_object = shell.CreateShortcut(
                        str(shortcut)
                    )

                    target_path = shortcut_object.TargetPath

                except Exception:
                    continue

                target_name = normalize_name(
                    Path(target_path).stem
                ) if target_path else ""

                # Match the shortcut's display name or executable
                if (
                    shortcut_name not in application_names
                    and target_name not in executable_names
                ):
                    continue

                add_candidate(
                    candidates,
                    target_path,
                    "start_menu_shortcut",
                    shortcut.stem,
                    str(shortcut)
                )

        except OSError:
            continue


def search_path(executables, candidates):
    """Search executable names in the system PATH."""

    for executable in executables:

        result = shutil.which(executable)

        if result:
            add_candidate(
                candidates,
                result,
                "system_path",
                Path(executable).stem
            )


def discover_application(application_name):
    """
    Discover an installed Windows application.

    Returns:
        found      - exactly one unique executable
        ambiguous  - multiple executable candidates
        not_found  - no validated executable found
    """

    if os.name != "nt":
        raise OSError(
            "This discovery implementation currently supports Windows only."
        )

    if not isinstance(application_name, str) or not application_name.strip():
        raise ValueError("Application name is required.")

    (
        executables,
        shortcut_names,
        executable_names
    ) = get_application_identifiers(application_name)

    candidates = {}

    # 1. Registry
    search_registry(executables, candidates)

    # 2. Start Menu
    search_start_menu(
        shortcut_names,
        executable_names,
        candidates
    )

    # 3. System PATH
    search_path(executables, candidates)

    results = list(candidates.values())

    if len(results) == 1:
        status = "found"
        selected = results[0]

    elif len(results) > 1:
        status = "ambiguous"
        selected = None

    else:
        status = "not_found"
        selected = None

    return {
        "query": application_name,
        "status": status,
        "selected": selected,
        "candidates": results
    }


if __name__ == "__main__":

    result = discover_application("Valorant")

    print("\n========== APPLICATION DISCOVERY ==========")
    print("Requested:", result["query"])
    print("Status:", result["status"])

    for candidate in result["candidates"]:

        print("\nApplication:", candidate["name"])
        print("Executable:", candidate["executable_path"])
        print("Sources:", candidate["sources"])
        print("Shortcut:", candidate["shortcut_path"])
