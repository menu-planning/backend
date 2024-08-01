import io
import json
from functools import partial

import aioboto3
import anyio
import httpx
from aio_pika import DeliveryMode, Message
from aio_pika.abc import AbstractIncomingMessage
from anyio import (
    Event,
    Semaphore,
    from_thread,
    get_cancelled_exc_class,
    move_on_after,
    to_thread,
)
from attrs import asdict
from PIL import Image
from src.config import settings
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from src.rabbitmq.queues_data import (
    scrape_product_image_data,
    scrape_product_image_result_data,
)

#


def buffer_img(r: httpx.Response, event: Event) -> io.BytesIO:
    try:
        raw_img_file = io.BytesIO(r.content)
        im = Image.open(raw_img_file).convert("RGB")
        jpeg_file = io.BytesIO()
        im.save(jpeg_file, "JPEG")
        return jpeg_file
    finally:
        from_thread.run_sync(event.set)


async def upload_to_bucket(product_id: str, r: httpx.Response) -> str:
    session = aioboto3.Session()
    try:
        async with session.client("s3") as s3:
            file_name = f"images/{product_id}.jpeg"
            event = Event()
            jpeg_file = await to_thread.run_sync(buffer_img, r, event)
            await event.wait()
            jpeg_file.seek(0)
            s3.upload_fileobj(
                jpeg_file,
                settings.image_S3_bucket,
                file_name,
                ExtraArgs={"ContentType": "image/jpeg"},
            )
            return f"{settings.image_cdn_url_prefix}/{file_name}"
    except get_cancelled_exc_class():
        with move_on_after(settings.cleanup_timeout) as cleanup_scope:
            cleanup_scope.shield = True
            try:
                await s3.close()
            except Exception:
                pass
        raise


async def scrape_callback(
    message: AbstractIncomingMessage,
    semaphore: Semaphore,
) -> None:
    """
    Scrape and save image to aws bucket.
    """
    async with semaphore:
        with move_on_after(settings.work_timeout) as scope:
            await message.ack()
            body: dict = json.loads(message.body)
            product_id = body.get("product_id")
            barcode = body.get("barcode")
            image_url = body.get("image_url")
            bucket_img_path = ""
            async with httpx.AsyncClient() as session:
                if image_url:
                    targets = [image_url]
                else:
                    targets = settings.image_source_url(barcode)
                for url in targets:
                    try:
                        r = await session.get(url, follow_redirects=True)
                        if r.status_code == 200:
                            bucket_img_path = await upload_to_bucket(product_id, r)
                            break
                    except Exception:
                        return
            if bucket_img_path:
                response = Message(
                    body=json.dumps(
                        {
                            "product_id": product_id,
                            "image_url": bucket_img_path,
                        }
                    ).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                )
                await publish_success_scraped_product_image_data(response)
        if scope.cancel_called:
            with move_on_after(settings.cleanup_timeout) as cleanup_scope:
                cleanup_scope.shield = True
                try:
                    await session.aclose()
                except Exception:
                    pass


async def publish_success_scraped_product_image_data(message: Message):
    aio_pika_manager = AIOPikaManager()
    await aio_pika_manager.connect()
    channel = aio_pika_manager.channel
    await setup_rabbitmq_resources(
        # channel=channel,
        rmq_manager=aio_pika_manager,
        data=scrape_product_image_result_data,
    )
    # message.headers["x-dead-letter-exchange"] = rabbitmq_resources.dl_exchange.name
    await aio_pika_manager.publish(
        message=message,
        routing_key=scrape_product_image_result_data.queue_bind.routing_key,
    )


async def main() -> None:
    semaphore = Semaphore(settings.max_concurrency)
    scrape_consumer = AIOPikaManager()
    await scrape_consumer.connect()
    # scrape
    channel = scrape_consumer.channel
    if scrape_product_image_data.set_qos:
        await channel.set_qos(**asdict(scrape_product_image_data.set_qos))
    await setup_rabbitmq_resources(
        # channel=channel,
        rmq_manager=scrape_consumer,
        data=scrape_product_image_data,
    )
    await scrape_consumer.consume(
        scrape_consumer.queue, partial(scrape_callback, semaphore=semaphore)
    )

    await anyio.sleep_forever()


if __name__ == "__main__":
    anyio.run(main)
