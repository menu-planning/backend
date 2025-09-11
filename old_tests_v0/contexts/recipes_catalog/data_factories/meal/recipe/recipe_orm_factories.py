"""
Data factories for Recipe testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- UUID4 IDs for realistic testing scenarios
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different recipe types
- ORM equivalents for all domain factory methods
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of Recipe domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from old_tests_v0.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_ingredient_kwargs,
    create_rating_kwargs,
)

# Import check_missing_attributes for validation
from old_tests_v0.contexts.recipes_catalog.data_factories.shared_orm_factories import (
    create_recipe_tag_orm,
)
from old_tests_v0.utils.counter_manager import (
    get_next_ingredient_id,
    get_next_rating_id,
    get_next_recipe_id,
    reset_all_counters,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import (
    RatingSaModel,
)

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import (
    RecipeSaModel,
)
from src.contexts.shared_kernel.adapters.name_search import StrProcessor
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC BEHAVIOR
# =============================================================================

# Use centralized counter manager instead of local counters

# Pre-generated author and meal IDs for consistent relationships
_AUTHOR_IDS = [str(uuid.uuid4()) for _ in range(10)]
_MEAL_IDS = [str(uuid.uuid4()) for _ in range(20)]
_PRODUCT_IDS = [str(uuid.uuid4()) for _ in range(50)]


def get_deterministic_author_id(counter: int) -> str:
    """Get a deterministic author ID based on counter"""
    return _AUTHOR_IDS[counter % len(_AUTHOR_IDS)]


def get_deterministic_meal_id(counter: int) -> str:
    """Get a deterministic meal ID based on counter"""
    return _MEAL_IDS[counter % len(_MEAL_IDS)]


def get_deterministic_product_id(counter: int) -> str:
    """Get a deterministic product ID based on counter"""
    return _PRODUCT_IDS[counter % len(_PRODUCT_IDS)]


# =============================================================================
# RECIPE DATA FACTORIES (ORM)
# =============================================================================


def create_recipe_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create recipe ORM kwargs with deterministic values and UUID4 IDs.

    Similar to create_recipe_kwargs but includes ORM-specific fields like preprocessed_name
    and nutritional calculation fields. Uses UUID4 for all IDs while maintaining
    deterministic behavior for other attributes.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required ORM recipe creation parameters
    """

    # Get current counter value
    recipe_counter = get_next_recipe_id()

    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    final_kwargs = {
        "id": kwargs.get("id", str(uuid.uuid4())),
        "name": kwargs.get("name", f"Test Recipe {recipe_counter}"),
        "preprocessed_name": kwargs.get(
            "preprocessed_name", StrProcessor(f"Test Recipe {recipe_counter}").output
        ),
        "author_id": kwargs.get(
            "author_id", get_deterministic_author_id(recipe_counter)
        ),
        "meal_id": kwargs.get("meal_id", get_deterministic_meal_id(recipe_counter)),
        "instructions": kwargs.get(
            "instructions",
            f"Test instructions for recipe {recipe_counter}. Step 1: Prepare ingredients. Step 2: Cook thoroughly.",
        ),
        "total_time": kwargs.get(
            "total_time",
            (15 + (recipe_counter * 5)) if recipe_counter % 4 != 0 else None,
        ),
        "description": kwargs.get(
            "description",
            (
                f"Test recipe description {recipe_counter}"
                if recipe_counter % 3 != 0
                else None
            ),
        ),
        "utensils": kwargs.get(
            "utensils", f"pot, pan, spoon" if recipe_counter % 2 == 0 else None
        ),
        "notes": kwargs.get(
            "notes",
            (
                f"Test notes for recipe {recipe_counter}"
                if recipe_counter % 4 != 0
                else None
            ),
        ),
        "privacy": kwargs.get(
            "privacy",
            Privacy.PUBLIC.value if recipe_counter % 3 == 0 else Privacy.PRIVATE.value,
        ),  # String values for ORM
        "weight_in_grams": kwargs.get(
            "weight_in_grams",
            (200 + (recipe_counter * 50)) if recipe_counter % 3 != 0 else None,
        ),
        "calorie_density": kwargs.get(
            "calorie_density", 1.5 + (recipe_counter % 2)
        ),  # 1.5-3.5 cal/g
        "carbo_percentage": kwargs.get(
            "carbo_percentage", 40.0 + (recipe_counter % 20)
        ),  # 40-60%
        "protein_percentage": kwargs.get(
            "protein_percentage", 15.0 + (recipe_counter % 15)
        ),  # 15-30%
        "total_fat_percentage": kwargs.get(
            "total_fat_percentage", 20.0 + (recipe_counter % 20)
        ),  # 20-40%
        "image_url": kwargs.get(
            "image_url",
            (
                f"https://example.com/recipe_{recipe_counter}.jpg"
                if recipe_counter % 2 == 0
                else None
            ),
        ),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=recipe_counter)
        ),
        "updated_at": kwargs.get(
            "updated_at", base_time + timedelta(hours=recipe_counter, minutes=30)
        ),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "average_taste_rating": kwargs.get(
            "average_taste_rating", 3.5 + (recipe_counter % 2)
        ),  # ORM calculated field
        "average_convenience_rating": kwargs.get(
            "average_convenience_rating", 3.0 + (recipe_counter % 3)
        ),  # ORM calculated field
        "nutri_facts": kwargs.get(
            "nutri_facts"
        ),  # Will be created separately if needed
        "ingredients": kwargs.get(
            "ingredients", []
        ),  # Will be populated separately if needed
        "tags": kwargs.get("tags", []),  # List for ORM relationships
        "ratings": kwargs.get("ratings", []),  # List for ORM relationships
    }

    return final_kwargs


def create_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a RecipeSaModel ORM instance with deterministic data and UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance
    """
    recipe_kwargs = create_recipe_orm_kwargs(**kwargs)
    return RecipeSaModel(**recipe_kwargs)


# =============================================================================
# INGREDIENT DATA FACTORIES (ORM)
# =============================================================================


def create_ingredient_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create ingredient ORM kwargs with deterministic values and UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with ORM ingredient creation parameters
    """

    # Get current counter value
    ingredient_counter = get_next_ingredient_id()

    # Use the same logic as domain ingredients but adapt for ORM fields
    ingredient_kwargs = create_ingredient_kwargs(**kwargs)

    # ORM specific adaptations
    final_kwargs = {
        "name": kwargs.get("name", ingredient_kwargs["name"]),
        "unit": kwargs.get(
            "unit", ingredient_kwargs["unit"]
        ),  # Convert enum to string for ORM
        "quantity": kwargs.get("quantity", ingredient_kwargs["quantity"]),
        "position": kwargs.get("position", ingredient_kwargs["position"]),
        "full_text": kwargs.get("full_text", ingredient_kwargs["full_text"]),
        "product_id": kwargs.get(
            "product_id",
            ingredient_kwargs.get(
                "product_id", get_deterministic_product_id(ingredient_counter)
            ),
        ),
        "recipe_id": kwargs.get("recipe_id", str(uuid.uuid4())),
    }
    final_kwargs["preprocessed_name"] = kwargs.get(
        "preprocessed_name", StrProcessor(final_kwargs["name"]).output
    )

    return final_kwargs


def create_ingredient_orm(**kwargs) -> IngredientSaModel:
    """
    Create an IngredientSaModel ORM instance with deterministic data and UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        IngredientSaModel ORM instance
    """
    ingredient_kwargs = create_ingredient_orm_kwargs(**kwargs)
    return IngredientSaModel(**ingredient_kwargs)


# =============================================================================
# RATING DATA FACTORIES (ORM)
# =============================================================================


def create_rating_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create rating ORM kwargs with deterministic values and UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with ORM rating creation parameters
    """

    # Get current counter value
    rating_counter = get_next_rating_id()

    # Use the same logic as domain ratings
    rating_kwargs = create_rating_kwargs(**kwargs)

    # ORM specific adaptations - add created_at timestamp
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    final_kwargs = {
        "user_id": kwargs.get("user_id", str(uuid.uuid4())),
        "recipe_id": kwargs.get("recipe_id", str(uuid.uuid4())),
        "taste": kwargs.get("taste", rating_kwargs["taste"]),
        "convenience": kwargs.get("convenience", rating_kwargs["convenience"]),
        "comment": kwargs.get("comment", rating_kwargs["comment"]),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=rating_counter)
        ),
    }

    return final_kwargs


def create_rating_orm(**kwargs) -> RatingSaModel:
    """
    Create a RatingSaModel ORM instance with deterministic data and UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RatingSaModel ORM instance
    """
    rating_kwargs = create_rating_orm_kwargs(**kwargs)
    return RatingSaModel(**rating_kwargs)


# =============================================================================
# SPECIALIZED RECIPE FACTORIES (ORM)
# =============================================================================


def create_quick_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a quick-cooking recipe ORM instance (≤20 minutes) with UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance optimized for quick cooking
    """
    final_kwargs = {
        "name": kwargs.get("name", "Quick Recipe"),
        "total_time": kwargs.get("total_time", 15),
        "instructions": kwargs.get(
            "instructions", "Quick and easy instructions. Heat, mix, serve."
        ),
        "tags": kwargs.get(
            "tags",
            [
                create_recipe_tag_orm(
                    key="difficulty",
                    value="easy",
                    author_id=get_deterministic_author_id(1),
                    type="recipe",
                ),
                create_recipe_tag_orm(
                    key="cooking_method",
                    value="raw",
                    author_id=get_deterministic_author_id(1),
                    type="recipe",
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["name", "total_time", "instructions", "tags"]
        },
    }
    return create_recipe_orm(**final_kwargs)


def create_high_protein_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a high-protein recipe ORM instance (≥25g protein) with UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance optimized for high protein content
    """
    recipe_id = str(uuid.uuid4())
    final_kwargs = {
        "id": recipe_id,
        "name": kwargs.get("name", "High Protein Recipe"),
        "protein_percentage": kwargs.get(
            "protein_percentage", 35.0
        ),  # High protein percentage for ORM
        "ingredients": kwargs.get(
            "ingredients",
            [
                create_ingredient_orm(
                    name="Chicken Breast",
                    unit=MeasureUnit.GRAM.value,
                    quantity=200.0,
                    position=0,
                    product_id=get_deterministic_product_id(1),
                    recipe_id=recipe_id,
                ),
                create_ingredient_orm(
                    name="Greek Yogurt",
                    unit=MeasureUnit.GRAM.value,
                    quantity=100.0,
                    position=1,
                    product_id=get_deterministic_product_id(2),
                    recipe_id=recipe_id,
                ),
            ],
        ),
        "tags": kwargs.get(
            "tags",
            [
                create_recipe_tag_orm(
                    key="diet",
                    value="high-protein",
                    author_id=get_deterministic_author_id(1),
                    type="recipe",
                )
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["name", "protein_percentage", "ingredients", "tags"]
        },
    }
    return create_recipe_orm(**final_kwargs)


def create_vegetarian_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a vegetarian recipe ORM instance with UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance suitable for vegetarians
    """
    recipe_id = str(uuid.uuid4())
    final_kwargs = {
        "id": recipe_id,
        "name": kwargs.get("name", "Vegetarian Recipe"),
        "ingredients": kwargs.get(
            "ingredients",
            [
                create_ingredient_orm(
                    name="Vegetables",
                    unit=MeasureUnit.GRAM.value,
                    quantity=300.0,
                    position=0,
                    product_id=get_deterministic_product_id(3),
                    recipe_id=recipe_id,
                ),
                create_ingredient_orm(
                    name="Olive Oil",
                    unit=MeasureUnit.TABLESPOON.value,
                    quantity=2.0,
                    position=1,
                    product_id=get_deterministic_product_id(4),
                    recipe_id=recipe_id,
                ),
            ],
        ),
        "tags": kwargs.get(
            "tags",
            [
                create_recipe_tag_orm(
                    key="diet",
                    value="vegetarian",
                    author_id=get_deterministic_author_id(1),
                    type="recipe",
                )
            ],
        ),
        **{k: v for k, v in kwargs.items() if k not in ["name", "ingredients", "tags"]},
    }
    return create_recipe_orm(**final_kwargs)


def create_public_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a public recipe ORM instance for access control testing with UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance with public privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Public Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PUBLIC.value),  # String value for ORM
        "description": kwargs.get(
            "description", "This is a public recipe available to all users"
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["name", "privacy", "description"]
        },
    }
    return create_recipe_orm(**final_kwargs)


def create_private_recipe_orm(**kwargs) -> RecipeSaModel:
    """
    Create a private recipe ORM instance for access control testing with UUID4 IDs.

    Args:
        **kwargs: Override any default values

    Returns:
        RecipeSaModel ORM instance with private privacy
    """
    final_kwargs = {
        "name": kwargs.get("name", "Private Recipe"),
        "privacy": kwargs.get("privacy", Privacy.PRIVATE.value),  # String value for ORM
        "description": kwargs.get(
            "description", "This is a private recipe only visible to the author"
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["name", "privacy", "description"]
        },
    }
    return create_recipe_orm(**final_kwargs)


# =============================================================================
# DATASET CREATION UTILITIES (ORM)
# =============================================================================


def create_recipes_with_ratings_orm(
    count: int = 3, ratings_per_recipe: int = 2
) -> list[RecipeSaModel]:
    """
    Create a list of recipe ORM instances with ratings for aggregation testing using UUID4 IDs.

    Args:
        count: Number of recipes to create
        ratings_per_recipe: Number of ratings per recipe

    Returns:
        List of RecipeSaModel instances with ratings
    """
    recipes = []
    for i in range(count):
        recipe_id = str(uuid.uuid4())
        ratings = []
        for j in range(ratings_per_recipe):
            rating = create_rating_orm(
                recipe_id=recipe_id,
                user_id=str(uuid.uuid4()),
                taste=(3 + j) % 6,  # Vary ratings
                convenience=(4 + j) % 6,
            )
            ratings.append(rating)

        recipe = create_recipe_orm(
            id=recipe_id, name=f"Recipe with Ratings {i+1}", ratings=ratings
        )
        recipes.append(recipe)

    return recipes


def create_test_dataset_orm(
    recipe_count: int = 100, tags_per_recipe: int = 0
) -> dict[str, Any]:
    """
    Create a comprehensive test dataset with ORM instances for performance and integration testing using UUID4 IDs.

    Args:
        recipe_count: Number of recipes to create
        tags_per_recipe: Number of tags per recipe

    Returns:
        Dict containing ORM recipes, ingredients, ratings, and metadata
    """
    reset_all_counters()

    recipes = []
    all_ingredients = []
    all_ratings = []
    all_tags = []

    for i in range(recipe_count):
        # Create varied recipes
        if i % 4 == 0:
            recipe = create_quick_recipe_orm()
        elif i % 4 == 1:
            recipe = create_high_protein_recipe_orm()
        elif i % 4 == 2:
            recipe = create_vegetarian_recipe_orm()
        else:
            recipe = create_recipe_orm()

        # Add tags if requested
        if tags_per_recipe > 0:
            tags = []
            for j in range(tags_per_recipe):
                tag = create_recipe_tag_orm(type="recipe")
                tags.append(tag)
                all_tags.append(tag)
            recipe.tags = tags

        # Add ratings (some recipes have ratings, some don't)
        if i % 3 != 0:  # 2/3 of recipes have ratings
            ratings = []
            num_ratings = (i % 3) + 1  # 1-3 ratings per recipe
            for j in range(num_ratings):
                rating = create_rating_orm(recipe_id=recipe.id)
                ratings.append(rating)
                all_ratings.append(rating)
            recipe.ratings = ratings

        # Collect ingredients
        all_ingredients.extend(recipe.ingredients if recipe.ingredients else [])
        recipes.append(recipe)

    return {
        "recipes": recipes,
        "ingredients": all_ingredients,
        "ratings": all_ratings,
        "tags": all_tags,
        "metadata": {
            "recipe_count": len(recipes),
            "ingredient_count": len(all_ingredients),
            "rating_count": len(all_ratings),
            "tag_count": len(all_tags),
            "tags_per_recipe": tags_per_recipe,
        },
    }
