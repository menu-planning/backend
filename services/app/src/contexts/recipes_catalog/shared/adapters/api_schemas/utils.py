def parse_tags(tag_string: str | None) -> list[tuple]:
    """
    Parses a tag string in the format 'key:value1|value2,key2:value3'
    into a dictionary where values are lists.
    Args:
        tag_string (str): The input tag string.
    Returns:
        dict: A dictionary with keys and their corresponding list of values.
    """
    result = []
    if not tag_string:
        return result
    key_value_pairs = tag_string.split("|")
    for pair in key_value_pairs:
        key, value = pair.split(":")
        result.append((key, value))
    return result
