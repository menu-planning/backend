from typing import Any, ClassVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.products_catalog.core.adapters.repositories import (
    ProductRepo,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.mappers.recipe_mapper import (
    RecipeMapper,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models import (
    IngredientSaModel,
    RecipeSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import (
    RepositoryLogger,
)
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository,
    FilterColumnMapper,
    SaGenericRepository,
)
from src.contexts.seedwork.shared.adapters.tag_filter_builder import (
    TagFilterBuilder,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.logging.logger import logger


class RecipeRepo(CompositeRepository[_Recipe, RecipeSaModel]):
    """
    RecipeRepository with enhanced tag filtering capabilities.

    Uses composition with TagFilter to provide standardized tag filtering
    methods that eliminate code duplication across repositories.
    """

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=RecipeSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "meal_id": "meal_id",
                "author_id": "author_id",
                "total_time": "total_time",
                "weight_in_grams": "weight_in_grams",
                "privacy": "privacy",
                "created_at": "created_at",
                "average_taste_rating": "average_taste_rating",
                "average_convenience_rating": "average_convenience_rating",
                "calories": "calories",
                "protein": "protein",
                "carbohydrate": "carbohydrate",
                "total_fat": "total_fat",
                "saturated_fat": "saturated_fat",
                "trans_fat": "trans_fat",
                "sugar": "sugar",
                "sodium": "sodium",
                "calorie_density": "calorie_density",
                "carbo_percentage": "carbo_percentage",
                "protein_percentage": "protein_percentage",
                "total_fat_percentage": "total_fat_percentage",
                "discarded": "discarded",
            },
        ),
        FilterColumnMapper(
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"products": "product_id"},
            join_target_and_on_clause=[(IngredientSaModel, RecipeSaModel.ingredients)],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        repository_logger: RepositoryLogger | None = None,
    ):
        self._session = db_session

        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("RecipeRepository")

        self._repository_logger = repository_logger

        # Initialize tag filter as a composition attribute
        self.tag_filter = TagFilterBuilder(TagSaModel)

        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=RecipeMapper,
            domain_model_type=_Recipe,
            sa_model_type=RecipeSaModel,
            filter_to_column_mappers=RecipeRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: _Recipe) -> None:
        error_msg = "Recipes must be added through the meal repo."
        raise NotImplementedError(error_msg)

    async def get(self, entity_id: str) -> _Recipe:
        return await self._generic_repo.get(entity_id)

    async def get_sa_instance(self, entity_id: str) -> RecipeSaModel:
        return await self._generic_repo.get_sa_instance(entity_id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
        _return_sa_instance: bool = False,
    ) -> list[_Recipe]:
        filters = filters or {}

        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="query", entity_type="Recipe", filter_count=len(filters)
        ) as query_context:

            # Handle product name similarity search
            if filters.get("product_name"):
                product_name = filters.pop("product_name")
                product_repo = ProductRepo(self._session)
                products = await product_repo.list_top_similar_names(
                    product_name, limit=3
                )
                product_ids = [product.id for product in products]
                filters["products"] = product_ids

                query_context["product_similarity_search"] = {
                    "search_term": product_name,
                    "products_found": len(product_ids),
                }

            # Handle tag filtering using TagFilter methods
            if "tags" in filters or "tags_not_exists" in filters:
                query_context["tag_filtering"] = True

                # Initialize starting statement if needed
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type)

                # Handle positive tag filtering
                if filters.get("tags"):
                    tags = filters.pop("tags")
                    self.tag_filter.validate_tag_format(tags)  # Using TagFilter method

                    tag_condition = self.tag_filter.build_tag_filter(
                        self.sa_model_type, tags, "recipe"
                    )  # Using TagFilter method
                    starting_stmt = starting_stmt.where(tag_condition)

                    query_context["positive_tags"] = len(tags)
                    self._repository_logger.debug_filter_operation(
                        f"Applied positive tag filter: {len(tags)} tag conditions",
                        tags_count=len(tags),
                    )

                # Handle negative tag filtering
                if filters.get("tags_not_exists"):
                    tags_not_exists = filters.pop("tags_not_exists")
                    self.tag_filter.validate_tag_format(
                        tags_not_exists
                    )  # Using TagFilter method

                    negative_tag_condition = self.tag_filter.build_negative_tag_filter(
                        self.sa_model_type, tags_not_exists, "recipe"
                    )  # Using TagFilter method
                    starting_stmt = starting_stmt.where(negative_tag_condition)

                    query_context["negative_tags"] = len(tags_not_exists)
                    self._repository_logger.debug_filter_operation(
                        (
                            f"Applied negative tag filter: {len(tags_not_exists)} "
                            f"exclusion conditions"
                        ),
                        exclusion_tags_count=len(tags_not_exists),
                    )

                # Ensure distinct results when using tag filters
                starting_stmt = starting_stmt.distinct()

            # Delegate to generic repository with all parameters
            results = await self._generic_repo.query(
                filters=filters,
                starting_stmt=starting_stmt,
                limit=limit,
                _return_sa_instance=_return_sa_instance,
            )

            # Update query context with results
            query_context["result_count"] = len(results)

            return results

    def list_filter_options(self) -> dict[str, dict]:
        return {
            "sort": {
                "type": FrontendFilterTypes.SORT.value,
                "options": [
                    "name",
                    "created_at",
                    "updated_at",
                    "total_time",
                    "average_taste_rating",
                    "average_convenience_rating",
                    "privacy",
                    "calories",
                    "protein",
                    "carbohydrate",
                    "total_fat",
                    "saturated_fat",
                    "trans_fat",
                    "dietary_fiber",
                    "sodium",
                    "sugar",
                ],
            },
        }

    async def persist(self, domain_obj: _Recipe) -> None:
        logger.debug(f"Persisting recipe: {domain_obj}")
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[_Recipe] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
