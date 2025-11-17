import json
import logging
import re
from typing import Any

import requests

# constants
ALL_DATA_FIELDS = "FB_PUBLIC_LOAD_DATA_"
FORM_SESSION_TYPE_ID = 8
ANY_TEXT_FIELD = "ANY TEXT!!"


# ---------------- FETCHING ---------------- #

logger = logging.getLogger(__name__)


def get_form_response_url(url: str) -> str:
    """Convert a normal Google Form URL to a formResponse URL."""
    url = url.replace("/viewform", "/formResponse")
    if not url.endswith("/formResponse"):
        if not url.endswith("/"):
            url += "/"
        url += "formResponse"
    return url


def extract_script_variables(name: str, html: str) -> Any | None:
    """
    Extracts the value of a JS variable from the page HTML.
    Example: var FB_PUBLIC_LOAD_DATA_ = [...];
    """
    pattern = re.compile(rf"var\s+{re.escape(name)}\s*=\s*(.*?);", re.DOTALL)
    match = pattern.search(html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def fetch_form_data(url: str) -> list | None:
    """
    Fetch the raw_questions form data from a Google Form URL.

    Returns:
        A Python list representing the internal Google Form data structure,
        or None if request fails or structure not found.
    """
    url = get_form_response_url(url)
    try:
        response = requests.get(url, timeout=10)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch form: {e}")

        return None

    if response.status_code != 200:
        logger.error(f"HTTP {response.status_code}: Cannot fetch form data.")

        return None

    data = extract_script_variables(ALL_DATA_FIELDS, response.text)
    if not data:
        logger.error("Cannot extract FB_PUBLIC_LOAD_DATA_. Possibly login required")
        return None

    return data


# ---------------- PARSING ---------------- #


def parse_entries(form_data: list, only_required: bool = False) -> list[dict]:
    """
    Parse form entries from FB_PUBLIC_LOAD_DATA_ structure.

    Args:
        form_data: Raw data structure extracted from the Google Form.
        only_required: If True, only include required fields.

    Returns:
        A list of parsed field dictionaries.
    """
    if not form_data or not form_data[1] or not form_data[1][1]:
        logger.error("Invalid form data structure.")
        return []

    entries_data = form_data[1][1]
    parsed_entries = []
    page_count = 0

    for entry in entries_data:
        entry_name = entry[1]
        entry_type_id = entry[3]

        # Skip section headers
        if entry_type_id == FORM_SESSION_TYPE_ID:
            page_count += 1
            continue

        # Parse sub-entries
        for sub_entry in entry[4]:
            field_info = {
                "id": sub_entry[0],
                "container_name": entry_name,
                "type": entry_type_id,
                "required": sub_entry[2] == 1,
                "name": (
                    " - ".join(sub_entry[3])
                    if (len(sub_entry) > 3 and sub_entry[3])
                    else None
                ),
                "options": (
                    [(x[0] or ANY_TEXT_FIELD) for x in sub_entry[1]]
                    if sub_entry[1]
                    else None
                ),
            }
            if only_required and not field_info["required"]:
                continue
            parsed_entries.append(field_info)

    # Handle email collection
    try:
        email_collection_type = form_data[1][10][6]
        if email_collection_type > 1:
            parsed_entries.append(
                {
                    "id": "emailAddress",
                    "container_name": "Email Address",
                    "type": "required",
                    "required": True,
                    "options": "email address",
                }
            )
    except (IndexError, TypeError):
        pass

    # Add page history (for multipage forms)
    if page_count > 0:
        parsed_entries.append(
            {
                "id": "pageHistory",
                "container_name": "Page History",
                "type": "required",
                "required": False,
                "options": "from 0 to (number of page - 1)",
                "default_value": ",".join(map(str, range(page_count + 1))),
            }
        )

    return parsed_entries


def fill_form_entries(entries, fill_algorithm):
    """Fill form entries with fill_algorithm"""
    for entry in entries:
        if entry.get("default_value"):
            continue
        # remove ANY_TEXT_FIELD from options to prevent choosing it
        options = (entry["options"] or [])[::]
        if ANY_TEXT_FIELD in options:
            options.remove(ANY_TEXT_FIELD)
            entry["default_value"] = fill_algorithm(
                entry["type"],
                entry["id"],
                options,
                required=entry["required"],
                entry_name=entry["container_name"],
            )
    return entries


# ------ OUTPUT ------ #
def parse_form_entries(url: str, only_required: bool = False) -> list[dict]:
    """
    Controller-level function that returns already parsed Google Form fields.
    Combines both fetching (HTML → JSON) and parsing (JSON → structured fields).

    Args:
        url (str): Google Form URL (either /viewform or /formResponse)
        only_required (bool): If True, include only required fields in the result.

    Returns:
        List[Dict]: A list of parsed form entries with metadata.
            Example structure:
            [
                {
                    "id": "123456",
                    "container_name": "Full Name",
                    "type": 0,
                    "required": True,
                    "name": None,
                    "options": None,
                    "default_value": None,
                },
                ...
            ]
    Raises:
        ValueError: If form data could not be fetched or parsed.
    """

    # Step 1: Fetch raw_questions form data from the given URL
    form_data = fetch_form_data(url)
    if not form_data:
        raise ValueError(
            "Failed to fetch or parse Google Form data. Check URL or form access settings."
        )

    # Step 2: Parse entries (questions and fields) from the raw_questions data
    entries = parse_entries(form_data, only_required=only_required)

    # Step 3: Return parsed entries to controller or API
    return entries


def get_form_submit_request(
    url: str,
    output="console",
    only_required=False,
    with_comment=True,
    fill_algorithm=None,
):
    """Get form request body data"""
    entries = parse_form_entries(url=url, only_required=only_required)

    if fill_algorithm:
        entries = fill_form_entries(entries, fill_algorithm)
    if not entries:
        return None
    result = generate_form_request_dict(entries, with_comment)
    if output == "console":
        print(result)
    elif output == "return":
        return result
    else:
        # save as file
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
            logger.info(f"Form saved to {output}")
            f.close()
    return None


def generate_form_request_dict(entries, with_comment: bool = True):
    """Generate a dict of form request data from entries"""
    result = "{\n"
    entry_id = 0
    for entry in entries:
        if with_comment:
            # gen name of entry
            result += f"    # {entry['container_name']}{(': ' + entry['name'])
            if entry.get('name') else ''}{' (required)' * entry['required']}\n"
            # gen all options (if any)
            if entry["options"]:
                result += f"    #   Options: {entry['options']}\n"
            else:
                result += f"    #   Option: {get_form_type_value_rule(entry['type'])}\n"
        # gen entry id
        entry_id += 1
        default_value = entry.get("default_value", "")
        default_value = json.dumps(default_value, ensure_ascii=False)

        if entry.get("type") == "required":
            result += f'    "{entry["id"]}": {default_value}'
        else:
            result += f'    "entry.{entry["id"]}": {default_value}'
        result += f"{(entry_id < len(entries)) * ','}\n"
    # remove the last comma
    result += "}"
    return result


def get_form_type_value_rule(type_id):
    """------ TYPE ID ------
    0: Short answer
    1: Paragraph
    2: Multiple choice
    3: Dropdown
    4: Checkboxes
    5: Linear scale
    7: Grid choice
    9: Date
    10: Time
    """
    if type_id == 9:
        return "YYYY-MM-DD"
    if type_id == 10:
        return "HH:MM (24h format)"
    return "any text"


def main():
    url = input("Enter the Google Form URL: ").strip()
    output = input("Enter output file path (leave empty for console): ").strip()
    only_required = input("Use only required fields? (y/n): ").strip().lower() == "y"
    add_comments = input("Add comments for each field? (y/n): ").strip().lower() != "n"

    if not output:
        output = "console"

    # Call your main function
    get_form_submit_request(url, output, only_required, add_comments)


if __name__ == "__main__":
    main()
