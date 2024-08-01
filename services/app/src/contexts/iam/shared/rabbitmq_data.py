from src.rabbitmq.aio_pika_classes import (
    AIOPikaData,
    AIOPikaExchangeData,
    AIOPikaQueueBindData,
    AIOPikaQueueData,
)

email_admin_new_user_data = AIOPikaData(
    exchange=AIOPikaExchangeData(
        name="notifications",
    ),
    queue=AIOPikaQueueData(
        name="notifications_email_admin_new_user",
        arguments={
            "x-dead-letter-exchange": "notifications_dlx",
            "x-dead-letter-routing-key": "notifications.email.admin.new_user",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="notifications",
        routing_key="notifications.email.admin.new_user",
    ),
    dl_queue=AIOPikaQueueData(
        name="notifications_email_admin_new_user_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="notifications_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="notifications_dlx",
        routing_key="notifications.email.admin.new_user",
    ),
)
