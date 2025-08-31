from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateWebhookUrlCommand(Command):
    """
    Command to update the webhook URL for an existing onboarding form.

    This command updates the TypeForm webhook configuration and
    the corresponding database record.
    """

    form_id: str
    new_webhook_url: str
