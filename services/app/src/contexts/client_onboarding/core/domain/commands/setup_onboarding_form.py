from typing import Optional
from src.contexts.seedwork.shared.domain.commands.command import Command
from attrs import frozen

@frozen(kw_only=True)
class SetupOnboardingFormCommand(Command):
    """
    Command to set up a new onboarding form with webhook integration.
    
    This command triggers the process of configuring a TypeForm webhook
    and creating the necessary database records.
    """
    user_id: int
    typeform_id: str
    webhook_url: Optional[str] = None
    auto_activate: bool = True