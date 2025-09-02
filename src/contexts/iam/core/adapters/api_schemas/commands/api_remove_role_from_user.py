from typing import Annotated

from pydantic import Field
from src.contexts.iam.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.iam.core.domain.commands import RemoveRoleFromUser
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiRemoveRoleFromUser(BaseApiCommand[RemoveRoleFromUser]):
    """API schema for role removal command.
    
    Attributes:
        user_id: UUID v4 of the user to remove the role from.
        role: Role to remove from the user.
    
    Notes:
        Boundary contract only; domain rules enforced in application layer.
    """

    user_id: UUIDIdRequired
    role: Annotated[ApiRole, Field(..., description="Role to remove from user")]

    def to_domain(self) -> RemoveRoleFromUser:
        """Map API command to domain command.
        
        Returns:
            Domain command for role removal.
        
        Raises:
            ValidationConversionError: If conversion fails or validation fails.
        """
        try:
            return RemoveRoleFromUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            error_message = f"Failed to convert ApiRemoveRoleFromUser to domain command: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)]
            ) from e
