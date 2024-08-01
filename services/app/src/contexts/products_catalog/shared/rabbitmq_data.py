from src.rabbitmq.aio_pika_classes import (
    AIOPikaData,
    AIOPikaExchangeData,
    AIOPikaQueueBindData,
    AIOPikaQueueData,
    SetQOSData,
)

scrape_product_image_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="product_image_scraper",
        durable=True,
    ),
    queue=AIOPikaQueueData(
        name="product_image_scraper_scrape",
        durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "product_image_scraper_dlx",
            "x-dead-letter-routing-key": "product_image_scraper.scrape",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="product_image_scraper",
        routing_key="product_image_scraper.scrape",
    ),
    dl_queue=AIOPikaQueueData(
        name="product_image_scraper_scrape_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="product_image_scraper_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="product_image_scraper_dlx",
        routing_key="product_image_scraper.scrape",
    ),
)

scrape_product_image_result_data = AIOPikaData(
    set_qos=SetQOSData(prefetch_count=1),
    exchange=AIOPikaExchangeData(
        name="product_image_scraper",
        # durable=True,
    ),
    queue=AIOPikaQueueData(
        name="product_image_scraper_result",
        # durable=True,
        arguments={
            # "x-message-ttl": <int>,
            # "x-max-length": <int>,
            "x-dead-letter-exchange": "product_image_scraper_dlx",
            "x-dead-letter-routing-key": "product_image_scraper.result",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="product_image_scraper",
        routing_key="product_image_scraper.result",
    ),
    dl_queue=AIOPikaQueueData(
        name="product_image_scraper_result_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="product_image_scraper_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="product_image_scraper_dlx",
        routing_key="product_image_scraper.result",
    ),
)

email_admin_new_product_data = AIOPikaData(
    exchange=AIOPikaExchangeData(
        name="notifications",
    ),
    queue=AIOPikaQueueData(
        name="notifications_email_admin_new_product",
        arguments={
            "x-dead-letter-exchange": "notifications_dlx",
            "x-dead-letter-routing-key": "notifications.email.admin.new_product",
        },
    ),
    queue_bind=AIOPikaQueueBindData(
        exchange="notifications",
        routing_key="notifications.email.admin.new_product",
    ),
    dl_queue=AIOPikaQueueData(
        name="notifications_email_admin_new_product_dlx",
    ),
    dl_exchange=AIOPikaExchangeData(
        name="notifications_dlx",
    ),
    dl_queue_bind=AIOPikaQueueBindData(
        exchange="notifications_dlx",
        routing_key="notifications.email.admin.new_product",
    ),
)

# email_admin_food_product_not_found_data = AIOPikaData(
#     exchange=AIOPikaExchangeData(
#         name="notifications",
#     ),
#     queue=AIOPikaQueueData(
#         name="notifications_email_admin_food_product_not_found",
#         arguments={
#             "x-dead-letter-exchange": "notifications_dlx",
#             "x-dead-letter-routing-key": "notifications.email.admin.food_product_not_found",
#         },
#     ),
#     queue_bind=AIOPikaQueueBindData(
#         exchange="notifications",
#         routing_key="notifications.email.admin.food_product_not_found",
#     ),
#     dl_queue=AIOPikaQueueData(
#         name="notifications_email_admin_food_product_not_found_dlx",
#     ),
#     dl_exchange=AIOPikaExchangeData(
#         name="notifications_dlx",
#     ),
#     dl_queue_bind=AIOPikaQueueBindData(
#         exchange="notifications_dlx",
#         routing_key="notifications.email.admin.food_product_not_found",
#     ),
# )
