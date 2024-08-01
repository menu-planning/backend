from __future__ import annotations

import logging
from enum import Enum

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.logging.logger import logger


class CRNRegion(str, Enum):
    """the type of a CRN"""

    CRN_1 = "CRN-1"
    CRN_2 = "CRN-2"
    CRN_3 = "CRN-3"
    CRN_4 = "CRN-4"
    CRN_5 = "CRN-5"
    CRN_6 = "CRN-6"
    CRN_7 = "CRN-7"
    CRN_8 = "CRN-8"
    CRN_9 = "CRN-9"
    CRN_10 = "CRN-10"
    CRN_11 = "CRN-11"

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, CRNRegion) and self.value == __o.value


@frozen(hash=True)
class CRN(ValueObject):
    """the CRN of a user"""

    number: str
    region: CRNRegion


@frozen(hash=True)
class ProductNotes(ValueObject):
    """the notes of a user about a product"""

    product_id: str
    like: bool | None = None
    notes: str | None = None


@frozen(hash=True)
class BrandNotes(ValueObject):
    """the notes of a user about a brand"""

    brand: str
    like: bool | None = None
    notes: str | None = None
