from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator


def _timestamp_check(v: Any):
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e
    return v


CreatedAtValue = Annotated[datetime | None, BeforeValidator(_timestamp_check)]


def _non_negative_float(v: Any):
    if v is None:
        return v
    assert v >= 0, f"{v} is not a non-negative float"
    return float(v)


MyNullableNonNegativeFloat = Annotated[float, BeforeValidator(_non_negative_float)]
