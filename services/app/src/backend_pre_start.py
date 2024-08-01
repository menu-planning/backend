# import logging

# import anyio
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession
# from src.db.database import async_db
# from src.logging.logger import logger
# from src.rabbitmq.connection import aio_pika_connection
# from tenacity import (
#     AsyncRetrying,
#     RetryError,
#     after_log,
#     before_log,
#     stop_after_attempt,
#     wait_fixed,
# )

# max_tries = 60
# wait_seconds = 5


# async def init() -> None:
#     db_initialized = False
#     rmq_initialized = False
#     try:
#         async for attempt in AsyncRetrying(
#             stop=stop_after_attempt(max_tries),
#             wait=wait_fixed(wait_seconds),
#             before=before_log(logger, logging.INFO),
#             after=after_log(logger, logging.WARN),
#         ):
#             with attempt:
#                 with anyio.fail_after(wait_seconds - 1):
#                     try:
#                         if not db_initialized:
#                             session: AsyncSession = async_db.async_session_factory()
#                             async with session:
#                                 await session.execute(text("SELECT 1"))
#                                 db_initialized = True
#                         if not rmq_initialized:
#                             connection = await aio_pika_connection.get_connection()
#                             channel = await connection.channel()
#                             if channel.is_initialized:
#                                 await channel.close()
#                                 rmq_initialized = True
#                     except Exception as e:
#                         logger.error(e)
#                         raise e
#     except RetryError as e:
#         logger.error(e)
#         raise e


# async def main() -> None:
#     logger.info("Initializing services")
#     await init()
#     logger.info("Services finished initializing")


# if __name__ == "__main__":
#     anyio.run(main)
