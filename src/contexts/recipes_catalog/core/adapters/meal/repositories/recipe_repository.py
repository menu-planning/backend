"""Repository for `Recipe` entities with tag-aware query helpers.

Provides composition over a generic SQLAlchemy repository and adds
tag filtering support plus product-name similarity search.
"""

from typing import Any, ClassVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.products_catalog.core.adapters.repositories.product_repository import (
    ProductRepo,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.mappers.recipe_mapper import (
    RecipeMapper,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
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


class RecipeRepo(CompositeRepository[_Recipe, RecipeSaModel]):
    """SQLAlchemy repository for Recipe entities with enhanced tag filtering.

    Uses composition with TagFilter to provide standardized tag filtering
    methods that eliminate code duplication across repositories.

    Notes:
        Adheres to CompositeRepository interface. Eager-loads: ingredients.
        Performance: avoids N+1 via joinedload on ingredients.
        Transactions: methods require active UnitOfWork session.
        Recipes must be added through meal repository, not directly.
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
        FilterColumnMapper(
            sa_model_type=ClientSaModel,
            filter_key_to_column_name={"client_name": "name"},
            join_target_and_on_clause=[
                (RecipeSaModel, MealSaModel.recipes),
                (MenuSaModel, MealSaModel.menu_id == MenuSaModel.id),
                (ClientSaModel, MenuSaModel.client_id == ClientSaModel.id),
            ],
        ),
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        repository_logger: RepositoryLogger | None = None,
    ):
        """Initialize recipe repository with database session and logging.

        Args:
            db_session: Active SQLAlchemy async session.
            repository_logger: Optional logger for query tracking.
        """
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
        """Recipes must be added through the meal repository.

        Args:
            entity: Recipe entity to add

        Raises:
            NotImplementedError: Always raised as recipes must be added via meal repo

        Notes:
            This method is intentionally not implemented to enforce proper
            aggregate boundaries - recipes should only exist within meals.
        """
        self._repository_logger.logger.warning(
            "Attempted to add recipe directly to recipe repository",
            recipe_id=entity.id,
            recipe_name=entity.name,
            operation="add_recipe_direct",
            error_type="not_implemented",
        )
        error_msg = "Recipes must be added through the meal repo."
        raise NotImplementedError(error_msg)

    async def get(self, id: str) -> _Recipe:
        """Retrieve recipe by ID.

        Args:
            id: Unique identifier for the recipe.

        Returns:
            Recipe domain object.

        Raises:
            ValueError: If recipe not found.
        """
        return await self._generic_repo.get(id)

    async def get_sa_instance(self, id: str) -> RecipeSaModel:
        """Retrieve SQLAlchemy model instance by ID.

        Args:
            id: Unique identifier for the recipe.

        Returns:
            RecipeSaModel SQLAlchemy instance.
        """
        return await self._generic_repo.get_sa_instance(id)

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        limit: int | None = None,
        _return_sa_instance: bool = False,
    ) -> list[_Recipe]:
        """Query recipes with advanced filtering and tag support.

        Args:
            filters: Dictionary of filter criteria.
            starting_stmt: Custom SQLAlchemy select statement to build upon.
            limit: Maximum number of results to return.
            _return_sa_instance: Whether to return SQLAlchemy models.

        Returns:
            List of Recipe domain objects matching criteria.

        Notes:
            Handles product similarity search and tag filtering automatically.
            Product search uses fuzzy matching with limit of 3 similar products.
        """
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
                    self._repository_logger.logger.debug(
                        "Applied positive tag filter",
                        operation="tag_filter_positive",
                        tags_count=len(tags),
                        tag_names=[
                            tag.get("name")
                            for tag in tags
                            if isinstance(tag, dict) and "name" in tag
                        ],
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
                    self._repository_logger.logger.debug(
                        "Applied negative tag filter",
                        operation="tag_filter_negative",
                        exclusion_tags_count=len(tags_not_exists),
                        excluded_tag_names=[
                            tag.get("name")
                            for tag in tags_not_exists
                            if isinstance(tag, dict) and "name" in tag
                        ],
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

    async def persist(self, domain_obj: _Recipe) -> None:
        """Persist recipe changes to database.

        Args:
            domain_obj: Recipe domain object to persist.

        Notes:
            Logs persistence operation with recipe details and ingredient count.
        """
        self._repository_logger.logger.info(
            "Persisting recipe entity",
            recipe_id=domain_obj.id,
            recipe_name=domain_obj.name,
            operation="persist_recipe",
            has_ingredients=len(domain_obj.ingredients) > 0,
            ingredient_count=len(domain_obj.ingredients),
        )
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[_Recipe] | None = None) -> None:
        """Persist multiple recipe entities in batch.

        Args:
            domain_entities: List of Recipe domain objects to persist.
        """
        await self._generic_repo.persist_all(domain_entities)
