from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiRole
from src.contexts.iam.core.domain.commands import AssignRoleToUser
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiAssignRoleToUser(BaseApiCommand[AssignRoleToUser]):
    """
    A Pydantic model representing and validating the data required
    to assign a role to a user via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user.
        role (ApiRole): The role to assign to the user.

    Methods:
        to_domain() -> AssignRoleToUser:
            Converts the instance to a domain model object
            for assigning a role to a user.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    user_id: UUIDIdRequired
    role: ApiRole

    def to_domain(self) -> AssignRoleToUser:
        try:
            return AssignRoleToUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            error_message = f"Failed to convert to domain: {e}"
            raise ValueError(error_message) from e
