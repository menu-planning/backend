from __future__ import annotations

from src.contexts._receipt_tracker.shared.adapters.repositories.receipt import (
    ReceiptRepo,
)
from src.contexts._receipt_tracker.shared.adapters.repositories.seller import SellerRepo
from src.contexts.seedwork.shared.services.uow import UnitOfWork as SeedUnitOfWork


class UnitOfWork(SeedUnitOfWork):
    async def __aenter__(self):
        await super().__aenter__()
        self.receipts = ReceiptRepo(self.session)
        self.sellers = SellerRepo(self.session)
        return self
