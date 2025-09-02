"""
API Command Schema: Delete Onboarding Form

Pydantic model for delete onboarding form API requests.
Maps HTTP requests to domain commands for form deletion operations.
"""

from pydantic import Field
from src.contexts.client_onboarding.core.domain.commands.delete_onboarding_form import (
    DeleteOnboardingFormCommand,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiDeleteOnboardingForm(BaseApiCommand[DeleteOnboardingFormCommand]):
    """API command schema for deleting (soft-deleting) an onboarding form.

    Maps HTTP DELETE requests to domain DeleteOnboardingFormCommand.
    Performs soft deletion by updating form status rather than removing records.

    Attributes:
        form_id: Internal form ID to delete (must be positive integer)

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Soft deletion preserves data integrity and audit trails.
    """

    form_id: int = Field(..., gt=0, description="Internal form ID to delete")

    def to_domain(self, *, user_id: str) -> DeleteOnboardingFormCommand:  # type: ignore[override]
        """Map API command to domain command.

        Args:
            user_id: User ID performing the deletion operation

        Returns:
            DeleteOnboardingFormCommand: Domain command for form deletion
        """
        return DeleteOnboardingFormCommand(
            user_id=user_id,
            form_id=int(self.form_id),
        )
