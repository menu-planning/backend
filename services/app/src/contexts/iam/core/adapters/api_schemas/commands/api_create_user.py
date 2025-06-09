from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.iam.core.domain.commands import CreateUser
from src.db.base import SaBase
from pydantic import Field, field_validator


class ApiCreateUser(BaseCommand[CreateUser, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to create a new user via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user. (required)

    Methods:
        to_domain() -> CreateUser:
            Converts the instance to a domain model object for creating a user.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    user_id: str = Field(..., min_length=1, description="User ID (must not be empty)")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate that user_id is not empty."""
        if not v.strip():
            raise ValueError("user_id must not be empty")
        return v

    def to_domain(self) -> CreateUser:
        try:
            return CreateUser(user_id=self.user_id)
        except Exception as e:
            raise ValueError(f"Failed to convert to domain: {e}") from e

    @classmethod
    def from_domain(cls, domain_obj: CreateUser) -> "ApiCreateUser":
        return cls(user_id=domain_obj.user_id)
