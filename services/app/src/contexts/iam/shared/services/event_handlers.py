import json

from aio_pika import Message
from src.config.app_config import app_settings
from src.contexts.iam.shared.domain.events import UserCreated
from src.contexts.iam.shared.rabbitmq_data import email_admin_new_user_data
from src.rabbitmq.aio_pika_manager import AIOPikaManager


async def publish_send_admin_new_user_notification(
    event: UserCreated,
    aio_pika_manager: AIOPikaManager,
) -> None:
    async with aio_pika_manager:
        await aio_pika_manager.declare_resources_from_AIOPikaData(
            email_admin_new_user_data
        )
        message = Message(
            body=json.dumps(
                {
                    "admin_email": app_settings.first_admin_email,
                    "user_id": event.user_id,
                }
            ).encode(),
            content_type="application/json",
            # headers={
            #     # "x-message-ttl": <int>,
            #     # "x-max-length": <int>,
            #     "x-dead-letter-exchange": dl_exchange.name,
            # },
        )
        await aio_pika_manager.publish_from_AIOPikaData(
            message=message,
            routing_key=email_admin_new_user_data.queue_bind.routing_key,
            aio_pika_data=email_admin_new_user_data,
        )
