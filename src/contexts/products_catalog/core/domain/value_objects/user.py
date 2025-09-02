"""User value object for Products Catalog domain.

Extends the base user value object with catalog-specific functionality.
"""
from src.contexts.seedwork.domain.value_objects.user import SeedUser


class User(SeedUser):
    """Products Catalog user value object.
    
    Extends the base SeedUser with catalog-specific functionality.
    Inherits all user fields and methods from the seed user value object.
    
    Notes:
        Immutable. Equality by value (inherited from SeedUser).
        Used for user identification and permission checking in catalog operations.
    """
    pass
