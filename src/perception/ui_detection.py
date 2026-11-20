from dataclasses import dataclass, field
from typing import Optional
from pywinauto import Desktop
import win32gui
from .ui_relationship import get_parent_metadata

@dataclass
class UIElement:
    """ Standard repersentation of a detected UI Element 
    """

    element_id: str
    element_type: str

    x: int
    y: int 
    width: int
    height: int 

    text: Optional[str] = None
    confidence: Optional[float] = None

    source: str = "Unknown"

    attributes: dict = field(default_factory=dict)

    @property
    def center(self):
        return (
        self.x + self.width / 2,
        self.y + self.height / 2
        )

    def to_dict(self):
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "text": self.text,
            "bounds": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height
            },
            "confidence": self.confidence,
            "source": self.source,
            "attributes": self.attributes
        }



from pywinauto import Desktop


# Map Windows control types to Aura element types
CONTROL_TYPE_MAP = {
    "Button": "button",
    "Edit": "input",
    "Document": "text_editor",
    "CheckBox": "checkbox",
    "RadioButton": "radio",
    "ComboBox": "dropdown",
    "List": "list",
    "ListItem": "list_item",
    "MenuItem": "menu_item",
    "TabItem": "tab",
    "Text": "text",
    "Hyperlink": "link",
    "Image": "image",
    "Window": "window",
    "ToolBar": "toolbar"
}


def detect_desktop_elements():

    detected_elements = []

    desktop = Desktop(backend="uia")

    windows = desktop.windows()

    element_counter = 0

    for window in windows:

        try:
            elements = window.descendants()

            for element in elements:

                info = element.element_info

                control_type = info.control_type

                element_type = CONTROL_TYPE_MAP.get(
                    control_type,
                    "unknown"
                )

                if element_type == "unknown":
                    continue

                rect = info.rectangle

                if rect.width() <= 0 or rect.height() <= 0:
                    continue

                element_counter += 1

                ui_element = UIElement(
                    element_id=f"desktop_{element_counter}",
                    element_type=element_type,
                    x=rect.left,
                    y=rect.top,
                    width=rect.width(),
                    height=rect.height(),
                    text=info.name or None,
                    confidence=None,
                    source="desktop_accessibility",
                    attributes={
                        "control_type": control_type,
                        "enabled": info.enabled,
                        "visible": info.visible,
                        "window": window.window_text()
                    }
                )

                detected_elements.append(ui_element)

        except Exception as error:
            print(f"Window inspection failed: {error}")

    return detected_elements


def filter_ui_elements(elements):
    """
    Remove empty, invisible and invalid UI elements.
    """

    filtered = []

    seen = set()

    for element in elements:

        # Ignore empty labels
        if not element.text and element.element_type == "unknown":
            continue

        # Ignore invisible elements
        if not element.attributes.get("visible", True):
            continue

        # Ignore invalid dimensions
        if element.width <= 0 or element.height <= 0:
            continue

        # Basic duplicate detection
        key = (
            element.element_type,
            element.text,
            element.x,
            element.y,
            element.width,
            element.height
        )

        if key in seen:
            continue

        seen.add(key)

        filtered.append(element)

    return filtered



def get_active_window():
    """
    Return the currently focused window.
    """
    hwnd = win32gui.GetForegroundWindow()

    if not hwnd:
        return None

    return Desktop(backend="uia").window(handle=hwnd)

def get_active_window_info():
    hwnd = win32gui.GetForegroundWindow()

    return {
        "handle": hwnd,
        "title": win32gui.GetWindowText(hwnd)
    }

def detect_active_window_elements():
    hwnd = win32gui.GetForegroundWindow()

    desktop = Desktop(backend="uia")

    window_spec = desktop.window(handle=hwnd)
    window = window_spec.wrapper_object()

    detected_elements = []

    for index, element in enumerate(window.descendants()):
        try:
            info = element.element_info
            rect = info.rectangle

            if rect.width() <= 0 or rect.height() <= 0:
                continue

            control_type = info.control_type
            element_type = CONTROL_TYPE_MAP.get(
                control_type, "unknown"
            )

            if element_type == "unknown":
                continue

            ui_element = UIElement(
                element_id=f"active_{index}",
                element_type=element_type,
                x=rect.left,
                y=rect.top,
                width=rect.width(),
                height=rect.height(),
                text=info.name or None,
                source="desktop_accessibility",
                attributes={
                    "control_type": control_type,
                    "enabled": info.enabled,
                    "visible": info.visible,
                    "window": win32gui.GetWindowText(hwnd),
                    "parent": get_parent_metadata(element)
                }
            )

            detected_elements.append(ui_element)

        except Exception:
            continue

    return detected_elements

if __name__ == "__main__":

    elements = detect_active_window_elements()
    elements = filter_ui_elements(elements)

    for element in elements:

        if element.text in (
            "Accounts",
            "Manage",
            "Outline",
            "Timeline"
        ):
            print("\nUI ELEMENT:")
            print(element.to_dict())

            print("\nPARENT:")
            print(element.attributes.get("parent"))