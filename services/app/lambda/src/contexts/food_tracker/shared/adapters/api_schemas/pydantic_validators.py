from typing import Annotated, Any

from pydantic import BeforeValidator


def value_cannot_be_empty(v: Any):
    if len(v) < 1:
        raise ValueError(f"Cfe key cannot be empty: {v}")
    return str(v)


NonEmptyStr = Annotated[str, BeforeValidator(value_cannot_be_empty)]
