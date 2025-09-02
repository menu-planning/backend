from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteOnboardingFormCommand(Command):
    """Command to delete an onboarding form and remove its webhook configuration.

    Args:
        user_id: User identifier who owns the form.
        form_id: Form identifier to delete.
    """

    user_id: str
    form_id: int
