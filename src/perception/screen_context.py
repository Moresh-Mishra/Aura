from .screenshot import capture_screen
from .text_details import (
    extract_observations,
    filter_obeservation,
    group_words_into_lines,
    reconstruct_lines
)

from .ui_detection import (
    get_active_window_info,
    detect_active_window_elements,
    filter_ui_elements
)

from .ui_relationship import analyze_ui_relationships

def get_screen_context(min_confidence = 40):
    """
    Collect information about the current screen and return it as a  unified context 
    """
    active_window = get_active_window_info()

    screenshot = capture_screen()

    screenshot_path = "screenshot.png"

    ui_elements = detect_active_window_elements()
    ui_elements = filter_ui_elements(ui_elements)

    # Analyze UI relationships
    relationships = analyze_ui_relationships(ui_elements)
    observation = extract_observations(screenshot_path)

    filtered_observations = filter_obeservation(
        observation,
        min_confidence
    )

    group = group_words_into_lines(filtered_observations)
    ocr_lines = reconstruct_lines(group)

    width, height = screenshot.size

    screen_context = {
        "active_window": active_window,

        "screenshot": {
            "path": screenshot_path,
            "width": width,
            "height": height
        },

        "ui_elements": [
            element.to_dict()
            for element in ui_elements
        ],

        "ocr_observations": filtered_observations,

        "ocr_lines": ocr_lines,

        "relationships": relationships,
    }

    return screen_context

if __name__ == "__main__":

    context = get_screen_context()

    print("\n========== SCREEN CONTEXT ==========")
    print("Total Relationships:", len(context["relationships"]))
    
    relationship_summary = {}
    
    for relationship in context["relationships"]:
    
        key = (
            relationship["evidence"],
            relationship["relation"]
        )
    
        relationship_summary[key] = (
            relationship_summary.get(key, 0) + 1
        )
    
    print("\nRelationship Breakdown:")
    
    for key, count in relationship_summary.items():
        print(f"{key[0]} | {key[1]}: {count}")