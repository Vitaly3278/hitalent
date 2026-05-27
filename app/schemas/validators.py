def trim_non_empty(value: str, field_name: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError(f"{field_name} must not be empty")
    if len(trimmed) > 200:
        raise ValueError(f"{field_name} must be at most 200 characters")
    return trimmed
