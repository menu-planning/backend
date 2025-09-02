from typing import Annotated

from pydantic import Field
from src.contexts.iam.core.adapters.api_schemas.value_objects.api_role import ApiRole
from src.contexts.iam.core.domain.commands import AssignRoleToUser
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiAssignRoleToUser(BaseApiCommand[AssignRoleToUser]):
    """API schema for role assignment command.
    
    Attributes:
        user_id: UUID v4 of the user to assign the role to.
        role: Role to assign to the user.
    
    Notes:
        Boundary contract only; domain rules enforced in application layer.
    """

    user_id: UUIDIdRequired
    role: Annotated[ApiRole, Field(..., description="Role to assign to user")]

    def to_domain(self) -> AssignRoleToUser:
        """Map API command to domain command.
        
        Returns:
            Domain command for role assignment.
        
        Raises:
            ValidationConversionError: If conversion fails or validation fails.
        """
        try:
            return AssignRoleToUser(user_id=self.user_id, role=self.role.to_domain())
        except Exception as e:
            error_message = f"Failed to convert ApiAssignRoleToUser to domain command: {e}"
            raise ValidationConversionError(
                message=error_message,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self,
                validation_errors=[str(e)]
            ) from e
