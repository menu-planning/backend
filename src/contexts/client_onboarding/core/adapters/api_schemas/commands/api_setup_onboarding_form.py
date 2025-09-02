"""
API Command Schema: Setup Onboarding Form

Pydantic model for setting up TypeForm webhook integration.
Maps HTTP requests to domain commands for form setup operations.
"""

from pydantic import Field, HttpUrl, field_validator
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import (
    TypeformUrlParser,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    MODEL_CONFIG,
    BaseApiCommand,
)


class ApiSetupOnboardingForm(BaseApiCommand[SetupOnboardingFormCommand]):
    """API command schema for creating and setting up TypeForm webhook integration.

    Maps HTTP POST requests to domain SetupOnboardingFormCommand.
    Normalizes TypeForm URLs or IDs into canonical typeform_id format.

    Attributes:
        typeform_url: TypeForm URL or form ID (1-300 characters, not auto-stripped)
        webhook_url: URL to receive webhook notifications (valid HTTP/HTTPS URL)
        auto_activate: Whether to automatically activate the form (default: True)
        form_title: Optional custom title (max 200 chars, not persisted)
        form_description: Optional description (max 500 chars, not persisted)

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        String whitespace not auto-stripped to allow custom validation messages.
        TypeForm URL validation extracts and normalizes form IDs.
    """

    # Do not auto-strip strings at the model level so whitespace-only inputs
    # reach our custom validator (tests expect our custom error message for that case)
    model_config = MODEL_CONFIG.copy()
    model_config["str_strip_whitespace"] = False

    typeform_url: str = Field(
        ..., min_length=1, max_length=300, description="Typeform URL or form ID"
    )
    webhook_url: HttpUrl = Field(
        ..., description="URL to receive webhook notifications"
    )
    auto_activate: bool = Field(
        default=True, description="Whether to automatically activate the form"
    )
    form_title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional custom title (not persisted)",
    )
    form_description: str | None = Field(
        default=None, max_length=500, description="Optional description (not persisted)"
    )

    @field_validator("typeform_url")
    @classmethod
    def validate_and_extract_typeform_id(cls, value: str) -> str:
        """Validate and extract TypeForm ID from URL or ID string.

        Args:
            value: TypeForm URL or form ID to validate

        Returns:
            Normalized TypeForm ID string

        Raises:
            ValidationError: If TypeForm ID format is invalid
        """
        form_id = TypeformUrlParser.extract_form_id(value)
        return TypeformUrlParser.validate_form_id_format(form_id)

    @property
    def typeform_id(self) -> str:
        """Get the extracted TypeForm ID for internal use.

        Returns:
            Extracted TypeForm ID from the provided URL or ID
        """
        return TypeformUrlParser.extract_form_id(self.typeform_url)

    def to_domain(self, *, user_id: str) -> SetupOnboardingFormCommand:
        """Map API command to domain command.

        Args:
            user_id: User ID setting up the form

        Returns:
            SetupOnboardingFormCommand: Domain command for form setup
        """
        return SetupOnboardingFormCommand(
            user_id=user_id,
            typeform_id=self.typeform_id,
            webhook_url=str(self.webhook_url),
            auto_activate=bool(self.auto_activate),
        )
