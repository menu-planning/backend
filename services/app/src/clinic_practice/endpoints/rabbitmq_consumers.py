# import json
# import logging

# from pika.channel import Channel
# from pika.spec import Basic, BasicProperties

# from src.rabbitmq.utils import (
#     declare_new_user_exchange_and_queue,
#     open_channel,
# )

# from ..container import Container
# from ..domain.commands import SendNewAccountVerificationEmail

# from src.logging.logger import logger


# def main():
#     logger.info("Rabbitmq pubsub starting")
#     register_create_user()


# def register_create_user():
#     """
#     Create a new user.
#     """
#     channel = open_channel()
#     _, queue, _ = declare_new_user_exchange_and_queue(channel)
#     channel.basic_consume(
#         publish_user_created,
#         queue=queue,
#         no_ack=False,
#         consumer_tag="new_user",
#     )
#     channel.start_consuming()


# def publish_user_created(
#     channel: Channel,
#     method: Basic.Deliver,
#     header: BasicProperties,
#     body: bytes,
# ):
#     """
#     Send e-mail to verify account ownership.
#     """
#     try:
#         email = json.loads(body)["email"]
#         cmd = SendNewAccountVerificationEmail(email=email)
#         bus = Container().bootstrap()
#         bus.handle(cmd)
#         channel.basic_ack(delivery_tag=method.delivery_tag)
#     except Exception:
#         logger.exception(
#             f"Error sending new account verification email: {body}"
#         )


# if __name__ == "__main__":
#     main()
