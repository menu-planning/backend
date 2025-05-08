from typing import Any

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductsCatalogProvider,
)
from src.contexts.food_tracker.shared.adapters.ORM.mappers.item import ItemMapper
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.items import ItemSaModel
from src.contexts.food_tracker.shared.domain.entities.item import Item
from src.contexts.seedwork.shared.adapters.repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)


class ItemsRepo(CompositeRepository[Item, ItemSaModel]):
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=ItemSaModel,
            filter_key_to_column_name={
                "product_id": "product_id",
                "house_id": "house_id",
                "date": "date",
                "barcode": "barcode",
                "cfe_key": "cfe_key",
                "is_food": "is_food",
                "description": "description",
            },
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.product_sa_model_type(),
            join_target_and_on_clause=[
                (ProductsCatalogProvider.product_sa_model_type(), ItemSaModel.product)
            ],
            filter_key_to_column_name={
                "product_name": "name",
                "calories": "calories",
                "protein": "protein",
                "carbohydrate": "carbohydrate",
                "total_fat": "total_fat",
                "saturated_fat": "saturated_fat",
                "trans_fat": "trans_fat",
                "dietary_fiber": "dietary_fiber",
                "sodium": "sodium",
                "arachidonic_acid": "arachidonic_acid",
                "ashes": "ashes",
                "dha": "dha",
                "epa": "epa",
                "sugar": "sugar",
                "starch": "starch",
                "biotin": "biotin",
                "boro": "boro",
                "caffeine": "caffeine",
                "calcium": "calcium",
                "chlorine": "chlorine",
                "copper": "copper",
                "cholesterol": "cholesterol",
                "choline": "choline",
                "chrome": "chrome",
                "dextrose": "dextrose",
                "sulfur": "sulfur",
                "phenylalanine": "phenylalanine",
                "iron": "iron",
                "insoluble_fiber": "insoluble_fiber",
                "soluble_fiber": "soluble_fiber",
                "fluor": "fluor",
                "phosphorus": "phosphorus",
                "fructo_oligosaccharides": "fructo_oligosaccharides",
                "fructose": "fructose",
                "galacto_oligosaccharides": "galacto_oligosaccharides",
                "galactose": "galactose",
                "glucose": "glucose",
                "glucoronolactone": "glucoronolactone",
                "monounsaturated_fat": "monounsaturated_fat",
                "polyunsaturated_fat": "polyunsaturated_fat",
                "guarana": "guarana",
                "inositol": "inositol",
                "inulin": "inulin",
                "iodine": "iodine",
                "l_carnitine": "l_carnitine",
                "l_methionine": "l_methionine",
                "lactose": "lactose",
                "magnesium": "magnesium",
                "maltose": "maltose",
                "manganese": "manganese",
                "molybdenum": "molybdenum",
                "linolenic_acid": "linolenic_acid",
                "linoleic_acid": "linoleic_acid",
                "omega_7": "omega_7",
                "omega_9": "omega_9",
                "oleic_acid": "oleic_acid",
                "other_carbo": "other_carbo",
                "polydextrose": "polydextrose",
                "polyols": "polyols",
                "potassium": "potassium",
                "sacarose": "sacarose",
                "selenium": "selenium",
                "silicon": "silicon",
                "sorbitol": "sorbitol",
                "sucralose": "sucralose",
                "taurine": "taurine",
                "vitamin_a": "vitamin_a",
                "vitamin_b1": "vitamin_b1",
                "vitamin_b2": "vitamin_b2",
                "vitamin_b3": "vitamin_b3",
                "vitamin_b5": "vitamin_b5",
                "vitamin_b6": "vitamin_b6",
                "folic_acid": "folic_acid",
                "vitamin_b12": "vitamin_b12",
                "vitamin_c": "vitamin_c",
                "vitamin_d": "vitamin_d",
                "vitamin_e": "vitamin_e",
                "vitamin_k": "vitamin_k",
                "zinc": "zinc",
                "retinol": "retinol",
                "thiamine": "thiamine",
                "riboflavin": "riboflavin",
                "pyridoxine": "pyridoxine",
                "niacin": "niacin",
            },
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.source_sa_model_type(),
            filter_key_to_column_name={"product_source": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.source_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().source,
                )
            ],
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.brand_sa_model_type(),
            filter_key_to_column_name={"product_brand": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.brand_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().brand,
                )
            ],
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.category_sa_model_type(),
            filter_key_to_column_name={"product_category": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.category_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().category,
                )
            ],
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.parent_category_sa_model_type(),
            filter_key_to_column_name={"product_parent_category": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.parent_category_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().parent_category,
                )
            ],
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.food_group_sa_model_type(),
            filter_key_to_column_name={"product_food_group": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.food_group_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().food_group,
                )
            ],
        ),
        FilterColumnMapper(
            sa_model_type=ProductsCatalogProvider.process_type_sa_model_type(),
            filter_key_to_column_name={"product_process_type": "name"},
            join_target_and_on_clause=[
                (
                    ProductsCatalogProvider.process_type_sa_model_type(),
                    ProductsCatalogProvider.product_sa_model_type().process_type,
                )
            ],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
    ):
        self._session = db_session
        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=ItemMapper,
            domain_model_type=Item,
            sa_model_type=ItemSaModel,
            filter_to_column_mappers=ItemsRepo.filter_to_column_mappers,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Item):
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Item:
        model_obj = await self._generic_repo.get(id)
        return model_obj

    async def get_sa_instance(self, id: str) -> ItemSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj

    async def query(
        self,
        filter: dict[str, Any] = {},
        starting_stmt: Select | None = None,
    ) -> list[Item]:
        model_objs: list[Item] = await self._generic_repo.query(
            filter=filter, starting_stmt=starting_stmt
        )
        return model_objs

    async def persist(self, domain_obj: Item) -> None:
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Item] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
