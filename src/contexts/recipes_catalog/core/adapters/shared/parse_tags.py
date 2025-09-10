"""Utilities for parsing tag strings used in filter/query endpoints."""


def parse_tags(tag_string: str | None) -> dict[str, list[str]]:
    """Parse tag strings into a structured format.

    Handles both key-value pairs and global tags:
    - Key-value pairs: "cuisine:italian|mediterranean" → {"cuisine": ["italian", "mediterranean"]}
    - Global tags: "quick,easy,healthy" → {"global": ["quick", "easy", "healthy"]}
    - Mixed: "cuisine:italian,quick,meal_type:breakfast" → {"cuisine": ["italian"], "global": ["quick"], "meal_type": ["breakfast"]}

    Args:
        tag_string: Input tag string with pairs separated by ',' or '|', key and value by ':'.

    Returns:
        A dictionary mapping keys to lists of values. Global tags (no key) are mapped to "global".
    """
    result = {}
    if not tag_string:
        return result

    # Split by comma first to handle mixed formats
    groups = tag_string.split(",")

    for group in groups:
        group = group.strip()
        if not group:
            continue

        if ":" in group:
            # Key-value pair: "cuisine:italian|mediterranean"
            key, values_str = group.split(":", 1)
            key = key.strip()
            values = [v.strip() for v in values_str.split("|") if v.strip()]
            if key not in result:
                result[key] = []
            result[key].extend(values)
        else:
            # Global tag: "quick,easy,healthy"
            values = [v.strip() for v in group.split("|") if v.strip()]
            if "global" not in result:
                result["global"] = []
            result["global"].extend(values)

    return result
