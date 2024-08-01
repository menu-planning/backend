from src.rabbitmq.aio_pika_classes import (
    AIOPikaData,
    AIOPikaExchangeData,
    AIOPikaQueueBindData,
    AIOPikaQueueData,
    SetQOSData,
)

email_account_verification_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="notifications",
    ),
    queue=AIOPikaQueueData(
        name="notifications_email_user_account_verification",
        arguments={
            "x-dead-letter-exchange": "notifications_dlx",
            "x-dead-letter-routing-key": "notifications.email.user.account_verification",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="notifications",
        routing_key="notifications.email.user.account_verification",
    ),
    dl_queue=AIOPikaQueueData(
        name="notifications_email_user_account_verification_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="notifications_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="notifications_dlx",
        routing_key="notifications.email.user.account_verification",
    ),
)

email_admin_new_event_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="notifications",
    ),
    queue=AIOPikaQueueData(
        name="notifications_email_admin_new_event",
        arguments={
            "x-dead-letter-exchange": "notifications_dlx",
            "x-dead-letter-routing-key": "notifications.email.admin.new_event",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="notifications",
        routing_key="notifications.email.admin.new_event",
    ),
    dl_queue=AIOPikaQueueData(
        name="notifications_email_admin_new_event_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="notifications_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="notifications_dlx",
        routing_key="notifications.email.admin.new_event",
    ),
)
