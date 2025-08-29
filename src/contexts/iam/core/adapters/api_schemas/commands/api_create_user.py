from src.contexts.iam.core.domain.commands import CreateUser
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiCreateUser(BaseApiCommand[CreateUser]):
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

    user_id: UUIDIdRequired

    def to_domain(self) -> CreateUser:
        try:
            return CreateUser(user_id=self.user_id)
        except Exception as e:
            error_message = f"Failed to convert to domain: {e}"
            raise ValueError(error_message) from e
