from pydantic import Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.client_onboarding.core.domain.commands.delete_onboarding_form import (
    DeleteOnboardingFormCommand,
)


class ApiDeleteOnboardingForm(BaseApiCommand[DeleteOnboardingFormCommand]):
    """API command to delete (soft-delete) an onboarding form."""

    form_id: int = Field(..., gt=0, description="ID of the form to delete")

    def to_domain(self, *, user_id: str) -> DeleteOnboardingFormCommand:  # type: ignore[override]
        return DeleteOnboardingFormCommand(
            user_id=user_id,
            form_id=int(self.form_id),
        )


