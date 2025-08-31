from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class SetupOnboardingFormCommand(Command):
    """
    Command to set up a new onboarding form with webhook integration.

    This command triggers the process of configuring a TypeForm webhook
    and creating the necessary database records.
    """

    user_id: str
    typeform_id: str
    webhook_url: str | None = None
    auto_activate: bool = True
