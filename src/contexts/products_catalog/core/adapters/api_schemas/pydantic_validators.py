from typing import Annotated, Any

from pydantic import AfterValidator
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product

MIN_SCORE = 0
MAX_SCORE = 100


def _score_range(v: Any):
    if v is not None and (v < MIN_SCORE or v > MAX_SCORE):
        error_msg = f"Score must be an int from {MIN_SCORE} to {MAX_SCORE}: {v}"
        raise ValueError(error_msg)
    return v


ScoreValue = Annotated[float | None, AfterValidator(_score_range)]


def _unique_barcode(v: Any):
    if not Product.is_barcode_unique(v):
        error_msg = f"Barcode must be 13 digits: {v}"
        raise ValueError(error_msg)
    return v


UniqueBarcode = Annotated[str | None, AfterValidator(_unique_barcode)]
