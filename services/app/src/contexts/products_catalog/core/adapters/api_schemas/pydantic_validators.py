from datetime import datetime
from typing import Annotated, Any

from pydantic import BeforeValidator
from src.contexts.products_catalog.core.domain.entities.product import Product


def _score_range(v: Any):
    if v is not None and (v < 0 or v > 100):
        raise ValueError(f"Score must be an int from 0 to 100: {v}")
    return v


ScoreValue = Annotated[float | None, BeforeValidator(_score_range)]


def _unique_barcode(v: Any):
    if not Product.is_barcode_unique(v):
        raise ValueError(f"Barcode must be 13 digits: {v}")
    return v


UniqueBarcode = Annotated[str | None, BeforeValidator(_unique_barcode)]
