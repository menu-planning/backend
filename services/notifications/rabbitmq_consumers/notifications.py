import json
from functools import partial

import anyio
from aio_pika.abc import AbstractIncomingMessage
from pydantic import AnyHttpUrl, BaseModel, EmailStr
from src.config import settings
from src.email.async_email import AsyncEmailNotifications
from src.logger import logger
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from src.rabbitmq.queues_data import (
    email_account_verification_data,
    email_admin_new_event_data,
)


class ApiAccountVerification(BaseModel):
    email: EmailStr
    endpoint: AnyHttpUrl
    expiration: int
    project_name: str


class ApiEvent(BaseModel):
    event: str


async def send_new_account_verification_email(
    message: AbstractIncomingMessage,
    semaphore: anyio.Semaphore,
) -> None:
    """
    Send email to user verify account.

    Args:
        message: A :class:`AbstractIncomingMessage <aio_pika.abc.AbstractIncomingMessage>`
            instance.
        semaphore: A :class:`Semaphore <anyio.Semaphore>` instance.

    Returns:
        None
    """
    async with semaphore:
        with anyio.move_on_after(settings.work_timeout) as scope:
            try:
                fields = json.loads(message.body)
                msg = ApiAccountVerification(**fields)
                await message.ack()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error: {e}")
                # Do not requeue malformed messages
                await message.reject()
            except Exception as e:
                logger.error(e)
                await message.nack(requeue=True)
            else:
                await AsyncEmailNotifications().send_new_account_confirmation_email(
                    receiver_email=msg.email,
                    endpoint=msg.endpoint,
                    token_expiration=msg.expiration,
                    project_name=msg.project_name,
                )
        if scope.cancel_called:
            logger.error(f"Request processing time excedeed limit. Message={fields}")


async def send_new_event_email(
    message: AbstractIncomingMessage,
    semaphore: anyio.Semaphore,
) -> None:
    """
    Send email to notify of new event.

    Args:
        message: A :class:`AbstractIncomingMessage <aio_pika.abc.AbstractIncomingMessage>`
            instance.
        semaphore: A :class:`Semaphore <anyio.Semaphore>` instance.

    Returns:
        None
    """
    async with semaphore:
        with anyio.move_on_after(settings.work_timeout) as scope:
            try:
                fields = json.loads(message.body)
                msg = ApiEvent(**fields)
                await message.ack()
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error: {e}")
                # Do not requeue malformed messages
                await message.reject()
            except Exception as e:
                logger.error(e)
                await message.nack(requeue=True)
            else:
                await AsyncEmailNotifications().send_admin_new_event(
                    new_event=msg.event,
                )
        if scope.cancel_called:
            logger.error(f"Request processing time excedeed limit. Message={fields}")


async def main() -> None:
    """
    Consume messages from rabbitmq and send notifications.
    """
    semaphore = anyio.Semaphore(settings.max_concurrency)
    consumer_manager = AIOPikaManager()

    # setup account verification email consumser
    await consumer_manager.declare_resources_from_AIOPikaData(
        email_account_verification_data
    )
    account_verification_queue = await consumer_manager.get_queue_from_AIOPikaData(
        email_account_verification_data
    )

    # setup new event consumser
    await consumer_manager.declare_resources_from_AIOPikaData(
        email_admin_new_event_data
    )
    admin_new_event_queue = await consumer_manager.get_queue_from_AIOPikaData(
        email_admin_new_event_data
    )

    async with anyio.create_task_group() as tg:
        tg.start_soon(
            consumer_manager.signal_handler,
            tg.cancel_scope,
        )
        tg.start_soon(
            consumer_manager.consume,
            admin_new_event_queue,
            partial(send_new_event_email, semaphore=semaphore),
        )
        tg.start_soon(
            consumer_manager.consume,
            account_verification_queue,
            partial(send_new_account_verification_email, semaphore=semaphore),
        )
        # prevent the script from finishing
        await anyio.sleep_forever()


if __name__ == "__main__":
    logger.info("Starting notifications consumer")
    anyio.run(main)
    logger.info("Stopping notifications consumer")
