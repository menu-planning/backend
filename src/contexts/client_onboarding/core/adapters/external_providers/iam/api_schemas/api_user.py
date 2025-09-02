"""
External Provider API Schema: User

Pydantic model for user data in cross-context communication.
Maps between domain User objects and ORM models for IAM integration.
"""

from src.contexts.client_onboarding.core.adapters.external_providers.iam.api_schemas.api_role import (
    ApiRole,
)
from src.contexts.client_onboarding.core.domain.shared.value_objects.user import User
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)


class ApiUser(ApiSeedUser["ApiUser", ApiRole, User, UserSaModel]):
    """API schema for user data in cross-context communication.

    Extends ApiSeedUser with IAM-specific metadata for client onboarding context.
    Includes IAM-specific fields like version control and soft delete flags while
    maintaining compatibility with the base user schema patterns.

    Notes:
        Boundary contract for cross-context communication.
        Handles user-role mapping for IAM integration.
    """

    def to_domain(self) -> User:
        """Convert the ApiUser instance to a User domain object.

        Returns:
            User: Domain user object with ID and roles
        """
        return User(
            id=self.id, roles=frozenset([role.to_domain() for role in self.roles])
        )
