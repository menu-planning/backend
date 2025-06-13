from typing import Any, Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.products_catalog.core.adapters.repositories.product_repository import \
    ProductRepo
from src.contexts.recipes_catalog.core.adapters.meal.ORM.mappers.meal_mapper import MealMapper
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import IngredientSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import RecipeSaModel
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.seedwork.shared.adapters.enums import FrontendFilterTypes
from src.contexts.seedwork.shared.adapters.mixins.tag_filter_mixin import TagFilterMixin
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    CompositeRepository, FilterColumnMapper, SaGenericRepository)
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import \
    TagSaModel
from src.logging.logger import logger


class MealRepo(CompositeRepository[Meal, MealSaModel], TagFilterMixin):
    """
    MealRepository with enhanced tag filtering capabilities.
    
    Inherits from TagFilterMixin to provide standardized tag filtering
    methods that eliminate code duplication across repositories.
    """
    
    # Required by TagFilterMixin
    tag_model = TagSaModel
    
    filter_to_column_mappers = [
        FilterColumnMapper(
            sa_model_type=MealSaModel,
            filter_key_to_column_name={
                "id": "id",
                "name": "name",
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
            },
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
        repository_logger: Optional[RepositoryLogger] = None,
    ):
        self._session = db_session
        
        # Create default logger if none provided
        if repository_logger is None:
            repository_logger = RepositoryLogger.create_logger("MealRepository")
        
        self._repository_logger = repository_logger
        
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
        await self._generic_repo.add(entity)

    async def get(self, id: str) -> Meal:
        model_obj = await self._generic_repo.get(id)
        return model_obj # type: ignore

    async def get_sa_instance(self, id: str) -> MealSaModel:
        sa_obj = await self._generic_repo.get_sa_instance(id)
        return sa_obj
    
    async def get_meal_by_recipe_id(self, recipe_id: str) -> Meal:
        """
        Get meal by recipe id.
        """
        result = await self._generic_repo.query(filter={"recipe_id": recipe_id})
        if len(result) == 0:
            raise ValueError(f"Meal with recipe id {recipe_id} not found.")
        if len(result) > 1:
            raise ValueError(f"Multiple meals with recipe id {recipe_id} found.")
        return result[0]

    async def query(
        self,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
    ) -> list[Meal]:
        filter = filter or {}
        
        # Use the track_query context manager for structured logging
        async with self._repository_logger.track_query(
            operation="query", 
            entity_type="Meal",
            filter_count=len(filter)
        ) as query_context:
            
            # Handle product name similarity search
            if filter.get("product_name"):
                product_name = filter.pop("product_name")
                product_repo = ProductRepo(self._session)
                products = await product_repo.list_top_similar_names(product_name, limit=3)
                product_ids = [product.id for product in products]
                filter["products"] = product_ids
                
                query_context["product_similarity_search"] = {
                    "search_term": product_name,
                    "products_found": len(product_ids)
                }

            # Handle tag filtering using TagFilterMixin methods
            if "tags" in filter or "tags_not_exists" in filter:
                query_context["tag_filtering"] = True
                
                # Initialize starting statement if needed
                if starting_stmt is None:
                    starting_stmt = select(self.sa_model_type)
                
                # Handle positive tag filtering
                if filter.get("tags"):
                    tags = filter.pop("tags")
                    self.validate_tag_format(tags)  # Using TagFilterMixin method
                    
                    tag_condition = self.build_tag_filter(self.sa_model_type, tags, "meal")  # Using TagFilterMixin method
                    starting_stmt = starting_stmt.where(tag_condition)
                    
                    query_context["positive_tags"] = len(tags)
                    self._repository_logger.debug_filter_operation(
                        f"Applied positive tag filter: {len(tags)} tag conditions",
                        tags_count=len(tags)
                    )
                
                # Handle negative tag filtering
                if filter.get("tags_not_exists"):
                    tags_not_exists = filter.pop("tags_not_exists")
                    self.validate_tag_format(tags_not_exists)  # Using TagFilterMixin method
                    
                    negative_tag_condition = self.build_negative_tag_filter(self.sa_model_type, tags_not_exists, "meal")  # Using TagFilterMixin method
                    starting_stmt = starting_stmt.where(negative_tag_condition)
                    
                    query_context["negative_tags"] = len(tags_not_exists)
                    self._repository_logger.debug_filter_operation(
                        f"Applied negative tag filter: {len(tags_not_exists)} exclusion conditions",
                        exclusion_tags_count=len(tags_not_exists)
                    )
                
                # Ensure distinct results when using tag filters
                starting_stmt = starting_stmt.distinct()

            # Delegate to generic repository
            results = await self._generic_repo.query(
                filter=filter,
                starting_stmt=starting_stmt
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

    async def persist(self, domain_obj: Meal) -> None:
        logger.debug(f"Persisting meal: {domain_obj}")
        await self._generic_repo.persist(domain_obj)

    async def persist_all(self, domain_entities: list[Meal] | None = None) -> None:
        await self._generic_repo.persist_all(domain_entities)
