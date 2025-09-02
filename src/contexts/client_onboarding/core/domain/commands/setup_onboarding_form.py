from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class SetupOnboardingFormCommand(Command):
    """Command to set up a new onboarding form with webhook integration.

    Args:
        user_id: User identifier who owns the form.
        typeform_id: Typeform form identifier.
        webhook_url: Webhook URL for receiving form submissions. If None, uses default.
        auto_activate: Whether to automatically activate the form after setup.

    Notes:
        Triggers the process of configuring a TypeForm webhook and creating
        the necessary database records.
    """

    user_id: str
    typeform_id: str
    webhook_url: str | None = None
    auto_activate: bool = True
