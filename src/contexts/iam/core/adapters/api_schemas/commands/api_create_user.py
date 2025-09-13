from typing import Annotated

from pydantic import Field
from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser
from src.contexts.iam.core.domain.commands import CreateUser
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiCreateUser(BaseApiCommand[CreateUser]):
    """API schema for user creation command.

    Attributes:
        user_id: UUID v4 of the user to create.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
    """

    user_id: UUIDIdRequired

    def to_domain(self) -> CreateUser:
        """Map API command to domain command.

        Returns:
            Domain command for user creation.

        Raises:
            ValidationConversionError: If conversion fails or validation fails.
        """
        try:
            return CreateUser(user_id=self.user_id)
        except Exception as e:
            error_message = f"Failed to convert ApiCreateUser to domain command: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)],
            ) from e
