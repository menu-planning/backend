import json
from datetime import datetime, timedelta
from functools import partial

from aio_pika import DeliveryMode, Message
from aio_pika.abc import AbstractIncomingMessage
from anyio import Semaphore, create_task_group, move_on_after, run, sleep_forever
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.common.exceptions import (
    NoSuchReceiptException,
    ReceiptNotAvailableYetException,
    ScrapingException,
)
from src.common.scraper_factory import ScraperFactory
from src.config import settings
from src.logger import logger
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from src.rabbitmq.queues_data import scrape_receipt_data, scrape_receipt_result_data

max_attempts = 4

scheduler = AsyncIOScheduler()
scheduler.start()


async def scrape_callback(
    message: AbstractIncomingMessage,
    semaphore: Semaphore,
) -> None:
    """
    Scrape receipt.
    """
    async with semaphore:
        body: dict = json.loads(message.body)
        cfe_key = body.get("cfe_key")
        qrcode = body.get("qrcode")
        attempts = body.get("attempts", 1)
        if attempts > max_attempts:
            logger.error(
                f"Max attempts reached trying to scrape receipt. Cfe key={cfe_key}. QRCode={qrcode}"
            )
            await message.reject()
            return
        with move_on_after(settings.work_timeout) as scope:
            try:
                fac = ScraperFactory()
                scraper_type = fac.get_scraper(
                    cfe_key=cfe_key,
                )
                scraper = scraper_type(cfe_key=cfe_key, qrcode=qrcode)
                # event = Event()
                await message.ack()
                async with scraper:
                    await scraper.scrape()
                # await event.wait()
            except json.JSONDecodeError as e:
                logger.error(f"JSONDecodeError: {e}")
                try:
                    await message.reject()
                except Exception:
                    pass
                return
            except NoSuchReceiptException as e:
                logger.error(f"NoSuchReceiptException: {e}")
                try:
                    await message.reject()
                except Exception:
                    pass
                return
            except ScrapingException as e:
                logger.error(f"ScrapingException: {e}")
                try:
                    await message.ack()
                    logger.info("Message acked so it will not be requeued")
                except Exception:
                    pass
                if attempts < max_attempts:
                    await retry_scrape_with_delay(cfe_key, qrcode, attempts + 1)
                else:
                    logger.error(
                        f"Max attempts reached trying to scrape receipt. Cfe key={cfe_key}. QRCode={qrcode}"
                    )
                    await message.reject()
                    return
            except ReceiptNotAvailableYetException as e:
                logger.error(f"ReceiptNotAvailableYetException: {e}")
                try:
                    await message.ack()
                    logger.info("Message acked so it will not be requeued")
                except Exception:
                    pass
                if attempts < max_attempts:
                    await retry_scrape_with_delay(cfe_key, qrcode, attempts + 1)
                else:
                    logger.error(
                        f"Max attempts reached trying to scrape receipt. Cfe key={cfe_key}. QRCode={qrcode}"
                    )
                    await message.reject()
                    return
            except Exception as e:
                logger.error(f"Exception: {e}")
                try:
                    await message.reject()
                except Exception:
                    pass
                if attempts < max_attempts:
                    await retry_scrape_with_delay(cfe_key, qrcode, attempts + 1)
                else:
                    logger.error(
                        f"Max attempts reached trying to scrape receipt. Cfe key={cfe_key}. QRCode={qrcode}"
                    )
                    await message.reject()
                    return
            else:
                response = Message(
                    delivery_mode=DeliveryMode.PERSISTENT,
                    body=json.dumps(
                        {
                            "cfe_key": cfe_key,
                            "date": scraper.date,
                            "seller": scraper.seller,
                            "items": scraper.items,
                        }
                    ).encode(),
                    content_type="application/json",
                )
                await publish_success_scraped_data(response)
        if scope.cancel_called:
            logger.error("Request processing time excedeed limit")
            with move_on_after(settings.cleanup_timeout) as cleanup_scope:
                cleanup_scope.shield = True
                try:
                    await scraper.close()
                except Exception:
                    pass


async def retry_scrape_with_delay(
    semaphore: Semaphore,
    cfe_key: str,
    qrcode: str | None = None,
    attempts: int = 1,
    retry_rate: int = 6,
):
    message = Message(
        delivery_mode=DeliveryMode.PERSISTENT,
        body=json.dumps(
            {
                "cfe_key": cfe_key,
                "qrcode": qrcode,
            }
        ).encode(),
        content_type="application/json",
        headers={
            "attempts": attempts,
        },
    )
    run_date = datetime.now() + timedelta(hours=retry_rate)
    scheduler.add_job(
        scrape_callback, "date", run_date=run_date, args=[message, semaphore]
    )


async def publish_success_scraped_data(message: Message):
    aio_pika_manager = AIOPikaManager()
    await aio_pika_manager.declare_resources_from_AIOPikaData(
        scrape_receipt_result_data,
    )
    await aio_pika_manager.publish_from_AIOPikaData(
        message=message,
        routing_key=scrape_receipt_result_data.queue_bind.routing_key,
        aio_pika_data=scrape_receipt_result_data,
    )


async def main() -> None:
    semaphore = Semaphore(settings.max_concurrency)
    consumer_manager = AIOPikaManager()

    await consumer_manager.declare_resources_from_AIOPikaData(scrape_receipt_data)
    queue = await consumer_manager.get_queue_from_AIOPikaData(scrape_receipt_data)

    async with create_task_group() as tg:
        tg.start_soon(
            consumer_manager.signal_handler,
            tg.cancel_scope,
        )
        tg.start_soon(
            consumer_manager.consume,
            queue,
            partial(scrape_callback, semaphore=semaphore),
        )

        # prevent the script from finishing
        await sleep_forever()


if __name__ == "__main__":
    logger.info("Starting receipt_scrapers consumer")
    run(main)
    logger.info("Stopping receipt_scrapers consumer")
