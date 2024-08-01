from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator
from src.contexts.products_catalog.shared.domain.entities.product import Product


def _score_range(v: Any):
    if v is not None and (v < 0 or v > 100):
        raise ValueError(f"Score must be an int from 0 to 100: {v}")
    return v


ScoreValue = Annotated[float | None, BeforeValidator(_score_range)]


def _timestamp_check(v: Any):
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e
    return v


CreatedAtValue = Annotated[datetime | None, BeforeValidator(_timestamp_check)]


def _unique_barcode(v: Any):
    if not Product.is_barcode_unique(v):
        raise ValueError(f"Barcode must be 13 digits: {v}")
    return v


UniqueBarcode = Annotated[str | None, BeforeValidator(_unique_barcode)]
