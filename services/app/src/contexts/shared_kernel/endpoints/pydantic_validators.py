from typing import Annotated, Any

from pydantic import AfterValidator


def _non_negative_float(v: Any):
    if v is None:
        return v
    assert v >= 0, f"{v} is not a non-negative float"
    return float(v)


MyNullableNonNegativeFloat = Annotated[float, AfterValidator(_non_negative_float)]
