from dataclasses import asdict as dataclass_asdict

import src.contexts.seedwork.shared.utils as utils
from attrs import asdict as attrs_asdict
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.items import (
    AmountSaModel,
    ItemSaModel,
)
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.product import (
    ProductSaModel,
)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.shared_kernel.domain.value_objects import Amount


class ItemMapper(ModelMapper):
    @staticmethod
    async def map_domain_to_sa(session: AsyncSession, domain_obj: Item) -> ItemSaModel:
        if domain_obj.product_id:
            product = await utils.get_sa_entity(
                session=session,
                sa_model_type=ProductSaModel,
                filter={"id": domain_obj.product_id},
            )
        else:
            product = None
        return ItemSaModel(
            id=domain_obj.id,
            house_id=domain_obj.house_id,
            date=domain_obj.date,
            description=domain_obj.description,
            amount=AmountSaModel(**attrs_asdict(domain_obj.amount)),
            is_food=domain_obj.is_food,
            product_id=domain_obj.product_id,
            price_per_unit=domain_obj.price_per_unit,
            barcode=domain_obj.barcode,
            cfe_key=domain_obj.cfe_key,
            ids_of_products_with_similar_names=domain_obj.ids_of_products_with_similar_names,
            discarded=domain_obj.discarded,
            version=domain_obj.version,
            # relationships
            product=product,
        )

    @staticmethod
    def map_sa_to_domain(sa_obj: ItemSaModel) -> Item:
        return Item(
            id=sa_obj.id,
            house_id=sa_obj.house_id,
            date=sa_obj.date,
            description=sa_obj.description,
            amount=Amount(**dataclass_asdict(sa_obj.amount)),
            is_food=sa_obj.is_food,
            product_id=sa_obj.product_id,
            price_per_unit=sa_obj.price_per_unit,
            barcode=sa_obj.barcode,
            cfe_key=sa_obj.cfe_key,
            ids_of_productos_with_similar_names=sa_obj.ids_of_products_with_similar_names,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )
