def get_form_type_description(type_id: int) -> dict:
    """
    Returns a dictionary containing the type_id and a human-readable description
    of a Google Form question type. If the type_id is unknown, it returns
    {'type_id': <id>, 'description': 'Type: Unknown'}.
    """
    type_descriptions = {
        0: "Short answer (single-line text input)",
        1: "Paragraph (multi-line text input)",
        2: "Multiple choice (select one option)",
        3: "Dropdown (select one option from a list)",
        4: "Checkboxes (select multiple options)",
        5: "Linear scale (rating scale, e.g., 1–5)",
        7: "Grid choice (matrix of options)",
        9: "Date (format: YYYY-MM-DD)",
        10: "Time (format: HH:MM, 24-hour format)",
    }

    description = type_descriptions.get(type_id, "Type: Unknown")
    return {"type_id": type_id, "description": description}
