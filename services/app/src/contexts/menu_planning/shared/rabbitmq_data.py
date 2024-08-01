# from src.rabbitmq.aio_pika_classes import (
#     AIOPikaData,
#     AIOPikaExchangeData,
#     AIOPikaQueueBindData,
#     AIOPikaQueueData,
#     SetQOSData,
# )

# prettify_recipe_file_data = AIOPikaData(
#     set_qos=SetQOSData(prefetch_count=1),
#     exchange=AIOPikaExchangeData(
#         name="recipe_file_prettfier",
#         durable=True,
#     ),
#     queue=AIOPikaQueueData(
#         name="recipe_file_prettifier",
#         durable=True,
#         arguments={
#             # "x-message-ttl": <int>,
#             # "x-max-length": <int>,
#             "x-dead-letter-exchange": "recipe_file_prettifier_dlx",
#             "x-dead-letter-routing-key": "recipe_file_prettifier.prettify",
#         },
#     ),
#     queue_bind=AIOPikaQueueBindData(
#         exchange="recipe_file_prettifier",
#         routing_key="recipe_file_prettifier.prettify",
#     ),
#     dl_queue=AIOPikaQueueData(
#         name="recipe_file_prettifier_prettify_dlx",
#     ),
#     dl_exchange=AIOPikaExchangeData(
#         name="recipe_file_prettifier_dlx",
#     ),
#     dl_queue_bind=AIOPikaQueueBindData(
#         exchange="recipe_file_prettifier_dlx",
#         routing_key="recipe_file_prettifier.prettify",
#     ),
# )

# prettify_recipe_file_result_data = AIOPikaData(
#     set_qos=SetQOSData(prefetch_count=1),
#     exchange=AIOPikaExchangeData(
#         name="recipe_file_prettifier",
#         # durable=True,
#     ),
#     queue=AIOPikaQueueData(
#         name="recipe_file_prettifier_result",
#         # durable=True,
#         arguments={
#             # "x-message-ttl": <int>,
#             # "x-max-length": <int>,
#             "x-dead-letter-exchange": "recipe_file_prettifier_dlx",
#             "x-dead-letter-routing-key": "recipe_file_prettifier.result",
#         },
#     ),
#     queue_bind=AIOPikaQueueBindData(
#         exchange="recipe_file_prettifier",
#         routing_key="recipe_file_prettifier.result",
#     ),
#     dl_queue=AIOPikaQueueData(
#         name="recipe_file_prettifier_result_dlx",
#     ),
#     dl_exchange=AIOPikaExchangeData(
#         name="recipe_file_prettifier_dlx",
#     ),
#     dl_queue_bind=AIOPikaQueueBindData(
#         exchange="recipe_file_prettifier_dlx",
#         routing_key="recipe_file_prettifier.result",
#     ),
# )
