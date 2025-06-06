from typing import cast

from src.contexts.recipes_catalog.core.domain.value_objects.role import Role
from src.contexts.recipes_catalog.core.domain.value_objects.user import User
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.user import ApiSeedUser
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.iam.core.adapters.ORM.sa_models.user import UserSaModel


class ApiUser(ApiSeedUser):
    """
    A Pydantic model representing and validating a user in the recipes catalog context.

    This model inherits from ApiSeedUser and overrides the domain type to use the
    recipes catalog specific User value object.
    """

    def to_domain(self) -> User:
        """Converts the instance to a domain model object."""
        return cast(User, super().to_domain())
    
    @classmethod
    def from_domain(cls, domain_obj: User) -> "ApiUser":
        """Creates an instance of `ApiUser` from a domain model object."""
        base = super().from_domain(domain_obj)
        return cast(ApiUser, base)