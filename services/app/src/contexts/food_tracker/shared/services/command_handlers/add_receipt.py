from typing import Annotated

from src.contexts.food_tracker.shared.domain.commands import (
    AddItem,
    AddItemBulk,
    AddReceipt,
    DiscardItems,
    InviteMember,
    InviteNutritionist,
    RemoveMember,
    RemoveNutritionist,
    UpdateItem,
)
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt
from src.contexts.food_tracker.shared.services.uow import UnitOfWork


async def add_receipt(cmd: AddReceipt, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.add_receipt(Receipt(cfe_key=cmd.cfe_key, qrcode=cmd.qrcode))
        await uow.houses.persist(house)
        await uow.commit()


async def add_item_bulk(cmd: AddItemBulk, uow: UnitOfWork) -> None:
    async with uow:
        receipts_to_discard: Annotated[dict[str, set[str]], "house_id:set(cfe_key)"] = (
            {}
        )
        for icmd in cmd.add_item_cmds:
            for house_id in icmd.house_ids:
                if receipts_to_discard.get(house_id):
                    receipts_to_discard[house_id].add(icmd.cfe_key)
                else:
                    receipts_to_discard[house_id] = set([icmd.cfe_key])
                item = Item.add_item(
                    house_id=house_id,
                    date=icmd.date,
                    description=icmd.description,
                    amount=icmd.amount,
                    is_food=icmd.is_food,
                    price_per_unit=icmd.price_per_unit,
                    barcode=icmd.barcode,
                    cfe_key=icmd.cfe_key,
                    product_id=icmd.product_id,
                )
                await uow.items.add(item)
        for house_id, cfe_keys in receipts_to_discard.items():
            house = await uow.houses.get(house_id)
            for cfe_key in cfe_keys:
                house.move_receipt_from_pending_to_added(cfe_key=cfe_key)
            await uow.houses.persist(house)
        await uow.commit()


async def add_item(cmd: AddItem, uow: UnitOfWork) -> None:
    async with uow:
        for house_id in cmd.house_ids:
            item = Item.add_item(
                house_id=house_id,
                date=cmd.date,
                description=cmd.description,
                amount=cmd.amount,
                is_food=cmd.is_food,
                price_per_unit=cmd.price_per_unit,
                barcode=cmd.barcode,
                cfe_key=cmd.cfe_key,
                product_id=cmd.product_id,
            )
            await uow.items.add(item)
        await uow.commit()


async def discard_items(cmd: DiscardItems, uow: UnitOfWork) -> None:
    async with uow:
        for item in cmd.item_ids:
            item = await uow.items.get(cmd.item_ids)
            item.delete()
            await uow.items.persist(item)
        await uow.commit()


async def update_item(cmd: UpdateItem, uow: UnitOfWork) -> None:
    async with uow:
        item = await uow.items.get(cmd.item_id)
        item.update_properties(**cmd.updates)
        await uow.items.persist(item)
        await uow.commit()


async def invite_member(cmd: InviteMember, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.invite_member(cmd.member_id)
        await uow.houses.persist(house)
        await uow.commit()


async def remove_member(cmd: RemoveMember, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.remove_member(cmd.member_id)
        await uow.houses.persist(house)
        await uow.commit()


async def invite_nutritionist(cmd: InviteNutritionist, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.invite_nutritionist(cmd.nutritionist_id)
        await uow.houses.persist(house)
        await uow.commit()


async def remove_nutritionist(cmd: RemoveNutritionist, uow: UnitOfWork) -> None:
    async with uow:
        house = await uow.houses.get(cmd.house_id)
        house.remove_nutritionist(cmd.nutritionist_id)
        await uow.houses.persist(house)
        await uow.commit()
