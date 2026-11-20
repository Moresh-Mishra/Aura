import math 
from collections import Counter

def get_bounds(element):
    return (
        element.x,
        element.y,
        element.x + element.width,
        element.y + element.height
    )

def is_inside(element_a, element_b):
    """
    Check whether element_a is completely inside element_b.
    """

    ax1, ay1, ax2, ay2 = get_bounds(element_a)
    bx1, by1, bx2, by2 = get_bounds(element_b)

    return (
        bx1 <= ax1 and
        by1 <= ay1 and
        bx2 >= ax2 and
        by2 >= ay2
    )

def calculate_distance(element_a, element_b):
    """
    Calculate distance between the centers of two elements.
    """

    center_a = element_a.center
    center_b = element_b.center

    return math.hypot(
        center_a[0] - center_b[0],
        center_a[1] - center_b[1]
    )



def detect_relationships(elements, proximity_threshold=100):

    relationships = []

    # Compare each unique pair only once
    for i, element_a in enumerate(elements):

        ax1, ay1, ax2, ay2 = get_bounds(element_a)

        for element_b in elements[i + 1:]:

            bx1, by1, bx2, by2 = get_bounds(element_b)

            # 1. Check containment
            a_contains_b = (
                is_inside(element_b, element_a)
                and get_bounds(element_a) != get_bounds(element_b)
            )

            b_contains_a = (
                is_inside(element_a, element_b)
                and get_bounds(element_a) != get_bounds(element_b)
            )

            if a_contains_b:
                relationships.append({
                    "source": element_a.element_id,
                    "relation": "contains",
                    "target": element_b.element_id
                })
                continue

            if b_contains_a:
                relationships.append({
                    "source": element_b.element_id,
                    "relation": "contains",
                    "target": element_a.element_id
                })
                continue

            # 2. Calculate bounding-box overlap
            
        # 2. Check identical bounding boxes
        if (ax1, ay1, ax2, ay2) == (bx1, by1, bx2, by2):
        
            relationships.append({
                "source": element_a.element_id,
                "relation": "same_bounds",
                "target": element_b.element_id
            })

            continue
        
        # 3. Calculate bounding-box overlap
        overlap_width = max(
            0, min(ax2, bx2) - max(ax1, bx1)
        )

        overlap_height = max(
            0, min(ay2, by2) - max(ay1, by1)
        )

        if overlap_width > 0 and overlap_height > 0:
        
            width_ratio = (
                overlap_width / min(element_a.width, element_b.width)
            )

            height_ratio = (
                overlap_height / min(element_a.height, element_b.height)
            )

            # Require meaningful overlap in both dimensions
            if width_ratio >= 0.25 and height_ratio >= 0.25:
            
                relationships.append({
                    "source": element_a.element_id,
                    "relation": "overlaps",
                    "target": element_b.element_id,
                    "width_ratio": round(width_ratio, 3),
                    "height_ratio": round(height_ratio, 3)
                })

            continue
        

        # 3. Calculate edge-to-edge distance
        dx = max(0, ax1 - bx2, bx1 - ax2)
        dy = max(0, ay1 - by2, by1 - ay2)
        distance = math.hypot(dx, dy)
        if distance == 0:
            relationships.append({
                "source": element_a.element_id,
                "relation": "touches",
                "target": element_b.element_id
            })
        elif distance <= proximity_threshold:
            relationships.append({
                "source": element_a.element_id,
                "relation": "near",
                "target": element_b.element_id,
                "distance": round(distance, 2)
            })

    return relationships


def detect_accessibility_relationships(elements):

    relationships = []

    # Build an index of detected elements using their bounds
    element_index = {}

    for element in elements:

        key = (
            element.attributes.get("control_type"),
            element.x,
            element.y,
            element.width,
            element.height
        )

        element_index.setdefault(key, []).append(element)

    # Find the detected parent of each element
    for child in elements:

        parent_info = child.attributes.get("parent")

        if not parent_info:
            continue

        bounds = parent_info.get("bounds")

        if not bounds:
            continue

        parent_key = (
            parent_info.get("control_type"),
            bounds["x"],
            bounds["y"],
            bounds["width"],
            bounds["height"]
        )

        candidates = [
            element
            for element in element_index.get(parent_key, [])
            if element.element_id != child.element_id
        ]

        # Resolve multiple candidates using their accessible names
        if len(candidates) > 1:

            def normalize_name(name):
                return "".join(
                    character.lower()
                    for character in (name or "")
                    if character.isalnum()
                )

            parent_name = normalize_name(parent_info.get("name"))

            matching_candidates = [
                element
                for element in candidates
                if normalize_name(element.text) == parent_name
            ]

            if len(matching_candidates) == 1:
                candidates = matching_candidates

        # Only create a relationship when the parent is identifiable
        if len(candidates) == 1:

            parent = candidates[0]

            relationships.append({
            "source": child.element_id,
            "relation": "child_of",
            "target": parent.element_id,
            "source_type": child.element_type,
            "target_type": parent.element_type,
            "evidence": "accessibility"
            })

    return relationships


def analyze_ui_relationships(elements, proximity_threshold=100):

    # 1. Detect geometric relationships
    geometric_relationships = detect_relationships(
        elements,
        proximity_threshold
    )

    # 2. Detect accessibility relationships
    accessibility_relationships = detect_accessibility_relationships(
        elements
    )

    # 3. Identify the evidence behind each relationship
    for relationship in geometric_relationships:
        relationship["evidence"] = "geometry"

    # 4. Combine both collections
    all_relationships = (
        accessibility_relationships +
        geometric_relationships
    )

    return all_relationships


def get_parent_metadata(element):

    try:
        parent = element.parent()
        info = parent.element_info
        rect = info.rectangle

        return {
            "name": info.name or None,
            "control_type": info.control_type,
            "bounds": {
                "x": rect.left,
                "y": rect.top,
                "width": rect.width(),
                "height": rect.height()
            }
        }

    except Exception:
        return None

if __name__ == "__main__":

    from .ui_detection import (
        detect_active_window_elements,
        filter_ui_elements
    )

    elements = filter_ui_elements(
        detect_active_window_elements()
    )

    relationships = detect_relationships(elements)

    counts = Counter(
    relationship["relation"]
    for relationship in relationships
    )

    
    element_lookup = {
    element.element_id: element
    for element in elements
    }   

    def describe_element(element):
        return (
        f"{element.element_id} "
        f"[{element.element_type}] "
        f"text={element.text!r} "
        f"bounds=({element.x}, {element.y}, "
        f"{element.width}, {element.height})"
    )


    for relation_type in (
        "contains",
        "overlaps",
        "touches",
        "near"
    ):

        print(f"\n========== {relation_type.upper()} ==========")

    samples = [
        relationship
        for relationship in relationships
        if relationship["relation"] == relation_type
    ][:5]

    accessibility_relationships = detect_accessibility_relationships(
        elements
    )

    print("\n========== ACCESSIBILITY RELATIONSHIPS ==========")

    print(
        "Detected accessibility relationships:",
        len(accessibility_relationships)
    )

    for relationship in accessibility_relationships[:20]:
        print(relationship)
    
