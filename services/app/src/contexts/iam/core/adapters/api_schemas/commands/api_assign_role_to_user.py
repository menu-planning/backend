from pydantic import Field, field_validator
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.iam.core.adapters.api_schemas.root_aggregate.user import ApiRole
from src.contexts.iam.core.domain.commands import AssignRoleToUser
from src.db.base import SaBase


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
            Converts the instance to a domain model object for assigning a role to a user.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    user_id: UUIDId
    role: ApiRole

    def to_domain(self) -> AssignRoleToUser:
        try:
            return AssignRoleToUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
