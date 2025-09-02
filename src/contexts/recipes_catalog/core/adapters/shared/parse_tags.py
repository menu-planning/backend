"""Utilities for parsing tag strings used in filter/query endpoints."""

def parse_tags(tag_string: str | None) -> list[tuple]:
    """Parse 'key:value|key2:value2' style string into a list of (key, value).

    Args:
        tag_string: Input tag string with pairs separated by '|', key and value by ':'.

    Returns:
        A list of (key, value) tuples in the same order as provided.
    """
    result = []
    if not tag_string:
        return result
    key_value_pairs = tag_string.split("|")
    for pair in key_value_pairs:
        key, value = pair.split(":", 1)
        result.append((key, value))
    return result
