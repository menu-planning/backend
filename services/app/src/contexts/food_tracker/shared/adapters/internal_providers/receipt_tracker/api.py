import json
from ast import Tuple

import src.contexts.receipt_tracker.shared.endpoints.internal.internal as receipt_tracker_api
from src.contexts.food_tracker.shared.adapters.internal_providers.receipt_tracker.schemas import (
    ReceiptTrackerReceipt,
)


class ReceiptTrackerProvider:
    @staticmethod
    async def add(*, house_id: str, cfe_key: str, qrcode: str | None = None) -> None:
        await receipt_tracker_api.add(house_id, cfe_key, qrcode)

    @staticmethod
    async def get_receipt_and_add_item_bulk_for_house(
        *, cfe_key: str, house_ids: list[str] | None = None
    ) -> Tuple:
        receipt_json = await receipt_tracker_api.get(cfe_key)
        receipt = ReceiptTrackerReceipt(**json.loads(receipt_json))
        return receipt.to_domain_receipt(), receipt.to_domain_add_item_bulk(house_ids)
