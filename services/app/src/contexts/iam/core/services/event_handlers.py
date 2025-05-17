import json

from aio_pika import Message
from src.config.app_config import app_settings
from src.contexts.iam.core.domain.events import UserCreated


async def publish_send_admin_new_user_notification(
    event: UserCreated,
) -> None:
    # TODO: implement this function
    raise NotImplementedError("Not implemented yet")