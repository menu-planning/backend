from typing import Any

from pydantic import BaseModel
from src.contexts.iam.core.adapters.api_schemas.entities.user import ApiRole
from src.contexts.iam.core.domain.commands import AssignRoleToUser


class ApiAssignRoleToUser(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to assign a role to a user via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user.
        role (Role): The role to assign to the user.

    Methods:
        to_domain() -> Any:
            Converts the instance to a domain model object for assigning a role to a user.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    user_id: str
    role: ApiRole

    def to_domain(self) -> Any:
        try:
            return AssignRoleToUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e
