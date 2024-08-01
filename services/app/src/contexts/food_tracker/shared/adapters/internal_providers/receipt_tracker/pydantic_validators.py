from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator
from src.contexts.shared_kernel.domain.enums import Month


def _rating_range(v: Any):
    if v is None or v not in range(0, 6):
        raise ValueError(f"Ranting must be an int from 0 to 5: {v}")
    return v


RatingValue = Annotated[int, BeforeValidator(_rating_range)]


def _month_range(v: Any):
    if v is None or v not in range(1, 13):
        raise ValueError(f"Month must be an int from 1 to 12: {v}")
    return v


MonthValue = Annotated[Month | None, BeforeValidator(_month_range)]


def _timestamp_check(v: Any):
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e


CreatedAtValue = Annotated[datetime | None, BeforeValidator(_timestamp_check)]


def _average_rating_range(v: Any):
    if v is None or v < 0 or v > 5:
        raise ValueError(f"Ranting must be an float from 0 to 5: {v}")
    return v


AverageRatingValue = Annotated[float, BeforeValidator(_average_rating_range)]
