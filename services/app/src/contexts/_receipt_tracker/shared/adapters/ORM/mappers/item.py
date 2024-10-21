from src.contexts._receipt_tracker.shared.adapters.ORM.sa_models.item import ItemSaModel
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.domain.value_objects import Amount


class ItemMapper(ModelMapper):
    @staticmethod
    def map_domain_to_sa(domain_obj: Item, receipt_id: str) -> ItemSaModel:
        return ItemSaModel(
            number=domain_obj.number,
            receipt_id=receipt_id,
            description=domain_obj.description,
            quantity=domain_obj.amount.quantity,
            unit=domain_obj.amount.unit,
            price_paid=domain_obj.price_paid,
            price_per_unit=domain_obj.price_per_unit,
            gross_price=domain_obj.gross_price,
            sellers_product_code=domain_obj.sellers_product_code,
            barcode=domain_obj.barcode,
            discount=domain_obj.discount,
            product_id=domain_obj.product.id if domain_obj.product else None,
            product_name=domain_obj.product.name if domain_obj.product else None,
            product_source=domain_obj.product.source if domain_obj.product else None,
            product_is_food=domain_obj.product.is_food if domain_obj.product else None,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ItemSaModel) -> Item:
        return Item(
            number=sa_obj.number,
            description=sa_obj.description,
            amount=Amount(
                quantity=sa_obj.quantity,
                unit=sa_obj.unit,
            ),
            price_paid=sa_obj.price_paid,
            price_per_unit=sa_obj.price_per_unit,
            gross_price=sa_obj.gross_price,
            sellers_product_code=sa_obj.sellers_product_code,
            barcode=sa_obj.barcode,
            discount=sa_obj.discount,
            product=Product(
                id=sa_obj.product_id,
                name=sa_obj.product_name,
                source=sa_obj.product_source,
                is_food=sa_obj.product_is_food,
            ),
        )
