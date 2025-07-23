from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.api_seed_user import ApiSeedUser

from .api_role import ApiRole


class ApiUser(ApiSeedUser["ApiUser", ApiRole, User, UserSaModel]):
    """
    IAM provider specific user model that extends ApiSeedUser with additional IAM metadata.
    
    Includes IAM-specific fields like version control and soft delete flags while
    maintaining compatibility with the base user schema patterns.
    """
    
    def to_domain(self) -> User:
        """Convert the ApiUser instance to a User domain object."""
        return User(
            id=self.id,
            roles=frozenset([role.to_domain() for role in self.roles])
        )