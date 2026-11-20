
from dataclasses import asdict, is_dataclass


def find_unique_element(context, text, element_type=None):
    """
    Find exactly one UI element by its accessible text.
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

    if len(matches) != 1:
        return None

    return matches[0]


def verify_element_position_changed(
    before_context,
    after_context,
    expected
):
    """
    Verify whether a UI element moved between two observations.
    """

    target_text = expected.get("target_text")
    element_type = expected.get("element_type")

    options = expected.get("options", {})

    axis = options.get("axis", "y")
    minimum_delta = options.get("minimum_delta", 1)

    if axis not in ("x", "y"):
        return {
            "status": "uncertain",
            "reason": "Invalid position axis"
        }

    before_element = find_unique_element(
        before_context,
        target_text,
        element_type
    )

    after_element = find_unique_element(
        after_context,
        target_text,
        element_type
    )

    if before_element is None or after_element is None:
        return {
            "status": "uncertain",
            "reason": "Target was missing or ambiguous"
        }

    before_position = before_element["bounds"][axis]
    after_position = after_element["bounds"][axis]

    delta = after_position - before_position

    verified = abs(delta) >= minimum_delta

    return {
        "status": "verified" if verified else "failed",
        "expected": "element_position_changed",
        "target": target_text,
        "axis": axis,
        "before": before_position,
        "after": after_position,
        "delta": delta,
        "minimum_delta": minimum_delta
    }


def verify_outcome(
    before_context,
    after_context,
    expected_outcome
):
    """
    Main verification dispatcher.
    """

    if is_dataclass(expected_outcome):
        expected_outcome = asdict(expected_outcome)

    if not isinstance(expected_outcome, dict):
        return {
            "status": "uncertain",
            "reason": "Invalid expected outcome"
        }

    kind = expected_outcome.get("kind")

    if kind == "element_position_changed":

        return verify_element_position_changed(
            before_context,
            after_context,
            expected_outcome
        )

    if kind == "text_present":
        return verify_text_present(
            after_context,
            expected_outcome
        )

    return {
        "status": "uncertain",
        "reason": f"Unsupported verification strategy: {kind}"
    }

def verify_text_present(after_context, expected):

    expected_text = expected.get("expected_value")

    if not isinstance(expected_text, str) or not expected_text.strip():
        return {
            "status": "uncertain",
            "reason": "Expected text is missing"
        }

    expected_text = " ".join(
        expected_text.split()
    ).casefold()

    for line in after_context.get("ocr_lines", []):

        detected_text = " ".join(
            line.get("text", "").split()
        ).casefold()

        if expected_text in detected_text:
            return {
                "status": "verified",
                "expected_text": expected_text,
                "evidence": "ocr"
            }

    return {
        "status": "uncertain",
        "expected_text": expected_text,
        "reason": "Expected text was not detected by OCR"
    }

if __name__ == "__main__":

    before_context = {
        "ui_elements": [
            {
                "element_type": "button",
                "text": "Timeline Section",
                "bounds": {"y": 602}
            }
        ]
    }

    after_context = {
        "ui_elements": [
            {
                "element_type": "button",
                "text": "Timeline Section",
                "bounds": {"y": 752}
            }
        ]
    }

    expected = {
        "kind": "element_position_changed",
        "target_text": "Timeline Section",
        "options": {
            "minimum_delta": 20
        }
    }

    result = verify_outcome(
        before_context,
        after_context,
        expected
    )

    print(result)