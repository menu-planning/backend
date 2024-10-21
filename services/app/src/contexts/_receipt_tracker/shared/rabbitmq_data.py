from src.rabbitmq.aio_pika_classes import (
    AIOPikaData,
    AIOPikaExchangeData,
    AIOPikaQueueBindData,
    AIOPikaQueueData,
    SetQOSData,
)

scrape_receipt_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="receipt_scraper",
        durable=True,
    ),
    queue=AIOPikaQueueData(
        name="receipt_scraper_scrape",
        durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "receipt_scraper_dlx",
            "x-dead-letter-routing-key": "receipt_scraper.scrape",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="receipt_scraper",
        routing_key="receipt_scraper.scrape",
    ),
    dl_queue=AIOPikaQueueData(
        name="receipt_scraper_scrape_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="receipt_scraper_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="receipt_scraper_dlx",
        routing_key="receipt_scraper.scrape",
    ),
)

scrape_receipt_result_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="receipt_scraper",
        durable=True,
    ),
    queue=AIOPikaQueueData(
        name="receipt_scraper_result",
        durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "receipt_scraper_dlx",
            "x-dead-letter-routing-key": "receipt_scraper.result",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="receipt_scraper",
        routing_key="receipt_scraper.result",
    ),
    dl_queue=AIOPikaQueueData(
        name="receipt_scraper_result_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="receipt_scraper_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="receipt_scraper_dlx",
        routing_key="receipt_scraper.result",
    ),
)

item_added_to_receipt_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="receipt_tracker",
        # type=ExchangeType.X_DELAYED_MESSAGE,
        # arguments={"x-delayed-type": "direct"},
    ),
    queue=AIOPikaQueueData(
        name="receipt_tracker_item_added",
        durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "receipt_tracker_dlx",
            "x-dead-letter-routing-key": "receipt_tracker.item_added",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="receipt_tracker",
        routing_key="receipt_tracker.item_added",
    ),
    dl_queue=AIOPikaQueueData(
        name="receipt_tracker_item_added_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="receipt_tracker_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="receipt_tracker_dlx",
        routing_key="receipt_tracker.item_added",
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
