from decimal import Decimal
from attrs import frozen, field

@frozen
class YieldRate:
    """
    A factor between 0 and 1 representing
    the *edible* fraction of the purchased weight.
    e.g. YieldRate(Decimal('0.75')) means 75% usable,
    so you’d over-buy by ~1/0.75 ≈ 1.33×.
    """
    factor: Decimal

    # def __attrs_post_init__(self):
    #     if not (Decimal("0") < self.factor <= Decimal("1")):
    #         raise ValueError("YieldRate.factor must be >0 and ≤1")
