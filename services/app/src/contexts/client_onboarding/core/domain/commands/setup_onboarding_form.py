from typing import Optional
from src.contexts.seedwork.shared.domain.commands.command import Command


class SetupOnboardingFormCommand(Command):
    """
    Command to set up a new onboarding form with webhook integration.
    
    This command triggers the process of configuring a TypeForm webhook
    and creating the necessary database records.
    """
    
    def __init__(self, user_id: int, typeform_id: str, webhook_url: Optional[str] = None):
        self.user_id = user_id
        self.typeform_id = typeform_id
        self.webhook_url = webhook_url 