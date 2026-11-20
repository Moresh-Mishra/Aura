import win32gui
import re
import time

from src.perception.screen_context import get_screen_context
from src.safety.action_policy import evaluate_action

from .mouse import (
    click_mouse,
    scroll_mouse,
    drag_mouse
    )

from .keyboard import type_text
from collections import defaultdict
from pywinauto import Desktop

from src.verification.action_request import (
    ActionRequest,
    ExpectedOutcome
)
from src.tools.applications import (
    launch_application,
    open_application
)

from src.tools.keyboard import (
    press_key,
    type_text,
    press_hotkey
)

from src.verification.verifier import verify_outcome, verify_text_present
from src.tools.applications import launch_application

from src.tools.window_manager import (
    find_windows_by_title,
    set_window_state,
    activate_window
)


def get_active_elements():

    context = get_screen_context()

    return context["ui_elements"]

def find_element(element_id):
    """Find an element using its current detection ID."""

    elements = get_active_elements()

    for element in elements:
        if element.element_id == element_id:
            return element

    raise ValueError(f"UI element not found: {element_id}")


def click_element(element_id):
    """Click the center of a detected UI element."""

    element = find_element(element_id)

    if not element.attributes.get("visible", True):
        raise ValueError("Element is not visible.")

    if not element.attributes.get("enabled", True):
        raise ValueError("Element is disabled.")

    center_x, center_y = element.center

    click_mouse(
        x=int(center_x),
        y=int(center_y)
    )

    return {
        "action": "click",
        "element_id": element.element_id,
        "element_text": element.text,
        "coordinates": {
            "x": int(center_x),
            "y": int(center_y)
        },
        "success": True
    }


def find_elements_by_text(context, text, element_type=None):
    """
    Search UI elements from an existing screen context.
    """

    matches = []

    for element in context["ui_elements"]:

        element_text = element.get("text")

        if not element_text:
            continue

        if element_text.strip().casefold() != text.strip().casefold():
            continue

        if element_type and element["element_type"] != element_type:
            continue

        matches.append(element)

    return matches


def click_element_by_text(context, text, element_type="button"):

    matches = find_elements_by_text(
        context,
        text,
        element_type
    )

    if not matches:
        raise ValueError(f"Element not found: {text}")

    if len(matches) > 1:
        raise ValueError(
            f"Multiple elements found with text: {text}"
        )

    element = matches[0]
    attributes = element["attributes"]

    if not attributes.get("visible", True):
        raise ValueError("Element is not visible.")

    if not attributes.get("enabled", True):
        raise ValueError("Element is disabled.")

    bounds = element["bounds"]

    center_x = int(bounds["x"] + bounds["width"] / 2)
    center_y = int(bounds["y"] + bounds["height"] / 2)

    click_mouse(center_x, center_y)

    return {
        "action": "click",
        "element_id": element["element_id"],
        "element_text": element["text"],
        "coordinates": {
            "x": center_x,
            "y": center_y
        },
        "success": True
    }



def execute_action(request, *, user_approved=False):
    """
    Execute an ActionRequest and verify its expected outcome.
    Currently supports click and type_text actions.
    """

    if not isinstance(request, ActionRequest):
        raise TypeError("Expected an ActionRequest object.")

    if not isinstance(user_approved, bool):
        raise TypeError("user_approved must be a boolean.")

    # Evaluate permissions before executing anything
    permission = evaluate_action(request.action)

    if permission["decision"] == "blocked":

        return {
            "permission": permission,
            "execution": {
                "status": "blocked"
            }
        }

    if (
        permission["decision"] == "confirmation_required"
        and user_approved is not True
    ):

        return {
            "permission": permission,
            "execution": {
                "status": "not_executed",
                "reason": "Waiting for user approval."
            }
        }
    # 1. Capture environment before the action
    before_context = get_screen_context()

    # 2. Execute the requested action
    if request.action == "click":

        if not request.target:
            raise ValueError("Click action requires a target.")

        target_text = request.target.get("text")
        element_type = request.target.get(
            "element_type", "button"
        )

        if not target_text:
            raise ValueError("Target text is required.")

        action_result = click_element_by_text(
            before_context,
            target_text,
            element_type
        )

    elif request.action == "scroll":
          amount = request.parameters.get("amount")
          axis = request.parameters.get("axis", "vertical")

          x = request.parameters.get("x")
          y = request.parameters.get("y")

          action_result = scroll_mouse(
            amount=amount,
            axis=axis,
            x=x,
            y=y
        )

    elif request.action == "drag":
        start_x = request.parameters.get("start_x")
        start_y = request.parameters.get("start_y")

        end_x = request.parameters.get("end_x")
        end_y = request.parameters.get("end_y")

        action_result = drag_mouse(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            duration=0.5,
        )


    elif request.action == "type_text":

        if not request.target:
            raise ValueError("Typing requires a target input.")

        target_text = request.target.get("text")
        element_type = request.target.get("element_type", "input")

        text_to_type = request.parameters.get("text")

        if not isinstance(text_to_type, str) or not text_to_type:
            raise ValueError("Text to type is required.")

        if not target_text:
            raise ValueError("Target input text is required.")

        if element_type not in ("input", "text_editor"):
            raise ValueError(
                "Typing target must be an input or text editor."
            )
        # Locate and focus the input
        focus_result = click_element_by_text(
            before_context,
            target_text,
            element_type
        )

        # Type the requested text
        typing_result = type_text(text_to_type)

        action_result = {
            "action": "type_text",
            "target": target_text,
            "focus": focus_result,
            "typing": typing_result
        }
    
    elif request.action == "press_key":
        key = request.parameters.get("key")

        if not isinstance(key, str) or not key: 
            raise ValueError("A valid key is needed")

        action_result= press_key(key)

    elif request.action == "hotkey":
        keys = request.parameters.get("keys")

        if not isinstance(keys, (list, tuple)) or not keys:
            raise ValueError("A valid list of keys is required.")

        if not all(isinstance(key, str) and key for key in keys):
            raise ValueError("All hotkey values must be strings.")

        action_result = press_hotkey(*keys)

    elif request.action == "launch_application":

        application = request.parameters.get("application")
        arguments = request.parameters.get("arguments", [])

        action_result = launch_application(
            application,
            arguments
        )

    elif request.action == "set_window_state":
    
            window_title = (
                request.target.get("title")
                if request.target else None
            )
    
            state = request.parameters.get("state")
    
            if not window_title:
                raise ValueError("Window title is required.")
    
            if state not in ("minimize", "maximize", "restore"):
                raise ValueError("Invalid window state.")
    
            # Find matching windows
            windows = find_windows_by_title(window_title)
    
            if not windows:
                raise ValueError(
                    f"Window not found: {window_title}"
                )
    
            if len(windows) > 1:
                raise ValueError(
                    f"Multiple windows found: {window_title}"
                )
    
            # Execute window operation
            hwnd = windows[0]["handle"]
    
            action_result = set_window_state(hwnd, state)
    
    elif request.action == "activate_window":

        window_title = (
            request.target.get("title")
            if request.target else None
        )

        if not window_title:
            raise ValueError("Window title is required.")

        windows = find_windows_by_title(window_title)

        if not windows:
            raise ValueError(
                f"Window not found: {window_title}"
            )

        if len(windows) > 1:
            raise ValueError(
                f"Multiple windows found: {window_title}"
            )

        hwnd = windows[0]["handle"]

        action_result = activate_window(hwnd)


    elif request.action == "open_application":

        application = request.parameters.get("application")
        arguments = request.parameters.get("arguments", [])

        window_timeout = request.parameters.get(
            "window_timeout", 10
        )

        poll_interval = request.parameters.get(
            "poll_interval", 0.25
        )

        action_result = open_application(
            application,
            arguments,
            window_timeout,
            poll_interval
        )
    
    else:
        raise NotImplementedError(
            f"Unsupported action: {request.action}"
        )

    # 3. Allow the application to respond
    settle_time = request.parameters.get(
        "settle_seconds", 0.5
    )

    if (
        isinstance(settle_time, bool)
        or not isinstance(settle_time, (int, float))
        or settle_time < 0
    ):
        raise ValueError("Invalid settle time.")

    time.sleep(settle_time)

    # 4. Capture the updated environment
    after_context = get_screen_context()

    # 5. Verify the expected outcome
    if request.expected_outcome is not None:

        verification = verify_outcome(
            before_context,
            after_context,
            request.expected_outcome
        )
    
    else:
        verification = {
            "status": "not_requested",
            "reason": "No expected outcome specified"
        }

    # 6. Return the complete execution report
    return {
        "action": action_result,
        "verification": verification
    }



def find_ocr_targets(context, text):
    """
    Find text using individual OCR word observations.
    Returns precise bounding boxes for matching words or phrases.
    """

    query_words = re.findall(
        r"[\w]+(?:[.-][\w]+)*",
        text.casefold()
    )

    if not query_words:
        return []

    # Group OCR words by their original Tesseract line
    groups = defaultdict(list)

    for observation in context["ocr_observations"]:

        key = (
            observation["block_num"],
            observation["par_num"],
            observation["line_num"]
        )

        groups[key].append(observation)

    matches = []

    for key, words in groups.items():

        words.sort(key=lambda item: item["x"])

        for i in range(len(words) - len(query_words) + 1):

            selected = words[i:i + len(query_words)]

            # Match each query word against its OCR observation
            matched = all(
                re.search(
                    rf"(?<!\w){re.escape(query_word)}(?!\w)",
                    observation["text"],
                    re.IGNORECASE
                )
                for query_word, observation
                in zip(query_words, selected)
            )

            if not matched:
                continue

            # Calculate the bounding box of matched words only
            x = min(word["x"] for word in selected)
            y = min(word["y"] for word in selected)

            right = max(
                word["x"] + word["width"]
                for word in selected
            )

            bottom = max(
                word["y"] + word["height"]
                for word in selected
            )

            width = right - x
            height = bottom - y

            matches.append({
                "source": "ocr",
                "element_type": "visual_text",
                "text": " ".join(
                    word["text"] for word in selected
                ),
                "matched_text": text,
                "bounds": {
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height
                },
                "center": {
                    "x": x + width / 2,
                    "y": y + height / 2
                }
            })

    return matches


def find_target(context, text, element_type=None):
    """
    Search accessibility first, then use OCR as a fallback.
    """

    # 1. Search accessibility elements
    accessibility_matches = find_elements_by_text(
        context,
        text,
        element_type
    )

    if len(accessibility_matches) == 1:
        return {
            "status": "found",
            "source": "accessibility",
            "target": accessibility_matches[0]
        }

    if len(accessibility_matches) > 1:
        return {
            "status": "ambiguous",
            "source": "accessibility",
            "matches": accessibility_matches
        }

    # 2. Fall back to OCR
    ocr_matches = find_ocr_targets(context, text)

    if len(ocr_matches) == 1:
        return {
            "status": "visual_text_only",
            "source": "ocr",
            "target": ocr_matches[0]
        }

    if len(ocr_matches) > 1:
        return {
            "status": "ambiguous",
            "source": "ocr",
            "matches": ocr_matches
        }

    return {
        "status": "not_found",
        "source": None,
        "target": None
    }


def click_ocr_target(context, text):
    """
    Click a uniquely identified OCR text target.
    This clicks visible text, not necessarily an interactive control.
    """

    matches = find_ocr_targets(context, text)

    if not matches:
        raise ValueError(f"OCR target not found: {text}")

    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous OCR target: {text}. "
            f"Found {len(matches)} matches."
        )

    target = matches[0]

    center = target["center"]

    click_mouse(
        int(center["x"]),
        int(center["y"])
    )

    return {
        "action": "visual_text_click",
        "source": "ocr",
        "matched_text": target["matched_text"],
        "coordinates": center,
        "success": True
    }


def verify_screen_change(before_context, after_context):
    """
    Compare two screen contexts and identify observable changes.
    This detects changes, not whether the intended action succeeded.
    """

    def get_ui_signature(context):

        return {
            (
                element["element_type"],
                (element.get("text") or "").strip(),
                element["bounds"]["x"],
                element["bounds"]["y"],
                element["bounds"]["width"],
                element["bounds"]["height"]
            )
            for element in context["ui_elements"]
        }

    before_ui = get_ui_signature(before_context)
    after_ui = get_ui_signature(after_context)

    added_elements = after_ui - before_ui
    removed_elements = before_ui - after_ui

    before_ocr = {
        line["text"].strip()
        for line in before_context["ocr_lines"]
    }

    after_ocr = {
        line["text"].strip()
        for line in after_context["ocr_lines"]
    }

    added_lines = after_ocr - before_ocr
    removed_lines = before_ocr - after_ocr

    screen_changed = bool(
        added_elements or
        removed_elements or
        added_lines or
        removed_lines
    )

    return {
        "status": (
            "screen_changed"
            if screen_changed
            else "no_detectable_change"
        ),
        "ui_elements_added": len(added_elements),
        "ui_elements_removed": len(removed_elements),
        "ocr_lines_added": len(added_lines),
        "ocr_lines_removed": len(removed_lines)
    }

def click_and_observe(context, text, element_type="button"):

    # Execute the action using the existing snapshot
    action_result = click_element_by_text(
        context,
        text,
        element_type
    )

    # Capture the updated environment
    updated_context = get_screen_context()

    # Compare the before and after states
    verification = verify_screen_change(
        context,
        updated_context
    )

    return {
        "action": action_result,
        "verification": verification
    }


def inspect_outline_layout(context):

    outline_matches = find_elements_by_text(
        context,
        "Outline Section",
        "button"
    )

    timeline_matches = find_elements_by_text(
        context,
        "Timeline Section",
        "button"
    )

    if len(outline_matches) != 1:
        return {"status": "outline_not_uniquely_found"}

    if len(timeline_matches) != 1:
        return {"status": "timeline_not_uniquely_found"}

    outline = outline_matches[0]["bounds"]
    timeline = timeline_matches[0]["bounds"]

    outline_bottom = outline["y"] + outline["height"]

    vertical_gap = timeline["y"] - outline_bottom

    # Find detected elements between the two headers
    elements_between = []

    for element in context["ui_elements"]:

        bounds = element["bounds"]

        center_y = bounds["y"] + bounds["height"] / 2

        horizontal_overlap = (
            bounds["x"] < outline["x"] + outline["width"]
            and bounds["x"] + bounds["width"] > outline["x"]
        )

        if (
            outline_bottom < center_y < timeline["y"]
            and horizontal_overlap
        ):
            elements_between.append({
                "type": element["element_type"],
                "text": element["text"],
                "bounds": bounds
            })

    return {
        "outline_bounds": outline,
        "timeline_bounds": timeline,
        "vertical_gap": vertical_gap,
        "elements_between": elements_between
    }


if __name__ == "__main__":
    request = ActionRequest(
    action="drag",

    parameters={
        "start_x": 10,
        "start_y": 10,
        "end_x": 100,
        "end_y": 100
    }
)

result = execute_action(
    request,
    user_approved=True
)

print("\n========== WINDOW SWITCHING ==========")
print(result)