from src.contexts._receipt_tracker.shared.domain.commands import AddReceipt
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException


async def add_receipt(cmd: AddReceipt, uow: UnitOfWork) -> None:
    """Add a receipt to a house. If the receipt already exists, add the house to the
    receipt. If the receipt doesn't exist, create a new receipt.

    Args:
        cmd: A :class:`AddReceipt <..domain.commands.AddReceipt>` instance.
        uow: A :class:`UnitOfWork <..services.async_uow.UnitOfWork>` instance.

    Returns:
        None
    """
    async with uow:
        try:
            receipt = await uow.receipts.get(cmd.cfe_key)
            if cmd.qrcode and not receipt.qrcode:
                receipt.qrcode = cmd.qrcode
            if cmd.house_id not in receipt.house_ids:
                receipt.add_house(cmd.house_id)
            await uow.receipts.persist(receipt)
            await uow.commit()
        except EntityNotFoundException:
            receipt = Receipt.add_receipt(
                cfe_key=cmd.cfe_key,
                house_ids=[cmd.house_id],
                qrcode=cmd.qrcode,
            )
            await uow.receipts.add(receipt)
            await uow.commit()
