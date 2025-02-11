import json

import src.contexts.products_catalog.shared.endpoints.internal.products as products_catalog_api
from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.schemas import (
    ProductsCatalogProduct,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models import (
    BrandSaModel,
    CategorySaModel,
    FoodGroupSaModel,
    ParentCategorySaModel,
    ProcessTypeSaModel,
    ProductSaModel,
    SourceSaModel,
)
from src.contexts.products_catalog.shared.adapters.ORM.sa_models.product import (
    ScoreSaModel,
)


class ProductsCatalogProvider:
    @staticmethod
    async def get(id: str) -> dict:
        product_data = await products_catalog_api.get(id)
        return ProductsCatalogProduct(**json.loads(product_data)).model_dump()

    @staticmethod
    async def query(filter: dict | None = None) -> list[dict]:
        products_data = await products_catalog_api.get_products(filter=filter)
        products_data = json.loads(products_data)
        return [
            ProductsCatalogProduct(**product).model_dump() for product in products_data
        ]

    @staticmethod
    async def get_filter_options(
        filter: dict | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        filter_data = await products_catalog_api.get_filter_options(filter=filter)
        return json.loads(filter_data)

    @staticmethod
    async def search_by_name(name: str) -> list[str]:
        names_data = await products_catalog_api.search_similar_name(name)
        return json.loads(names_data)

    @staticmethod
    async def add_house_input_and_create_product_if_needed(
        barcode: str,
        house_id: str,
        is_food: bool,
    ) -> None:
        await products_catalog_api.add_house_input_to_is_food_registry(
            barcode=barcode,
            house_id=house_id,
            is_food=is_food,
        )

    @staticmethod
    def product_sa_model_type() -> ProductSaModel:
        return ProductSaModel

    @staticmethod
    def source_sa_model_type() -> SourceSaModel:
        return SourceSaModel

    @staticmethod
    def brand_sa_model_type() -> BrandSaModel:
        return BrandSaModel

    @staticmethod
    def category_sa_model_type() -> CategorySaModel:
        return CategorySaModel

    @staticmethod
    def parent_category_sa_model_type() -> ParentCategorySaModel:
        return ParentCategorySaModel

    @staticmethod
    def food_group_sa_model_type() -> FoodGroupSaModel:
        return FoodGroupSaModel

    @staticmethod
    def process_type_sa_model_type() -> ProcessTypeSaModel:
        return ProcessTypeSaModel

    @staticmethod
    def score_sa_model_type() -> ScoreSaModel:
        return ScoreSaModel
