from src.contexts.seedwork.shared.domain.commands.command import Command


class UpdateWebhookUrlCommand(Command):
    """
    Command to update the webhook URL for an existing onboarding form.
    
    This command updates the TypeForm webhook configuration and
    the corresponding database record.
    """
    
    def __init__(self, form_id: str, new_webhook_url: str):
        self.form_id = form_id
        self.new_webhook_url = new_webhook_url 