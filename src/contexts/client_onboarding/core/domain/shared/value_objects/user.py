from src.contexts.client_onboarding.core.domain.shared.value_objects.role import Role
from src.contexts.seedwork.domain.value_objects.user import SeedUser


class User(SeedUser[Role]):
    """Client onboarding user value object.

    Extends the base user with client onboarding specific role support.
    """
