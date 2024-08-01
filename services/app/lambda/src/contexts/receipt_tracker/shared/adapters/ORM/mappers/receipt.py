from src.contexts.receipt_tracker.shared.adapters.ORM.mappers.item import ItemMapper
from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.house import (
    HousesSaModel,
)
from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.receipt import (
    ReceiptSaModel,
)
from src.contexts.receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper


class ReceiptMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Receipt) -> ReceiptSaModel:
        return ReceiptSaModel(
            id=domain_obj.id,
            house_ids=[HousesSaModel(id=i) for i in domain_obj.house_ids],
            qrcode=domain_obj.qrcode,
            date=domain_obj.date,
            state=domain_obj.state,
            seller_id=domain_obj.seller_id,
            scraped=domain_obj.scraped,
            products_added=domain_obj.products_added,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            items=[
                ItemMapper.map_domain_to_sa(item, domain_obj.id)
                for item in domain_obj.items
            ],
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ReceiptSaModel) -> Receipt:
        return Receipt(
            cfe_key=sa_obj.id,
            house_ids=[house.id for house in sa_obj.house_ids],
            qrcode=sa_obj.qrcode,
            date=sa_obj.date,
            state=sa_obj.state,
            seller_id=sa_obj.seller_id,
            scraped=sa_obj.scraped,
            products_added=sa_obj.products_added,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
            items=[ItemMapper.map_sa_to_domain(item) for item in sa_obj.items],
        )
