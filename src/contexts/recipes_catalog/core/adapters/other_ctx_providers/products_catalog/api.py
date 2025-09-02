import json

import src.contexts.products_catalog.core.internal_endpoints.products as products_catalog_api
from src.contexts.products_catalog.core.adapters.ORM.sa_models.brand import BrandSaModel
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.category_sa_model import (
    CategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.food_group_sa_model import (
    FoodGroupSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.parent_categorysa_model import (
    ParentCategorySaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.classification.process_type_sa_model import (
    ProcessTypeSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.product import (
    ProductSaModel,
    ScoreSaModel,
)
from src.contexts.products_catalog.core.adapters.ORM.sa_models.source import (
    SourceSaModel,
)
from src.contexts.recipes_catalog.core.adapters.other_ctx_providers.products_catalog.schemas import (
    ProductsCatalogProduct,
)


class ProductsCatalogProvider:
    """External provider for products catalog integration.

    Provides access to products catalog data through internal API endpoints.
    Handles JSON serialization/deserialization and type conversion.

    Notes:
        Integrates with products_catalog internal API.
        All methods are async and return serialized data.
    """

    @staticmethod
    async def get(id: str) -> dict:
        """Retrieve single product by ID.

        Args:
            id: Product identifier.

        Returns:
            Serialized product data as dictionary.
        """
        product_data = await products_catalog_api.get(id)
        return ProductsCatalogProduct(**json.loads(product_data)).model_dump()

    @staticmethod
    async def query(filter: dict | None = None) -> list[dict]:
        """Query products with optional filters.

        Args:
            filter: Optional filter criteria for products.

        Returns:
            List of serialized product data dictionaries.
        """
        products_data = await products_catalog_api.get_products(filters=filter)
        products_data = json.loads(products_data)
        return [
            ProductsCatalogProduct(**product).model_dump() for product in products_data
        ]

    @staticmethod
    async def get_filter_options(
        filter: dict | None = None,
    ) -> dict[str, dict[str, str | list[str]]]:
        """Retrieve available filter options for products.

        Args:
            filter: Optional filter criteria to scope available options.

        Returns:
            Dictionary mapping filter types to available values.
        """
        filter_data = await products_catalog_api.get_filter_options(filters=filter)
        return json.loads(filter_data)

    @staticmethod
    async def search_by_name(name: str) -> list[str]:
        """Search for products by name similarity.

        Args:
            name: Product name to search for.

        Returns:
            List of product names matching search criteria.
        """
        names_data = await products_catalog_api.search_similar_name(name)
        return json.loads(names_data)

    @staticmethod
    async def add_house_input_and_create_product_if_needed(
        barcode: str,
        house_id: str,
        is_food: bool,
    ) -> None:
        """Register house input for product creation workflow.

        Args:
            barcode: Product barcode identifier.
            house_id: House identifier.
            is_food: Whether the product is classified as food.

        Notes:
            Triggers product creation workflow if product doesn't exist.
        """
        await products_catalog_api.add_house_input_to_is_food_registry(
            barcode=barcode,
            house_id=house_id,
            is_food=is_food,
        )

    @staticmethod
    def product_sa_model_type() -> type[ProductSaModel]:
        """Return Product SQLAlchemy model type.

        Returns:
            ProductSaModel class type for ORM operations.
        """
        return ProductSaModel

    @staticmethod
    def source_sa_model_type() -> type[SourceSaModel]:
        """Return Source SQLAlchemy model type.

        Returns:
            SourceSaModel class type for ORM operations.
        """
        return SourceSaModel

    @staticmethod
    def brand_sa_model_type() -> type[BrandSaModel]:
        """Return Brand SQLAlchemy model type.

        Returns:
            BrandSaModel class type for ORM operations.
        """
        return BrandSaModel

    @staticmethod
    def category_sa_model_type() -> type[CategorySaModel]:
        """Return Category SQLAlchemy model type.

        Returns:
            CategorySaModel class type for ORM operations.
        """
        return CategorySaModel

    @staticmethod
    def parent_category_sa_model_type() -> type[ParentCategorySaModel]:
        """Return ParentCategory SQLAlchemy model type.

        Returns:
            ParentCategorySaModel class type for ORM operations.
        """
        return ParentCategorySaModel

    @staticmethod
    def food_group_sa_model_type() -> type[FoodGroupSaModel]:
        """Return FoodGroup SQLAlchemy model type.

        Returns:
            FoodGroupSaModel class type for ORM operations.
        """
        return FoodGroupSaModel

    @staticmethod
    def process_type_sa_model_type() -> type[ProcessTypeSaModel]:
        """Return ProcessType SQLAlchemy model type.

        Returns:
            ProcessTypeSaModel class type for ORM operations.
        """
        return ProcessTypeSaModel

    @staticmethod
    def score_sa_model_type() -> type[ScoreSaModel]:
        """Return Score SQLAlchemy model type.

        Returns:
            ScoreSaModel class type for ORM operations.
        """
        return ScoreSaModel
