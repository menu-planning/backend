import json
from datetime import datetime
from unittest import mock

import pytest
from aio_pika import Message, RobustChannel
from attrs import asdict
from src.contexts.food_tracker.fastapi.bootstrap import (
    fastapi_bootstrap,
    get_aio_pika_manager,
)
from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.food_tracker.shared.adapters.internal_providers.receipt_tracker.api import (
    ReceiptTrackerProvider,
)
from src.contexts.food_tracker.shared.domain.commands import (
    AddItem,
    AddItemBulk,
    AddReceipt,
    ChangeHouseName,
    CreateHouse,
    DiscardHouses,
    UpdateItem,
)
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.domain.rules import (
    CanNotChangeIsFoodAttributeOfItemWithUniqueBarcode,
)
from src.contexts.food_tracker.shared.rabbitmq_data import email_admin_new_event_data
from src.contexts.food_tracker.shared.services.uow import UnitOfWork
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.product import (
    ApiProduct,
)
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationException
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.rabbitmq.aio_pika_classes import AIOPikaData
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from tests.food_tracker.random_refs import (
    random_attr,
    random_barcode,
    random_cfe_key,
    random_create_house_classmethod_kwargs,
    random_house,
    random_item,
    random_receipt,
)
from tests.food_tracker.unit.fakes import FakeUnitOfWork
from tests.products_catalog.random_refs import (
    random_food_product,
    random_non_food_product,
    random_nutri_facts,
)

pytestmark = pytest.mark.anyio


def bus_mock(aio_pika_manager_mock=None) -> MessageBus:
    uow = FakeUnitOfWork()
    if aio_pika_manager_mock:
        return fastapi_bootstrap(uow, aio_pika_manager_mock)
    return fastapi_bootstrap(uow, get_aio_pika_manager())


async def test_can_create_house():
    bus_test = bus_mock()
    kwargs = random_create_house_classmethod_kwargs(prefix="test_new_house-")
    cmd = CreateHouse(
        owner_id=kwargs["owner_id"],
        name=kwargs["name"],
    )
    await bus_test.handle(cmd)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        house = await uow.houses.query()
        assert house[0] is not None
        assert house[0].owner_id == kwargs["owner_id"]
        assert uow.committed


async def test_can_change_house_name():
    bus_test = bus_mock()
    house = random_house(prefix="test_change_house_name-")
    uow: UnitOfWork
    async with bus_test.uow as uow:
        await uow.houses.add(house)
    new_name = random_attr("test_change_house_name-new_name")
    cmd = ChangeHouseName(house_id=house.id, name=new_name)
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        houses = await uow.houses.query(filter={"name": new_name})
        assert houses[0] is not None
        assert houses[0] is house


async def test_discard_houses():
    bus_test = bus_mock()
    house_name = random_attr("test_discard_house_name-")
    house = random_house(name=house_name)
    uow: UnitOfWork
    async with bus_test.uow as uow:
        await uow.houses.add(house)
    cmd = DiscardHouses(house_ids=[house.id])
    await bus_test.handle(cmd)
    async with bus_test.uow as uow:
        house = await uow.houses.query(filter={"name": house_name})
        assert house == []


class TestAddReceipt:
    async def test_publish_new_event_message(self):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        bus_test = bus_mock(
            aio_pika_manager_mock=aio_pika_manager_mock,
        )
        house = random_house(prefix="test_change_house_name-")
        uow: UnitOfWork
        async with bus_test.uow as uow:
            await uow.houses.add(house)

        # start acctual test
        cfe_key = random_cfe_key()
        cmd = AddReceipt(house_id=house.id, cfe_key=cfe_key)
        await bus_test.handle(cmd)
        async with bus_test.uow as uow:
            house = await uow.houses.query(filter={"name": house.name})
        house = house[0]
        receipts = list(house.pending_receipts)
        assert receipts[0].cfe_key == cfe_key
        assert receipts[0].qrcode is None

        assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 1
        for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
            for arg in list(call.kwargs.values()):
                if isinstance(arg, Message) and hasattr(arg, "body"):
                    msg = json.loads(arg.body.decode())
                    assert msg["event"]["event_name"] == "ReceiptCreated"
                    assert msg["event"]["house_id"] == house.id
                    assert msg["event"]["cfe_key"] == cfe_key
                    assert msg["event"]["qrcode"] is None

        queue_names = []
        for (
            call
        ) in aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_args_list:
            for arg in list(call.args):
                if isinstance(arg, AIOPikaData):
                    queue_names.append(arg.queue.name)
        assert aio_pika_manager_mock.declare_resources_from_AIOPikaData.await_count == 1
        assert len(queue_names) == 1
        assert email_admin_new_event_data.queue.name in queue_names

    async def test_calls_receipt_tracker_and_tries_to_add_items(self):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        receipt_provider_mock = mock.AsyncMock(spec=ReceiptTrackerProvider)
        attrs = {
            "add.return_value": None,
            "get_receipt_and_add_item_bulk_for_house.return_value": (
                None,
                AddItemBulk(add_item_cmds=[]),
            ),
        }
        receipt_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.receipt_created.add_receipt_to_and_retrieve_items_from_receipt_tracker.ReceiptTrackerProvider",
            receipt_provider_mock,
        ):
            bus_test: MessageBus = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            house = random_house(prefix="test_change_house_name-")
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)

            # start acctual test
            cfe_key = random_cfe_key()
            cmd = AddReceipt(house_id=house.id, cfe_key=cfe_key)
            await bus_test.handle(cmd)
            async with bus_test.uow as uow:
                house = await uow.houses.query(filter={"name": house.name})
            house = house[0]
            receipts = list(house.pending_receipts)
            assert receipts[0].cfe_key == cfe_key
            assert receipts[0].qrcode is None

            assert receipt_provider_mock.add.await_count == 1
            for call in receipt_provider_mock.add.await_args_list:
                for k, v in call.kwargs.items():
                    v == asdict(cmd).get(k)

            assert (
                receipt_provider_mock.get_receipt_and_add_item_bulk_for_house.await_count
                == 1
            )
            for (
                call
            ) in (
                receipt_provider_mock.get_receipt_and_add_item_bulk_for_house.await_args_list
            ):
                assert cfe_key in call.kwargs.values()
                assert [house.id] in call.kwargs.values()


class TestAddItemBulk:
    async def test_update_items_and_moves_receipts_from_pending_to_added(self):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )

        house = random_house(prefix="test_change_house_name-")
        receipt = random_receipt()
        house._pending_receipts = set([receipt])
        barcode_1 = random_barcode()
        product_2_name = random_attr("test_add_item_bulk-name")
        cmds: dict[AddItem, dict | None] = {
            AddItem(
                house_ids=[house.id],
                date=datetime.now(),
                amount={"quantity": 1, "unit": "kg"},
                description=random_attr("add_item_bulk-1"),
                price_per_unit=1.0,
                barcode=barcode_1,
                cfe_key=receipt.cfe_key,
            ): ApiProduct.from_domain(
                random_food_product(
                    barcode=barcode_1, name=random_attr("add_item_bulk-name")
                )
            ).model_dump(),
            AddItem(
                house_ids=[house.id],
                date=datetime.now(),
                amount={"quantity": 2, "unit": "kg"},
                description=product_2_name[:-3],
                price_per_unit=1.0,
                barcode="001",
                cfe_key=receipt.cfe_key,
            ): ApiProduct.from_domain(
                random_food_product(is_food=True, name=product_2_name)
            ).model_dump(),
            AddItem(
                house_ids=[house.id],
                date=datetime.now(),
                amount={"quantity": 3, "unit": "kg"},
                description=random_attr("add_item_bulk-3"),
                price_per_unit=1.0,
                barcode="002",
                cfe_key=receipt.cfe_key,
            ): None,
        }
        add_item_bulk_cmd = AddItemBulk(
            add_item_cmds=[
                list(cmds.keys())[0],
                list(cmds.keys())[1],
                list(cmds.keys())[2],
            ]
        )

        def query_products_side_effect(filter):
            if filter == {"barcode": list(cmds.keys())[0].barcode}:
                return [list(cmds.values())[0]]
            elif filter == {"name": [list(cmds.values())[1]["name"]]}:
                return [list(cmds.values())[1]]
            else:
                return []

        def search_by_name(value):
            if value == list(cmds.keys())[1].description:
                return [list(cmds.values())[1]["name"]]
            else:
                return []

        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.side_effect": query_products_side_effect,
            "search_by_name.side_effect": search_by_name,
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_added.update_item_product.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)

            # start acctual test
            await bus_test.handle(add_item_bulk_cmd)
            async with bus_test.uow as uow:
                houses = await uow.houses.query(filter={"name": house.name})
            house = houses[0]
            receipts = list(house.added_receipts)
            assert receipts[0].cfe_key == receipt.cfe_key
            assert receipts[0].qrcode is None

            async with bus_test.uow as uow:
                items = await uow.items.query(filter={"cfe_key": receipt.cfe_key})
            assert len(items) == 3
            for item in items:
                add_item_cmd = next(
                    i
                    for i in add_item_bulk_cmd.add_item_cmds
                    if i.description == item.description
                )
                assert item.house_id == house.id
                assert item.date == add_item_cmd.date
                assert item.amount == add_item_cmd.amount
                assert item.description == add_item_cmd.description
                assert item.price_per_unit == add_item_cmd.price_per_unit
                assert item.barcode == add_item_cmd.barcode
                assert item.cfe_key == add_item_cmd.cfe_key
                if cmds[add_item_cmd] is None:
                    assert item.is_food is None
                    assert item.product_id is None
                else:
                    assert item.is_food == cmds[add_item_cmd].get("is_food")
                    assert item.product_id == cmds[add_item_cmd].get("id")

    async def test_discard_item_if_unique_barcode_and_produt_is_not_food(self):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        house = random_house(prefix="test_change_house_name-")
        receipt = random_receipt()
        house._pending_receipts = set([receipt])
        item_product = random_non_food_product(
            barcode=random_barcode(),
            name=random_attr("test_add_item_bulk-name"),
        )
        add_item_cmd = AddItem(
            house_ids=[house.id],
            date=datetime.now(),
            amount={"quantity": 1, "unit": "kg"},
            description=random_attr("test_add_item_bulk-description"),
            price_per_unit=1.0,
            barcode=item_product.barcode,
            cfe_key=receipt.cfe_key,
        )
        attrs = {
            "query.return_value": [ApiProduct.from_domain(item_product).model_dump()],
            "search_by_name.return_value": [item_product.name],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_added.update_item_product.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)

            # start acctual test
            add_item_bulk_cmd = AddItemBulk(add_item_cmds=[add_item_cmd])
            await bus_test.handle(add_item_bulk_cmd)
            async with bus_test.uow as uow:
                item = await uow.items.query(
                    filter={"description": add_item_cmd.description}
                )
                assert item == []

    async def test_notify_admin_if_did_not_find_product(self):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.return_value": [],
            "search_by_name.return_value": [],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_added.update_item_product.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            house = random_house(prefix="test_change_house_name-")
            receipt = random_receipt()
            house._pending_receipts = set([receipt])
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)

            # start acctual test
            with_barcode = AddItem(
                house_ids=[house.id],
                date=datetime.now(),
                amount={"quantity": 1, "unit": "kg"},
                description=random_attr("test_add_item_bulk-description"),
                price_per_unit=1.0,
                barcode=random_barcode(),
                cfe_key=receipt.cfe_key,
            )
            no_barcode = AddItem(
                house_ids=[house.id],
                date=datetime.now(),
                amount={"quantity": 1, "unit": "kg"},
                description=random_attr("test_add_item_bulk-description"),
                price_per_unit=1.0,
                barcode="001",
                cfe_key=receipt.cfe_key,
            )
            add_item_bulk_cmd = AddItemBulk(add_item_cmds=[with_barcode, no_barcode])
            await bus_test.handle(add_item_bulk_cmd)

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
            assert email_admin_new_event_data.queue.name in queue_names
            assert len(set(queue_names)) == 1


class TestUpdateItem:
    async def test_user_input_for_is_food_register_only_for_unique_bacode_with_no_product(
        self,
    ):
        # setup
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.return_value": [],
            "search_by_name.return_value": [],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_is_food_changed.add_house_input_and_create_product_if_needed.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            house = random_house(prefix="test_change_house_name-")
            # receipt = random_receipt()
            items: list[Item] = []
            # house._pending_receipts = set([receipt])
            item_with_unique_barcode_with_no_product = random_item(
                house_id=house.id, barcode=random_barcode(), product_id=None
            )
            items.append(item_with_unique_barcode_with_no_product)
            product_with_unique_barcode = random_food_product(
                barcode=random_barcode(), nutri_facts=random_nutri_facts()
            )
            item_with_unique_barcode_with_product = random_item(
                house_id=house.id,
                barcode=product_with_unique_barcode.barcode,
                product_id=product_with_unique_barcode.id,
            )
            items.append(item_with_unique_barcode_with_product)
            product_without_barcode = random_food_product(barcode=None)
            item_without_unique_barcode_but_with_product = random_item(
                house_id=house.id,
                barcode="001",
                product_id=product_without_barcode.id,
            )
            items.append(item_without_unique_barcode_but_with_product)
            item_without_unique_barcode_and_product = random_item(
                house_id=house.id,
                barcode="002",
                product_id=None,
            )
            items.append(item_without_unique_barcode_and_product)
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)
                for item in items:
                    await uow.items.add(item)

            # start acctual test
            for item in items:
                update_item_cmd = UpdateItem(
                    item_id=item.id,
                    updates={
                        "date": item.date,
                        "description": item.description,
                        "amount": item.amount,
                        "is_food": False,
                        "price_per_unit": item.price_per_unit,
                        "product_id": None,
                    },
                )
                if item == item_with_unique_barcode_with_product:
                    with pytest.raises(BusinessRuleValidationException) as exc:
                        await bus_test.handle(update_item_cmd)
                    # assert any(
                    #     isinstance(e, BusinessRuleValidationException)
                    #     for e in exc.value.exceptions
                    # )
                    # assert (
                    #     exc.value.args[0]
                    #     == CanNotChangeIsFoodAttributeOfItemWithUniqueBarcode
                    # )
                else:
                    await bus_test.handle(update_item_cmd)
            assert (
                product_provider_mock.add_house_input_and_create_product_if_needed.await_count
                == 1
            )
            for (
                call
            ) in (
                product_provider_mock.add_house_input_and_create_product_if_needed.await_args_list
            ):
                assert (
                    call.kwargs["barcode"]
                    == item_with_unique_barcode_with_no_product.barcode
                )
                assert call.kwargs["house_id"] == house.id
                assert call.kwargs["is_food"] == False

    async def test_notify_admin_when_product_set_to_none(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.return_value": [],
            "search_by_name.return_value": [],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_added.update_item_product.ProductsCatalogProvider",
            product_provider_mock,
        ):
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            house = random_house(prefix="test_change_house_name-")
            item_with_unique_barcode_but_no_product = random_item(
                house_id=house.id, product_id=None
            )
            product_without_barcode = random_food_product(barcode=None)
            item_without_unique_barcode_and_no_product = random_item(
                house_id=house.id,
                barcode="002",
                product_id=None,
            )
            item_with_unique_barcode_but_no_product.events = []
            item_without_unique_barcode_and_no_product.events = []
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)
                await uow.items.add(item_with_unique_barcode_but_no_product)
                await uow.items.add(item_without_unique_barcode_and_no_product)

            # start acctual test
            notify = UpdateItem(
                item_id=item_with_unique_barcode_but_no_product.id,
                updates={
                    "product_id": None,
                },
            )
            await bus_test.handle(notify)
            does_not_notify = UpdateItem(
                item_id=item_without_unique_barcode_and_no_product.id,
                updates={
                    "product_id": product_without_barcode.id,
                },
            )
            await bus_test.handle(does_not_notify)

            assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 1
            for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
                for arg in list(call.kwargs.values()):
                    if isinstance(arg, Message) and hasattr(arg, "body"):
                        msg = json.loads(arg.body.decode())
                        assert msg["event"]["event_name"] == "ProductNotFound"
                        assert (
                            msg["event"]["item_id"]
                            == item_with_unique_barcode_but_no_product.id
                        )
                        assert (
                            msg["event"]["description"]
                            == item_with_unique_barcode_but_no_product.description
                        )
                        assert (
                            msg["event"]["barcode"]
                            == item_with_unique_barcode_but_no_product.barcode
                        )

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
                == 1
            )
            assert len(queue_names) == 1
            assert email_admin_new_event_data.queue.name in queue_names

    async def test_notify_admin_of_wrong_allocation_when_change_top_similiar_name_product(
        self,
    ):
        mock_channel = mock.Mock(spec=RobustChannel)
        aio_pika_manager_mock = mock.AsyncMock(
            spec=AIOPikaManager, channel=mock_channel
        )
        product_provider_mock = mock.AsyncMock(spec=ProductsCatalogProvider)
        attrs = {
            "query.return_value": [],
            "search_by_name.return_value": [],
        }
        product_provider_mock.configure_mock(**attrs)
        with mock.patch(
            "src.contexts.food_tracker.shared.services.event_handlers.item_added.update_item_product.ProductsCatalogProvider",
            product_provider_mock,
        ):
            house = random_house(prefix="test_change_house_name-")
            product_without_barcode = random_food_product(barcode=None)
            item_with_top_similar_name = random_item(
                house_id=house.id,
                barcode="002",
                product_id=product_without_barcode.id,
            )
            item_with_top_similar_name.ids_of_products_with_similar_names = [
                product_without_barcode.id,
                "id of another with similar name",
            ]
            product_without_barcode_too = random_food_product(barcode=None)
            item_without_top_similar_name = random_item(
                house_id=house.id,
                barcode="002",
                product_id=product_without_barcode_too.id,
            )
            bus_test = bus_mock(
                aio_pika_manager_mock=aio_pika_manager_mock,
            )
            uow: UnitOfWork
            async with bus_test.uow as uow:
                await uow.houses.add(house)
                await uow.items.add(item_with_top_similar_name)
                await uow.items.add(item_without_top_similar_name)

            item_with_top_similar_name.events = []
            item_without_top_similar_name.events = []

            # start acctual test
            notify = UpdateItem(
                item_id=item_with_top_similar_name.id,
                updates={
                    "product_id": "id of another with similar name",
                },
            )
            await bus_test.handle(notify)
            does_not_notify = UpdateItem(
                item_id=item_without_top_similar_name.id,
                updates={
                    "product_id": product_without_barcode_too.id,
                },
            )
            await bus_test.handle(does_not_notify)

            assert aio_pika_manager_mock.publish_from_AIOPikaData.await_count == 1
            for call in aio_pika_manager_mock.publish_from_AIOPikaData.await_args_list:
                for arg in list(call.kwargs.values()):
                    if isinstance(arg, Message) and hasattr(arg, "body"):
                        msg = json.loads(arg.body.decode())
                        assert msg["event"]["event_name"] == "WrongProductAllocated"
                        assert msg["event"]["item_id"] == item_with_top_similar_name.id
                        assert (
                            msg["event"]["description"]
                            == item_with_top_similar_name.description
                        )
                        assert msg["event"]["product_id"] == product_without_barcode.id

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
                == 1
            )
            assert len(queue_names) == 1
            assert email_admin_new_event_data.queue.name in queue_names
