from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.iam.api_schemas.api_role import (
    ApiRole,
)
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)


class ApiUser(ApiSeedUser["ApiUser", ApiRole, User, UserSaModel]):
    """IAM provider specific user model for recipes catalog context.

    Extends ApiSeedUser with additional IAM metadata while maintaining
    compatibility with base user schema patterns. Used for cross-context
    user data exchange between IAM and recipes catalog.

    Attributes:
        Inherits all fields from ApiSeedUser including id and roles.

    Notes:
        Boundary contract for IAM user data in recipes catalog context.
        Maintains compatibility with base user schema patterns.
    """

    def to_domain(self) -> User:
        """Convert API schema instance to domain model object.

        Returns:
            User domain object with roles converted from API format.

        Notes:
            Converts each role using role.to_domain() method.
            Maintains frozenset structure for roles.
        """
        return User(
            id=self.id, roles=frozenset([role.to_domain() for role in self.roles])
        )
