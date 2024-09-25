import json
from unittest import mock

import pytest
from aio_pika import Message, RobustChannel
from attrs import asdict
from src.contexts.products_catalog.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
    get_uow,
)
from src.contexts.products_catalog.shared.domain.commands import (
    AddFoodProduct,
    AddFoodProductBulk,
    AddHouseInputAndCreateProductIfNeeded,
    UpdateProduct,
)
from src.contexts.products_catalog.shared.rabbitmq_data import (
    email_admin_new_product_data,
    scrape_product_image_data,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.products_catalog.random_refs import (
    random_add_food_product_cmd_kwargs,
    random_attr,
    random_barcode,
)
from tests.products_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_aio_pika_manager_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


class TestAddProduct:
    async def test_for_new_product(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_add_food_product_cmd_kwargs()
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert uow.committed

    async def test_same_barcode_different_source(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_add_food_product_cmd_kwargs(barcode=random_barcode())
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert uow.committed
        new_cmd_kwargs = asdict(cmd)
        new_cmd_kwargs["add_product_cmds"][0]["source_id"] = "new_source"
        cmd2 = AddFoodProductBulk(
            add_product_cmds=[AddFoodProduct(**new_cmd_kwargs["add_product_cmds"][0])]
        )
        await bus_test.handle(cmd2)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            products = await uow.products.query(
                filter={"barcode": cmd.add_product_cmds[0].barcode}
            )
            assert len(products) == 2

    async def test_same_barcode_and_source(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_add_food_product_cmd_kwargs(barcode=random_barcode())
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert product is not None
            assert uow.committed
        new_cmd_kwargs = asdict(cmd)
        cmd2 = AddFoodProductBulk(
            add_product_cmds=[AddFoodProduct(**new_cmd_kwargs["add_product_cmds"][0])]
        )
        with pytest.raises(ExceptionGroup) as exc:
            await bus_test.handle(cmd2)
        assert any(isinstance(e, BadRequestException) for e in exc.value.exceptions)


class TestUpdateProduct:
    async def test_add_and_remove_diet_type(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_add_food_product_cmd_kwargs(diet_types_ids=None)
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            products = await uow.products.query()
            assert len(products) == 1
            product = products[0]
            assert product is not None
            assert product.diet_types_ids == set()
            assert uow.committed
        # TODO: fix this
        # cmd2 = AddDietType(product_id=product.id, diet_type="vegan")
        # await bus_test.handle(cmd2)
        # async with bus_test.uow as uow:
        #     product = await uow.products.get(product.id)
        #     assert product.diet_types_ids == set(["vegan"])
        #     assert uow.committed
        # cmd3 = RemoveDietType(product_id=product.id, diet_type="not_existent")
        # await bus_test.handle(cmd3)
        # async with bus_test.uow as uow:
        #     product = await uow.products.get(product.id)
        #     assert product.diet_types_ids == set(["vegan"])
        #     assert uow.committed
        # cmd4 = RemoveDietType(product_id=product.id, diet_type="vegan")
        # await bus_test.handle(cmd4)
        # async with bus_test.uow as uow:
        #     product = await uow.products.get(product.id)
        #     assert product.diet_types_ids == set()
        #     assert uow.committed

    async def test_compute_user_is_food_input(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        barcode = random_barcode()
        kwargs = random_add_food_product_cmd_kwargs(barcode=barcode)
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            product = await uow.products.query()
            product = product[0]
            assert product is not None
            assert uow.committed
        cmd2 = AddHouseInputAndCreateProductIfNeeded(
            barcode=product.barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test.handle(cmd2)
        async with bus_test.uow as uow:
            products = await uow.products.query(filter={"barcode": product.barcode})
            assert products[0].is_food_votes.is_food_houses == {cmd2.house_id}
            assert uow.committed
        cmd3 = AddHouseInputAndCreateProductIfNeeded(
            barcode=product.barcode, house_id=random_attr("user_id"), is_food=False
        )
        await bus_test.handle(cmd3)
        async with bus_test.uow as uow:
            products = await uow.products.query(filter={"barcode": product.barcode})
            assert products[0].is_food_votes.is_food_houses == {cmd2.house_id}
            assert products[0].is_food_votes.is_not_food_houses == {cmd3.house_id}
            assert uow.committed

    async def test_add_auto_food_product_notify_admin_and_scrape_image(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        barcode = random_barcode()
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            products = await uow.products.query(
                filter={"barcode": barcode}, hide_undefined_auto_products=False
            )
            product = products[0]
            assert product.is_food == True
            assert product.source_id == "auto"
            assert product.is_food_votes.is_food_houses == {cmd.house_id}
            assert uow.committed
        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 2

        for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
            for arg in list(call.kwargs.values()):
                if isinstance(arg, Message) and hasattr(arg, "body"):
                    msg = json.loads(arg.body.decode())
                    assert msg["barcode"] == barcode

        queue_names = []
        for (
            call
        ) in aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_args_list:
            for arg in list(call.args):
                if isinstance(arg, AIOPikaData):
                    queue_names.append(arg.queue.name)
        assert aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_count == 2
        assert email_admin_new_product_data.queue.name in queue_names
        assert scrape_product_image_data.queue.name in queue_names

    async def test_add_auto_product_not_unique_barcode_does_nothing(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        barcode = "0" * 4
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            products = await uow.products.query(filter={"barcode": barcode})
            assert uow.committed
        assert len(products) == 0
        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 0

    async def test_add_auto_non_food_product_does_not_notify_admin_neither_scrape_image(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        barcode = random_barcode()
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=False
        )
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            products = await uow.products.query(
                filter={"barcode": barcode}, hide_undefined_auto_products=False
            )
            product = products[0]
            assert product.is_food == False
            assert product.source_id == "auto"
            assert product.is_food_votes.is_not_food_houses == {cmd.house_id}
            assert uow.committed
        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 0

    async def test_can_update_product_properties(self):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_aio_pika_manager_mock(aio_pika_manager_mock)
        kwargs = random_add_food_product_cmd_kwargs()
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test.handle(cmd)
        uow: UnitOfWork
        async with bus_test.uow as uow:
            product = await uow.products.query()
            product = product[0]
            assert product is not None
            assert uow.committed
        new_product_kwargs = {
            "name": random_attr("name"),
            "brand_id": random_attr("brand_id"),
            "source_id": random_attr("source_id"),
            "category_id": random_attr("category_id"),
            "parent_category_id": random_attr("parent_category_id"),
            "food_group_id": random_attr("food_group_id"),
            "process_type_id": random_attr("process_type_id"),
            "ingredients": random_attr("ingredients"),
            "package_size": random_attr("package_size"),
            "package_size_unit": random_attr("package_size_unit"),
            "image_url": random_attr("image_url"),
            "json_data": random_attr("json_data"),
        }
        cmd2 = UpdateProduct(product_id=product.id, updates=new_product_kwargs)
        await bus_test.handle(cmd2)
        async with bus_test.uow as uow:
            product = await uow.products.get(product.id)
            assert product is not None
            assert product.name == new_product_kwargs["name"]
            assert product.brand_id == new_product_kwargs["brand_id"]
            assert product.source_id == new_product_kwargs["source_id"]
            assert product.category_id == new_product_kwargs["category_id"]
            assert (
                product.parent_category_id == new_product_kwargs["parent_category_id"]
            )
            assert product.food_group_id == new_product_kwargs["food_group_id"]
            assert product.process_type_id == new_product_kwargs["process_type_id"]
            assert product.ingredients == new_product_kwargs["ingredients"]
            assert product.package_size == new_product_kwargs["package_size"]
            assert product.package_size_unit == new_product_kwargs["package_size_unit"]
            assert product.image_url == new_product_kwargs["image_url"]
            assert product.json_data == new_product_kwargs["json_data"]

        cmd3 = UpdateProduct(
            product_id=product.id, updates={"barcode": random_barcode()}
        )
        with pytest.raises(ExceptionGroup) as exc:
            await bus_test.handle(cmd3)
        assert any(isinstance(e, AttributeError) for e in exc.value.exceptions)

        cmd4 = UpdateProduct(product_id=product.id, updates={"_id": random_barcode()})
        with pytest.raises(ExceptionGroup) as exc:
            await bus_test.handle(cmd4)
        assert any(isinstance(e, AttributeError) for e in exc.value.exceptions)

        cmd5 = UpdateProduct(
            product_id=product.id, updates={"diet_types_ids": ["vegan"]}
        )
        with pytest.raises(ExceptionGroup) as exc:
            await bus_test.handle(cmd5)
        assert any(isinstance(e, AttributeError) for e in exc.value.exceptions)
