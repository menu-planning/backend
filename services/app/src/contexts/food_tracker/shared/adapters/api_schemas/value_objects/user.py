from typing import ClassVar

from src.contexts.food_tracker.shared.domain.value_objects.role import Role
from src.contexts.food_tracker.shared.domain.value_objects.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.value_ojbects.user import (
    ApiSeedUser,
)
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser


class ApiUser(ApiSeedUser):
    domain_user_type: ClassVar[type[SeedUser]] = User
    role_type: ClassVar[type[SeedRole]] = Role
