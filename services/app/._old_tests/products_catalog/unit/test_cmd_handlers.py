import json
from unittest import mock

import pytest
from attrs import asdict

from src.contexts.products_catalog.core.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.products_catalog.core.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.products_catalog.core.domain.commands.products.add_house_input_and_create_product_if_needed import (
    AddHouseInputAndCreateProductIfNeeded,
)
from src.contexts.products_catalog.core.domain.commands.products.update import (
    UpdateProduct,
)
from src.contexts.products_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus
from tests.products_catalog.random_refs import (
    random_add_food_product_cmd_kwargs,
    random_attr,
    random_barcode,
)
from tests.products_catalog.unit.fakes import FakeUnitOfWork

pytestmark = pytest.mark.anyio


def bus_test() -> MessageBus:
    uow = FakeUnitOfWork()
    return MessageBus(uow, event_handlers={}, command_handlers={})


class TestAddProduct:
    async def test_for_new_product(
        self,
    ):
        bus_test_instance = bus_test()
        kwargs = random_add_food_product_cmd_kwargs()
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert uow.committed # type: ignore

    async def test_same_barcode_different_source(
        self,
    ):
        bus_test_instance = bus_test()
        kwargs = random_add_food_product_cmd_kwargs(barcode=random_barcode())
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert uow.committed # type: ignore
        new_cmd_kwargs = asdict(cmd)
        new_cmd_kwargs["add_product_cmds"][0]["source_id"] = "new_source"
        cmd2 = AddFoodProductBulk(
            add_product_cmds=[AddFoodProduct(**new_cmd_kwargs["add_product_cmds"][0])]
        )
        await bus_test_instance.handle(cmd2)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(
                filter={"barcode": cmd.add_product_cmds[0].barcode}
            )
            assert len(products) == 2

    async def test_same_barcode_and_source(
        self,
    ):
        bus_test_instance = bus_test()
        kwargs = random_add_food_product_cmd_kwargs(barcode=random_barcode())
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            product = await uow.products.query()
            assert product[0] is not None
            assert product is not None
            assert uow.committed # type: ignore
        new_cmd_kwargs = asdict(cmd)
        cmd2 = AddFoodProductBulk(
            add_product_cmds=[AddFoodProduct(**new_cmd_kwargs["add_product_cmds"][0])]
        )
        with pytest.raises(BadRequestException) as exc:
            await bus_test_instance.handle(cmd2)


class TestUpdateProduct:
    async def test_compute_user_is_food_input(self):
        bus_test_instance = bus_test()
        barcode = random_barcode()
        kwargs = random_add_food_product_cmd_kwargs(barcode=barcode)
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            product = await uow.products.query()
            product = product[0]
            assert product is not None
            assert uow.committed # type: ignore
        cmd2 = AddHouseInputAndCreateProductIfNeeded(
            barcode=product.barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test_instance.handle(cmd2)
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(filter={"barcode": product.barcode})
            assert products[0].is_food_votes.is_food_houses == {cmd2.house_id}
            assert uow.committed # type: ignore
        cmd3 = AddHouseInputAndCreateProductIfNeeded(
            barcode=product.barcode, house_id=random_attr("user_id"), is_food=False
        )
        await bus_test_instance.handle(cmd3)
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(filter={"barcode": product.barcode})
            assert products[0].is_food_votes.is_food_houses == {cmd2.house_id}
            assert products[0].is_food_votes.is_not_food_houses == {cmd3.house_id}
            assert uow.committed # type: ignore

    async def test_add_auto_food_product(self):
        bus_test_instance = bus_test()
        barcode = random_barcode()
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(
                filter={"barcode": barcode}, hide_undefined_auto_products=False
            )
            product = products[0]
            assert product.is_food == True
            assert product.source_id == "auto"
            assert product.is_food_votes.is_food_houses == {cmd.house_id}
            assert uow.committed # type: ignore

    async def test_add_auto_product_not_unique_barcode_does_nothing(self):
        bus_test_instance = bus_test()
        barcode = "0" * 4
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=True
        )
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(filter={"barcode": barcode})
            assert uow.committed # type: ignore
        assert len(products) == 0

    async def test_add_auto_non_food_product(self):
        bus_test_instance = bus_test()
        barcode = random_barcode()
        cmd = AddHouseInputAndCreateProductIfNeeded(
            barcode=barcode, house_id=random_attr("user_id"), is_food=False
        )
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            products = await uow.products.query(
                filter={"barcode": barcode}, hide_undefined_auto_products=False
            )
            product = products[0]
            assert product.is_food == False
            assert product.source_id == "auto"
            assert product.is_food_votes.is_not_food_houses == {cmd.house_id}
            assert uow.committed # type: ignore

    async def test_can_update_product_properties(self):
        bus_test_instance = bus_test()
        kwargs = random_add_food_product_cmd_kwargs()
        cmd = AddFoodProductBulk(add_product_cmds=[AddFoodProduct(**kwargs)])
        await bus_test_instance.handle(cmd)
        uow: UnitOfWork
        async with bus_test_instance.uow as uow:
            product = await uow.products.query()
            product = product[0]
            assert product is not None
            assert uow.committed # type: ignore
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
        await bus_test_instance.handle(cmd2)
        async with bus_test_instance.uow as uow:
            product = await uow.products.get(product.id)
            assert product is not None
            assert product.name == new_product_kwargs["name"]
            assert product.brand_id == new_product_kwargs["brand_id"]
            assert product.source_id == new_product_kwargs["source_id"]
            assert product.category_id == new_product_kwargs["category_id"]
            assert product.parent_category_id == new_product_kwargs["parent_category_id"]
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
        with pytest.raises(AttributeError) as exc:
            await bus_test_instance.handle(cmd3)

        cmd4 = UpdateProduct(product_id=product.id, updates={"_id": random_barcode()})
        with pytest.raises(AttributeError) as exc:
            await bus_test_instance.handle(cmd4)

        cmd5 = UpdateProduct(
            product_id=product.id, updates={"diet_types_ids": ["vegan"]}
        )
        with pytest.raises(AttributeError) as exc:
            await bus_test_instance.handle(cmd5)
