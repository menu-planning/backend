from src.rabbitmq.aio_pika_classes import (
    AIOPikaData,
    AIOPikaExchangeData,
    AIOPikaQueueBindData,
    AIOPikaQueueData,
    SetQOSData,
)

email_admin_new_event_data = AIOPikaData(
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

email_admin_product_not_found_data = AIOPikaData(
    exchange=AIOPikaExchangeData(
        name="notifications",
    ),
    queue=AIOPikaQueueData(
        name="notifications_email_admin_product_not_found",
        arguments={
            "x-dead-letter-exchange": "notifications_dlx",
            "x-dead-letter-routing-key": "notifications.email.admin.product_not_found",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="notifications",
        routing_key="notifications.email.admin.product_not_found",
    ),
    dl_queue=AIOPikaQueueData(
        name="notifications_email_admin_product_not_found_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="notifications_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="notifications_dlx",
        routing_key="notifications.email.admin.product_not_found",
    ),
)

products_added_to_items_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="receipt_tracker",
        # type=ExchangeType.X_DELAYED_MESSAGE,
        # arguments={"x-delayed-type": "direct"},
    ),
    queue=AIOPikaQueueData(
        name="receipt_tracker_products_added_to_items",
        durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "receipt_tracker_dlx",
            "x-dead-letter-routing-key": "receipt_tracker.products_added_to_items",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="receipt_tracker",
        routing_key="receipt_tracker.products_added_to_items",
    ),
    dl_queue=AIOPikaQueueData(
        name="receipt_tracker_products_added_to_items_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="receipt_tracker_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="receipt_tracker_dlx",
        routing_key="receipt_tracker.products_added_to_items",
    ),
)
