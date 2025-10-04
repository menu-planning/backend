"""Repository for Meal entities with tag-aware query helpers and logging."""

from typing import Any, ClassVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.mappers.meal_mapper import (
    MealMapper,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import (
    MealSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.seedwork.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.adapters.repositories.filter_mapper import FilterColumnMapper
from src.contexts.seedwork.adapters.repositories.protocols import CompositeRepository
from src.contexts.seedwork.adapters.repositories.repository_logger import (
    RepositoryLogger,
)
from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
    SaGenericRepository,
)
from src.contexts.seedwork.adapters.tag_filter_builder import (
    TagFilterBuilder,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.logging.logger import get_logger


class MealRepo(CompositeRepository[Meal, MealSaModel]):
    """SQLAlchemy repository for Meal aggregate with enhanced tag filtering.

    Uses composition with TagFilter to provide standardized tag filtering
    methods that eliminate code duplication across repositories.

    Notes:
        Adheres to CompositeRepository interface. Eager-loads: recipes and ingredients.
        Performance: avoids N+1 via joinedload on recipes and nested ingredients.
        Transactions: methods require active UnitOfWork session.
    """

    filter_to_column_mappers: ClassVar[list[FilterColumnMapper]] = [
        FilterColumnMapper(
            sa_model_type=MealSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
                "description": "description",
                "menu_id": "menu_id",
                "author_id": "author_id",
                "total_time": "total_time",
                "weight_in_grams": "weight_in_grams",
                "created_at": "created_at",
                "updated_at": "updated_at",
                "like": "like",
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
            sa_model_type=ClientSaModel,
            filter_key_to_column_name={"client_name": "name"},
            join_target_and_on_clause=[
                (MenuSaModel, MealSaModel.menu_id == MenuSaModel.id),
                (ClientSaModel, MenuSaModel.client_id == ClientSaModel.id),
            ],
        ),
        FilterColumnMapper(
            sa_model_type=RecipeSaModel,
            filter_key_to_column_name={
                "recipe_id": "id",
                "recipe_name": "name",
            },
            join_target_and_on_clause=[(RecipeSaModel, MealSaModel.recipes)],
        ),
        FilterColumnMapper(
            sa_model_type=IngredientSaModel,
            filter_key_to_column_name={"products": "product_id"},
            join_target_and_on_clause=[
                (RecipeSaModel, MealSaModel.recipes),
                (IngredientSaModel, RecipeSaModel.ingredients),
            ],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        repository_logger: RepositoryLogger | None = None,
    ):
        """Initialize meal repository with database session and logging.

        Args:
            db_session: Active SQLAlchemy async session.
            repository_logger: Optional logger for query tracking.
        """
        self._session = db_session

        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("MealRepository")

        self._repository_logger = repository_logger

        # Initialize structured logger for this repository
        self._logger = get_logger("MealRepository")

        # Initialize tag filter as a composition attribute
        self.tag_filter = TagFilterBuilder(TagSaModel)

        self._generic_repo = SaGenericRepository(
            db_session=self._session,
            data_mapper=MealMapper,
            domain_model_type=Meal,
            sa_model_type=MealSaModel,
            filter_to_column_mappers=MealRepo.filter_to_column_mappers,
            repository_logger=self._repository_logger,
        )
        self.data_mapper = self._generic_repo.data_mapper
        self.domain_model_type = self._generic_repo.domain_model_type
        self.sa_model_type = self._generic_repo.sa_model_type
        self.seen = self._generic_repo.seen

    async def add(self, entity: Meal):
        """Add meal entity to repository.

        Args:
            entity: Meal domain object to persist.
        """
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Meal:
        """Retrieve meal by ID.

        Args:
            id: Unique identifier for the meal.

        Returns:
            Meal domain object.

        Raises:
            ValueError: If meal not found.
        """
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> MealSaModel:
        """Retrieve SQLAlchemy model instance by ID.

        Args:
            id: Unique identifier for the meal.

        Returns:
            MealSaModel SQLAlchemy instance.
        """
        return await self._generic_repo.get_sa_instance(id)

    async def get_meal_by_recipe_id(self, recipe_id: str) -> Meal:
        """Retrieve meal containing specific recipe.

        Args:
            recipe_id: ID of recipe to search for.

        Returns:
            Meal that contains the specified recipe.

        Raises:
            ValueError: If no meal found or multiple meals found for recipe.

        Notes:
            Performs data integrity check to ensure single meal per recipe.
        """
        self._logger.debug(
            "Searching for meal by recipe ID",
            recipe_id=recipe_id,
            operation="get_meal_by_recipe_id",
        )

        result = await self._generic_repo.query(filters={"recipe_id": recipe_id})

        if len(result) == 0:
            self._logger.warning(
                "Meal not found for recipe ID", recipe_id=recipe_id, result_count=0
            )
            error_msg = f"Meal with recipe id {recipe_id} not found."
            raise ValueError(error_msg)

        if len(result) > 1:
            self._logger.error(
                "Multiple meals found for single recipe ID - data integrity issue",
                recipe_id=recipe_id,
                result_count=len(result),
                meal_ids=[meal.id for meal in result],
            )
            error_msg = f"Multiple meals with recipe id {recipe_id} found."
            raise ValueError(error_msg)

        self._logger.debug(
            "Successfully found meal by recipe ID",
            recipe_id=recipe_id,
            meal_id=result[0].id,
            meal_name=result[0].name,
        )
        return result[0]

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
        _return_sa_instance: bool = False,
    ) -> list[Meal]:
        """Query meals with advanced filtering and tag support.

        Args:
            filters: Dictionary of filter criteria.
            starting_stmt: Custom SQLAlchemy select statement to build upon.
            limit: Maximum number of results to return.
            _return_sa_instance: Whether to return SQLAlchemy models.

        Returns:
            List of Meal domain objects matching criteria.

        Notes:
            Handles product similarity search and tag filtering automatically.
            Product search uses fuzzy matching with limit of 3 similar products.
        """
        filters = filters or {}

        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="query", entity_type="Meal", filter_count=len(filters)
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
                    "product_ids": (
                        product_ids[:5] if product_ids else []
                    ),  # Include first 5 IDs for context
                }

            # Handle tag filtering using TagFilter methods
            if "tags" in filters or "tags_not_exists" in filters:
                query_context["tag_filtering"] = True

                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type)

                if filters.get("tags"):
                    tags = filters.pop("tags")
                    self.tag_filter.validate_tag_format(tags)

                    tag_condition = self.tag_filter.build_tag_filter(
                        self.sa_model_type, tags, "meal"
                    )  # Using TagFilter method
                    starting_stmt = starting_stmt.where(tag_condition)

                    query_context["positive_tags"] = len(tags)
                    self._repository_logger.debug_filter_operation(
                        f"Applied positive tag filter: {len(tags)} tag conditions",
                        tags_count=len(tags),
                    )

                if filters.get("tags_not_exists"):
                    tags_not_exists = filters.pop("tags_not_exists")
                    self.tag_filter.validate_tag_format(tags_not_exists)

                    negative_tag_condition = self.tag_filter.build_negative_tag_filter(
                        self.sa_model_type, tags_not_exists, "meal"
                    )
                    starting_stmt = starting_stmt.where(negative_tag_condition)

                    query_context["negative_tags"] = len(tags_not_exists)
                    self._repository_logger.debug_filter_operation(
                        (
                            f"Applied negative tag filter: {len(tags_not_exists)} "
                            f"exclusion conditions"
                        ),
                        exclusion_tags_count=len(tags_not_exists),
                    )

                starting_stmt = starting_stmt.distinct()

            results = await self._generic_repo.query(
                filters=filters,
                starting_stmt=starting_stmt,
                limit=limit,
                _return_sa_instance=_return_sa_instance,
            )

            query_context["result_count"] = len(results)

            return results

    def list_filter_options(self) -> dict[str, dict]:
        """Return available filter and sort options for frontend.

        Returns:
            Dictionary mapping filter types to available options.
        """
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

    async def persist(self, domain_obj: Meal) -> None:
        """Persist meal changes to database.

        Args:
            domain_obj: Meal domain object to persist.

        Notes:
            Logs persistence operation with meal details and recipe count.
        """
        self._logger.info(
            "Persisting meal to database",
            meal_id=domain_obj.id,
            meal_name=domain_obj.name,
            operation="persist",
            has_recipes=len(domain_obj.recipes) > 0,
            recipe_count=len(domain_obj.recipes),
        )
        await self._generic_repo.persist(domain_obj)

        self._logger.debug(
            "Meal successfully persisted",
            meal_id=domain_obj.id,
            meal_name=domain_obj.name,
        )

    async def persist_all(self, domain_entities: list[Meal] | None = None) -> None:
        """Persist multiple meal entities in batch.

        Args:
            domain_entities: List of Meal domain objects to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
