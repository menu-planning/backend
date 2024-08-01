from typing import Any

from src.contexts.receipt_tracker.shared.adapters.api_schemas.commands.add_receipt import (
    ApiAddReceipt,
)
from src.contexts.receipt_tracker.shared.adapters.api_schemas.commands.update_products import (
    ApiUpdateProducts,
)
from src.contexts.receipt_tracker.shared.adapters.api_schemas.entities.receipt import (
    ApiReceipt,
)
from src.contexts.receipt_tracker.shared.bootstrap.container import Container
from src.contexts.receipt_tracker.shared.services.uow import UnitOfWork

DEFAULT_CONTAINER = Container()
"""The default :class:`Container <..container.ApiProduct>` used to injecting 
dependencies, including bootstraping.
"""


async def get(cfe_key: str, container: Container = DEFAULT_CONTAINER) -> str:
    """Get a receipt with cfe_key.

    Args:
        cfe_key: A string representing the id of the receipt.
        bus: Defaults to :attr:`DEFAULT_CONTAINER
    `

    Returns:
        A json str of the :class:`ApiReceipt <..domain.entities.Receipt>`
            instance with cfe_key.
    """
    bus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        receipt = await uow.receipts.get(cfe_key)
        return ApiReceipt.from_domain(receipt).model_dump_json()


async def add(
    house_id: str,
    cfe_key: str,
    qrcode: str | None = None,
    container: Container = DEFAULT_CONTAINER,
) -> None:
    """Add a receipt to a house.

    Args:
        house_id: A string representing the id of the house.
        cfe_key: The string id of a receipt
        qrcode: A string representing the qrcode of the receipt.
        bus: Defaults to :attr:`DEFAULT_CONTAINER
    `

    Returns:
        None
    """
    bus = container.bootstrap()
    cmd = ApiAddReceipt(house_id=house_id, cfe_key=cfe_key, qrcode=qrcode).to_domain()
    await bus.handle(cmd)


async def update_product(
    cfe_key: str,
    barcode_product_mapping: dict[str, dict[str, Any]],
    container: Container = DEFAULT_CONTAINER,
) -> None:
    """Update products in receipt with cfe_key.

    Args:
        cfe_key: A string representing the cfe_key of the receipt.
        barcode_product_mapping: A string keyed mapping of a barcode to a string
            keyed mapping representation of :class:`ApiProduct <.api_schemas.ApiProduct>`.
        bus: Defaults to :attr:`DEFAULT_CONTAINER
    `

    Returns:
        None
    """
    bus = container.bootstrap()
    cmd = ApiUpdateProducts(
        cfe_key=cfe_key,
        barcode_product_mapping=barcode_product_mapping,
    ).to_domain()
    await bus.handle(cmd)
