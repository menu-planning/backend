"""Event handlers for IAM domain events.

Integration services that handle domain events by publishing notifications
or triggering external system integrations.
"""

from src.contexts.iam.core.domain.events import UserCreated


async def publish_send_admin_new_user_notification(
    event: UserCreated,
) -> None:
    """Handle UserCreated event by notifying administrators.
    
    Args:
        event: UserCreated domain event containing user_id of new user.
    
    Returns:
        None: Notification is a side-effect operation.
    
    Raises:
        NotImplementedError: Currently not implemented.
    
    Side Effects:
        Publishes admin notification via messaging system (when implemented).
    
    Notes:
        Implementation depends on the messaging/notification provider.
        This is a placeholder for future integration with notification services.
    """
    raise NotImplementedError("Not implemented yet")
