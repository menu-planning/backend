from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateWebhookUrlCommand(Command):
    """Command to update the webhook URL for an existing onboarding form.

    Args:
        form_id: Form identifier to update.
        new_webhook_url: New webhook URL for receiving form submissions.

    Notes:
        Updates the TypeForm webhook configuration and the corresponding
        database record.
    """

    form_id: str
    new_webhook_url: str
