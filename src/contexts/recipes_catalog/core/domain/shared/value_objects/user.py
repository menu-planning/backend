"""User value object for recipes catalog domain."""
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.seedwork.domain.value_objects.user import SeedUser


class User(SeedUser[Role]):
    """User value object with recipes catalog specific role.

    Extends base user with catalog-specific role capabilities.
    """
    pass
