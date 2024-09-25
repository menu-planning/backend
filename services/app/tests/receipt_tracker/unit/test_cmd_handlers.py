import json
import uuid
from datetime import datetime
from unittest import mock

import pytest
from aio_pika import Message, RobustChannel
from src.contexts.receipt_tracker.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.receipt_tracker.shared.domain import commands
from src.contexts.receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts.receipt_tracker.shared.rabbitmq_data import (
    products_added_to_items_data,
    scrape_receipt_data,
)
from src.contexts.receipt_tracker.shared.services.event_handlers.receipt_added.publish_scrape_receipt import (
    ProductsCatalogProvider,
)
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.receipt_tracker.random_refs import (
    random_attr,
    random_cfe_key,
    random_item,
    random_seller,
)
from tests.receipt_tracker.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


class TestAddReceipt:
    async def test_for_new_receipt(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(aio_pika_manager_mock)
        cmd = commands.AddReceipt(
            house_id=f"test_new_receipt-{uuid.uuid4()}",
            cfe_key=random_cfe_key(35),
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            receipt = await uow.receipts.get(cmd.cfe_key)
            assert receipt is not None
            assert uow.committed
        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 1

        for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
            for arg in list(call.kwargs.values()):
                if isinstance(arg, Message) and hasattr(arg, "body"):
                    msg = json.loads(arg.body.decode())
                    assert msg["cfe_key"] == cmd.cfe_key

        queue_names = []
        for (
            call
        ) in aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_args_list:
            for arg in list(call.args):
                if isinstance(arg, AIOPikaData):
                    queue_names.append(arg.queue.name)
        assert aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_count == 1
        assert scrape_receipt_data.queue.name in queue_names

    async def test_for_existing_receipt(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(aio_pika_manager_mock)
        cmd = commands.AddReceipt(
            house_id=f"test_new_receipt-{uuid.uuid4()}",
            cfe_key=random_cfe_key(35),
        )
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            receipt = await uow.receipts.get(cmd.cfe_key)
            assert receipt is not None
            assert uow.committed
        cmd2 = commands.AddReceipt(cmd.house_id, cmd.cfe_key, qrcode="test_qrcode")
        await bus_test.handle(cmd2)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            receipt = await uow.receipts.get(cmd.cfe_key)
            assert receipt.qrcode == "test_qrcode"

    async def test_for_existing_receipt_on_another_house(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(aio_pika_manager_mock)
        cmd = commands.AddReceipt(
            house_id=f"test_new_receipt-{uuid.uuid4()}",
            cfe_key=random_cfe_key(35),
        )
        await bus_test.handle(cmd)
        cmd2 = commands.AddReceipt(
            house_id=f"test_new_receipt-{uuid.uuid4()}",
            cfe_key=cmd.cfe_key,
            qrcode="test_qrcode",
        )
        await bus_test.handle(cmd2)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            receipt = await uow.receipts.get(cmd.cfe_key)
            assert len(receipt.house_ids) == 2


class TestUpdateWithScrapedData:
    async def test_create_seller_and_update_receipt(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.return_value": [],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.receipt_tracker.shared.services.event_handlers.items_added_to_receipt.add_products_to_items.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            cmd = commands.AddReceipt(
                house_id=f"test_update_with_scraped_data-{uuid.uuid4()}",
                cfe_key=random_cfe_key(35),
            )
            await bus_test.handle(cmd)
            update_cmd = commands.CreateSellerAndUpdateWithScrapedData(
                cfe_key=cmd.cfe_key,
                date=datetime.now(),
                seller=random_seller(prefix="test_update_with_scraped_data"),
                items=[random_item() for _ in range(3)],
            )
            await bus_test.handle(update_cmd)
            assert bus_test.uow.committed
            uow: UnitOfWork
            async with bus_test.uow as uow:
                receipt = await uow.receipts.get(cmd.cfe_key)
                assert receipt is not None
                assert receipt.seller_id == update_cmd.seller.cnpj
                assert receipt.date == update_cmd.date
                assert len(receipt.items) == len(update_cmd.items)
                assert receipt.scraped
                seller = await uow.sellers.get(update_cmd.seller.cnpj)
                assert seller is not None
                assert receipt.products_added
            assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 2

            for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
                for arg in list(call.kwargs.values()):
                    if isinstance(arg, Message) and hasattr(arg, "body"):
                        msg = json.loads(arg.body.decode())
                        assert msg["cfe_key"] == cmd.cfe_key

            queue_names = []
            for (
                call
            ) in (
                aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_args_list
            ):
                for arg in list(call.args):
                    if isinstance(arg, AIOPikaData):
                        queue_names.append(arg.queue.name)
            assert (
                aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_count
                == 2
            )
            assert scrape_receipt_data.queue.name in queue_names
            assert products_added_to_items_data.queue.name in queue_names

    async def test_nonexistent_receipt(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(aio_pika_manager_mock)
        cmd = commands.CreateSellerAndUpdateWithScrapedData(
            cfe_key=random_cfe_key(35),
            date=datetime.now(),
            seller=random_seller(prefix="test_update_with_scraped_data"),
            items=[random_item() for _ in range(3)],
        )
        with pytest.raises(ExceptionGroup) as exc:
            await bus_test.handle(cmd)
        assert any(isinstance(e, EntityNotFoundException) for e in exc.value.exceptions)


class TestUpdateProducts:
    async def test_update_products(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(aio_pika_manager_mock)
        cmd = commands.AddReceipt(
            house_id=f"test_update_with_scraped_data-{uuid.uuid4()}",
            cfe_key=random_cfe_key(35),
        )
        await bus_test.handle(cmd)
        update_cmd = commands.CreateSellerAndUpdateWithScrapedData(
            cfe_key=cmd.cfe_key,
            date=datetime.now(),
            seller=random_seller(prefix="test_update_with_scraped_data"),
            items=[random_item() for _ in range(3)],
        )
        await bus_test.handle(update_cmd)
        p1 = Product(
            id=random_attr("id"),
            source="private",
            name=random_attr("name"),
            is_food=True,
        )
        p2 = Product(
            id=random_attr("id"),
            source="auto",
            name=random_attr("name"),
            is_food=False,
        )
        update_product_cmd = commands.UpdateProducts(
            cfe_key=cmd.cfe_key,
            barcode_product_mapping={
                update_cmd.items[0].barcode: p1,
                update_cmd.items[1].barcode: p2,
            },
        )
        await bus_test.handle(update_product_cmd)
        assert bus_test.uow.committed
        uow: UnitOfWork
        async with bus_test.uow as uow:
            receipt = await uow.receipts.get(cmd.cfe_key)
        products = [i.product for i in receipt.items]
        assert p1 in products
        assert p2 in products
