
from pywinauto import Desktop


def inspect_windows():

    desktop = Desktop(backend="uia")

    windows = desktop.windows()

    for window in windows:

        print("\nWINDOW:", window.window_text())

        try:
            elements = window.descendants()

            for element in elements:

                info = element.element_info

                print({
                    "name": info.name,
                    "control_type": info.control_type,
                    "rectangle": str(info.rectangle),
                    "enabled": info.enabled
                })

        except Exception as error:
            print("Inspection error:", error)


if __name__ == "__main__":
    inspect_windows()
