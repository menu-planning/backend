from src.contexts.seedwork.shared.domain.commands.command import Command
from attrs import frozen

@frozen(kw_only=True)
class DeleteOnboardingFormCommand(Command):
    """
    Command to delete (soft-delete) an onboarding form and remove its webhook configuration.
    """
    user_id: int
    form_id: int
