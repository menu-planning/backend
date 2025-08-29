from pydantic import Field, HttpUrl, field_validator

from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import (
    TypeformUrlParser,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    MODEL_CONFIG,
    BaseApiCommand,
)


class ApiSetupOnboardingForm(BaseApiCommand[SetupOnboardingFormCommand]):
    """API command for creating and setting up a Typeform webhook for onboarding.

    This mirrors the domain `SetupOnboardingFormCommand` and normalizes a provided
    Typeform URL or ID into a canonical `typeform_id`.
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
        """Normalize input to a valid Typeform ID string."""
        form_id = TypeformUrlParser.extract_form_id(value)
        return TypeformUrlParser.validate_form_id_format(form_id)

    @property
    def typeform_id(self) -> str:
        return TypeformUrlParser.extract_form_id(self.typeform_url)

    def to_domain(self, *, user_id: str) -> SetupOnboardingFormCommand:
        return SetupOnboardingFormCommand(
            user_id=user_id,
            typeform_id=self.typeform_id,
            webhook_url=str(self.webhook_url),
            auto_activate=bool(self.auto_activate),
        )
