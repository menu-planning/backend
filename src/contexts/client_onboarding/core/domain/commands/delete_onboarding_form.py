from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteOnboardingFormCommand(Command):
    """
    Command to delete (soft-delete) an onboarding form and
    remove its webhook configuration.
    """

    user_id: str
    form_id: int
