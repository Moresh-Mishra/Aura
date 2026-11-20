
import pytesseract


# 1. Extract OCR observations
def extract_observations(image_path):

    img_data = pytesseract.image_to_data(
        image_path,
        output_type=pytesseract.Output.DICT
    )

    observations = []

    for i in range(len(img_data["text"])):

        word = img_data["text"][i].strip()

        if not word:
            continue

        observations.append({
            "text": word,
            "x": img_data["left"][i],
            "y": img_data["top"][i],
            "width": img_data["width"][i],
            "height": img_data["height"][i],
            "confidence": float(img_data["conf"][i]),

            "centre_x": float(
                img_data["left"][i] + img_data["width"][i] / 2
            ),

            "centre_y": float(
                img_data["top"][i] + img_data["height"][i] / 2
            ),

            "block_num": img_data["block_num"][i],
            "par_num": img_data["par_num"][i],
            "line_num": img_data["line_num"][i],
            "word_num": img_data["word_num"][i]
        })

    return observations


# 2. Filter observations by OCR confidence
def filter_obeservation(observations, min_confidence):

    filtered = []

    for observation in observations:

        if observation["confidence"] >= min_confidence:
            filtered.append(observation)

    return filtered


# 3. Group words using Tesseract line identifiers
def group_words_into_lines(observations):

    groups = {}

    for observation in observations:

        key = (
            observation["block_num"],
            observation["par_num"],
            observation["line_num"]
        )

        if key not in groups:
            groups[key] = []

        groups[key].append(observation)

    # Validate spatial alignment
    for key, group in groups.items():

        group.sort(key=lambda item: item["x"])

    return groups


# 4. Calculate horizontal overlap
def horizontal_overlap(box_a, box_b):

    right_a = box_a["x"] + box_a["width"]

    right_b = box_b["x"] + box_b["width"]

    overlap = max(
        0,
        min(right_a, right_b) - max(box_a["x"], box_b["x"])
    )

    return overlap


# 5. Calculate vertical overlap
def vertical_overlap(box_a, box_b):

    bottom_a = box_a["y"] + box_a["height"]

    bottom_b = box_b["y"] + box_b["height"]

    overlap = max(
        0,
        min(bottom_a, bottom_b) - max(box_a["y"], box_b["y"])
    )

    return overlap


# 6. Calculate vertical overlap ratio
def vertical_overlap_ratio(box_a, box_b):

    overlap = vertical_overlap(box_a, box_b)

    smaller_height = min(
        box_a["height"],
        box_b["height"]
    )

    if smaller_height == 0:
        return 0

    return overlap / smaller_height


# 7. Calculate vertical centre distance
def vertical_alignment(box_a, box_b):

    centre_a = box_a["centre_y"]

    centre_b = box_b["centre_y"]

    return abs(centre_a - centre_b)


# 8. Calculate normalized vertical alignment score
def vertical_alignment_score(box_a, box_b):

    distance = vertical_alignment(box_a, box_b)

    avg_height = (
        box_a["height"] + box_b["height"]
    ) / 2

    if avg_height == 0:
        return 0

    score = 1 - (distance / avg_height)

    return max(0, score)


# 9. Validate vertical alignment
def validate_vertical_alignment(box_a, box_b):

    alignment = vertical_alignment_score(box_a, box_b)

    overlap_ratio = vertical_overlap_ratio(box_a, box_b)

    return {
        "alignment": alignment,
        "overlap_ratio": overlap_ratio,
        "valid": alignment >= 0.75 and overlap_ratio >= 0.70
    }


# 10. Reconstruct individual text lines
def reconstruct_lines(groups):

    lines = []

    for group in groups.values():

        if not group:
            continue

        sorted_group = sorted(
            group,
            key=lambda item: item["x"]
        )

        sentence = " ".join(
            item["text"] for item in sorted_group
        )

        line_x = min(item["x"] for item in sorted_group)

        line_y = min(item["y"] for item in sorted_group)

        line_right = max(
            item["x"] + item["width"] for item in sorted_group
        )

        line_bottom = max(
            item["y"] + item["height"] for item in sorted_group
        )

        line_width = line_right - line_x

        line_height = line_bottom - line_y

        lines.append({
            "x": line_x,
            "y": line_y,
            "width": line_width,
            "height": line_height,
            "text": sentence
        })

    sort_lines_by_y = sorted(
        lines,
        key=lambda item: item["y"]
    )

    return sort_lines_by_y


# 11. Main execution
if __name__ == "__main__":

    observations = extract_observations("screenshot.png")

    filtered = filter_obeservation(observations, 40)

    groups = group_words_into_lines(filtered)

    reconstructed = reconstruct_lines(groups)

    print("\n========== RECONSTRUCTED LINES ==========\n")

    for line in reconstructed:

        print(
            f"X={line['x']} | "
            f"Y={line['y']} | "
            f"W={line['width']} | "
            f"H={line['height']} | "
            f"Text={line['text']}"
        )
