from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import (
    RatingSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import (
    RecipeSaModel,
)
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.seedwork.adapters.ORM.mappers import helpers
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.shared_kernel.adapters.name_search import StrProcessor
from src.contexts.shared_kernel.adapters.ORM.mappers.nutri_facts_mapper import (
    NutriFactsMapper,
)
from src.contexts.shared_kernel.adapters.ORM.mappers.tag.tag_mapper import TagMapper
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy
from src.logging.logger import structlog_logger


class RecipeMapper(ModelMapper):
    """Mapper for converting between Recipe domain objects and SQLAlchemy models.

    Handles complex mapping including nested ingredients, ratings, tags, and
    nutritional facts. Performs concurrent mapping of child entities with
    timeout protection.

    Notes:
        Lossless: Yes. Timezone: UTC assumption. Currency: N/A.
        Handles async operations with 5-second timeout for child entity mapping.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession, domain_obj: _Recipe, merge: bool = True
    ) -> RecipeSaModel:
        """Map domain recipe to SQLAlchemy model.

        Args:
            session: Database session for operations.
            domain_obj: Recipe domain object to map.
            merge: Whether to merge with existing database entity.

        Returns:
            SQLAlchemy recipe model ready for persistence.

        Notes:
            Maps child entities (ingredients, ratings, tags) concurrently.
            Uses 5-second timeout for child entity mapping operations.
            Handles existing recipe merging and child entity updates.
        """
        logger = structlog_logger("recipe_mapper")
        merge_children = False
        recipe_on_db = await helpers.get_sa_entity(
            session=session, sa_model_type=RecipeSaModel, filters={"id": domain_obj.id}
        )
        if not recipe_on_db and merge:
            # if recipe on db then it will be merged
            # so we should not need merge the children
            merge_children = True
        # if not is_domain_obj_discarded:
        tags_tasks = (
            [TagMapper.map_domain_to_sa(session, i) for i in domain_obj.tags]
            if domain_obj.tags
            else []
        )
        ratings_tasks = (
            [
                _RatingMapper.map_domain_to_sa(
                    session=session,
                    parent=domain_obj,
                    domain_obj=r,
                    merge=merge_children,
                )
                for r in domain_obj.ratings
            ]
            if domain_obj.ratings
            else []
        )
        ingredients_tasks = (
            [
                _IngredientMapper.map_domain_to_sa(
                    session=session,
                    parent=domain_obj,
                    domain_obj=i,
                    merge=merge_children,
                )
                for i in domain_obj.ingredients
            ]
            if domain_obj.ingredients
            else []
        )

        combined_tasks = tags_tasks + ratings_tasks + ingredients_tasks

        # If we have any tasks, gather them in one call.
        if combined_tasks:
            logger.debug(
                "Mapping recipe child entities",
                recipe_id=domain_obj.id,
                tags_count=len(tags_tasks),
                ratings_count=len(ratings_tasks),
                ingredients_count=len(ingredients_tasks),
                total_tasks=len(combined_tasks)
            )
            try:
                combined_results = await helpers.gather_results_with_timeout(
                    combined_tasks,
                    timeout=5,
                    timeout_message="Timeout mapping recipes and tags in RecipeMapper",
                )
            except Exception as e:
                logger.error(
                    "Failed to map recipe child entities",
                    recipe_id=domain_obj.id,
                    error=str(e),
                    tags_count=len(tags_tasks),
                    ratings_count=len(ratings_tasks),
                    ingredients_count=len(ingredients_tasks)
                )
                raise
            # Split the combined results back into recipes and tags.
            tags = combined_results[: len(tags_tasks)]
            ratings = combined_results[
                len(tags_tasks) : len(tags_tasks) + len(ratings_tasks)
            ]
            ingredients = combined_results[len(tags_tasks) + len(ratings_tasks) :]
        else:
            # No child entities to map - this is normal for recipes without tags, ratings, or ingredients
            tags = []
            ratings = []
            ingredients = []

        sa_recipe_kwargs = {
            "id": domain_obj.id,
            "meal_id": domain_obj.meal_id,
            "name": domain_obj.name,
            "preprocessed_name": StrProcessor(domain_obj.name).output,
            "description": domain_obj.description,
            "instructions": domain_obj.instructions,
            "author_id": domain_obj.author_id,
            "utensils": domain_obj.utensils,
            "total_time": domain_obj.total_time,
            "notes": domain_obj.notes,
            "privacy": domain_obj.privacy.value,
            "nutri_facts": await NutriFactsMapper.map_domain_to_sa(
                session, domain_obj.nutri_facts
            ),
            "calorie_density": domain_obj.calorie_density,
            "carbo_percentage": (
                domain_obj.macro_division.carbohydrate
                if domain_obj.macro_division
                else None
            ),
            "protein_percentage": (
                domain_obj.macro_division.protein if domain_obj.macro_division else None
            ),
            "total_fat_percentage": (
                domain_obj.macro_division.fat if domain_obj.macro_division else None
            ),
            "weight_in_grams": domain_obj.weight_in_grams,
            "image_url": domain_obj.image_url,
            "created_at": (
                domain_obj.created_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "updated_at": (
                domain_obj.updated_at if domain_obj.created_at else datetime.now(UTC)
            ),
            "discarded": domain_obj.discarded,
            "version": domain_obj.version,
            "average_taste_rating": domain_obj.average_taste_rating,
            "average_convenience_rating": domain_obj.average_convenience_rating,
            # relationships
            "ingredients": ingredients,
            "tags": tags,
            "ratings": ratings,
        }

        sa_recipe = RecipeSaModel(**sa_recipe_kwargs)
        if recipe_on_db:  # and merge and not is_domain_obj_discarded:
            logger.debug(
                "Merging existing recipe",
                recipe_id=domain_obj.id,
                recipe_name=domain_obj.name
            )
            return await session.merge(sa_recipe)  # , meal_on_db)

        logger.debug(
            "Creating new recipe",
            recipe_id=domain_obj.id,
            recipe_name=domain_obj.name
        )
        return sa_recipe

    @staticmethod
    def map_sa_to_domain(sa_obj: RecipeSaModel) -> _Recipe:
        """Map SQLAlchemy recipe model to domain object.

        Args:
            sa_obj: SQLAlchemy recipe model to convert.

        Returns:
            Recipe domain object with all relationships mapped.

        Notes:
            Maps nested ingredients, ratings, and tags using their respective mappers.
            Converts privacy enum from string to domain enum.
        """
        return _Recipe(
            entity_id=sa_obj.id,
            meal_id=sa_obj.meal_id,
            name=sa_obj.name,
            description=sa_obj.description,
            ingredients=[
                _IngredientMapper.map_sa_to_domain(i) for i in sa_obj.ingredients
            ],
            instructions=sa_obj.instructions,
            author_id=sa_obj.author_id,
            utensils=sa_obj.utensils,
            total_time=sa_obj.total_time,
            notes=sa_obj.notes,
            tags={TagMapper.map_sa_to_domain(t) for t in sa_obj.tags},
            privacy=Privacy(sa_obj.privacy),
            ratings=[_RatingMapper.map_sa_to_domain(i) for i in sa_obj.ratings],
            nutri_facts=NutriFactsMapper.map_sa_to_domain(sa_obj.nutri_facts),
            weight_in_grams=sa_obj.weight_in_grams,
            image_url=sa_obj.image_url,
            created_at=sa_obj.created_at,
            updated_at=sa_obj.updated_at,
            discarded=sa_obj.discarded,
            version=sa_obj.version,
        )


class _IngredientMapper:
    """Private mapper for converting between Ingredient domain objects and SQLAlchemy models.

    Handles ingredient mapping within recipe context, including preprocessing
    of ingredient names for search capabilities.

    Notes:
        Lossless: Yes. Timezone: N/A. Currency: N/A.
        Maps ingredient names to preprocessed versions for similarity search.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        parent: _Recipe,
        domain_obj: Ingredient,
        merge: bool = True,
    ) -> IngredientSaModel:
        """Map domain ingredient to SQLAlchemy model.

        Args:
            session: Database session for operations.
            parent: Parent recipe domain object.
            domain_obj: Ingredient domain object to map.
            merge: Whether to merge with existing entity.

        Returns:
            SQLAlchemy ingredient model ready for persistence.

        Notes:
            Searches for existing ingredient by recipe_id and name.
            Updates existing ingredient if found, otherwise creates new one.
            Preprocesses ingredient name for similarity search.
        """
        logger = structlog_logger("ingredient_mapper")
        ingredient_on_db: IngredientSaModel = await helpers.get_sa_entity(
            session=session,
            sa_model_type=IngredientSaModel,
            filters={"recipe_id": parent.id, "name": domain_obj.name},
        )
        ingredient_on_entity = IngredientSaModel(
            name=domain_obj.name,
            preprocessed_name=StrProcessor(domain_obj.name).output,
            quantity=domain_obj.quantity,
            unit=domain_obj.unit.value,
            recipe_id=parent.id,
            full_text=domain_obj.full_text,
            product_id=domain_obj.product_id,
            position=domain_obj.position,
        )
        if ingredient_on_db and merge:
            logger.debug(
                "Merging existing ingredient",
                recipe_id=parent.id,
                ingredient_name=domain_obj.name,
                product_id=domain_obj.product_id
            )
            return await session.merge(ingredient_on_entity)  # , ingredient_on_db)
        if ingredient_on_db:
            logger.debug(
                "Updating existing ingredient without merge",
                recipe_id=parent.id,
                ingredient_name=domain_obj.name,
                product_id=domain_obj.product_id
            )
            ingredient_on_db.name = ingredient_on_entity.name
            ingredient_on_db.preprocessed_name = ingredient_on_entity.preprocessed_name
            ingredient_on_db.quantity = ingredient_on_entity.quantity
            ingredient_on_db.unit = ingredient_on_entity.unit
            ingredient_on_db.recipe_id = ingredient_on_entity.recipe_id
            ingredient_on_db.full_text = ingredient_on_entity.full_text
            ingredient_on_db.product_id = ingredient_on_entity.product_id
            ingredient_on_db.position = ingredient_on_entity.position
            return ingredient_on_db

        logger.debug(
            "Creating new ingredient",
            recipe_id=parent.id,
            ingredient_name=domain_obj.name,
            product_id=domain_obj.product_id
        )
        return ingredient_on_entity

    @staticmethod
    def map_sa_to_domain(sa_obj: IngredientSaModel) -> Ingredient:
        """Map SQLAlchemy ingredient model to domain object.

        Args:
            sa_obj: SQLAlchemy ingredient model to convert.

        Returns:
            Ingredient domain object.

        Notes:
            Converts unit enum from string to domain enum.
        """
        return Ingredient(
            name=sa_obj.name,
            quantity=sa_obj.quantity,
            unit=MeasureUnit(sa_obj.unit),
            full_text=sa_obj.full_text,
            product_id=sa_obj.product_id,
            position=sa_obj.position,
        )


class _RatingMapper(ModelMapper):
    """Private mapper for converting between Rating domain objects and SQLAlchemy models.

    Handles rating mapping within recipe context, including user-specific
    rating data for taste and convenience.

    Notes:
        Lossless: Yes. Timezone: N/A. Currency: N/A.
        Maps user-specific ratings by user_id and recipe_id combination.
    """

    @staticmethod
    async def map_domain_to_sa(
        session: AsyncSession,
        parent: _Recipe,
        domain_obj: Rating,
        merge: bool = True,
    ) -> RatingSaModel:
        """Map domain rating to SQLAlchemy model.

        Args:
            session: Database session for operations.
            parent: Parent recipe domain object.
            domain_obj: Rating domain object to map.
            merge: Whether to merge with existing entity.

        Returns:
            SQLAlchemy rating model ready for persistence.

        Notes:
            Searches for existing rating by user_id and recipe_id.
            Updates existing rating if found, otherwise creates new one.
            Handles taste and convenience rating components.
        """
        logger = structlog_logger("rating_mapper")
        rating_on_db: RatingSaModel = await helpers.get_sa_entity(
            session=session,
            sa_model_type=RatingSaModel,
            filters={"user_id": domain_obj.user_id, "recipe_id": parent.id},
        )
        rating_on_entity = RatingSaModel(
            user_id=domain_obj.user_id,
            recipe_id=parent.id,
            taste=domain_obj.taste,
            convenience=domain_obj.convenience,
            comment=domain_obj.comment,
        )
        if rating_on_db and merge:
            logger.debug(
                "Merging existing rating",
                recipe_id=parent.id,
                user_id=domain_obj.user_id,
                taste_rating=domain_obj.taste,
                convenience_rating=domain_obj.convenience
            )
            return await session.merge(rating_on_entity)  # , rating_on_db)
        if rating_on_db:
            logger.debug(
                "Updating existing rating without merge",
                recipe_id=parent.id,
                user_id=domain_obj.user_id,
                taste_rating=domain_obj.taste,
                convenience_rating=domain_obj.convenience
            )
            rating_on_db.user_id = rating_on_entity.user_id
            rating_on_db.recipe_id = rating_on_entity.recipe_id
            rating_on_db.taste = rating_on_entity.taste
            rating_on_db.convenience = rating_on_entity.convenience
            rating_on_db.comment = rating_on_entity.comment
            return rating_on_db

        logger.debug(
            "Creating new rating",
            recipe_id=parent.id,
            user_id=domain_obj.user_id,
            taste_rating=domain_obj.taste,
            convenience_rating=domain_obj.convenience
        )
        return rating_on_entity

    @staticmethod
    def map_sa_to_domain(sa_obj: RatingSaModel) -> Rating:
        """Map SQLAlchemy rating model to domain object.

        Args:
            sa_obj: SQLAlchemy rating model to convert.

        Returns:
            Rating domain object.
        """
        return Rating(
            user_id=sa_obj.user_id,
            recipe_id=sa_obj.recipe_id,
            taste=sa_obj.taste,
            convenience=sa_obj.convenience,
            comment=sa_obj.comment,
        )
