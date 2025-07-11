from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.iam.core.adapters.api_schemas.root_aggregate.user import ApiRole
from src.contexts.iam.core.domain.commands import RemoveRoleFromUser


class ApiRemoveRoleFromUser(BaseApiCommand[RemoveRoleFromUser]):
    """
    A Pydantic model representing and validating the data required
    to remove a role from a user via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user.
        role (ApiRole): The role to remove from the user.

    Methods:
        to_domain() -> RemoveRoleFromUser:
            Converts the instance to a domain model object for removing a role from a user.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    user_id: UUIDIdRequired
    role: ApiRole


    def to_domain(self) -> RemoveRoleFromUser:
        try:
            return RemoveRoleFromUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
