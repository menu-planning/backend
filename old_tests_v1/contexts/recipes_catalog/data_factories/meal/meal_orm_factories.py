"""
Data factories for MealRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different meal types
- ORM equivalents for all domain factory methods
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of Meal domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import (
    MealSaModel,
)
from src.contexts.shared_kernel.adapters.name_search import StrProcessor
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.data_factories.shared_orm_factories import (
    create_meal_tag_orm,
)
from tests.utils.counter_manager import get_next_meal_id
from tests.utils.utils import check_missing_attributes

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_MEALS = [
    {
        "name": "Italian Date Night Dinner",
        "description": "Romantic three-course Italian meal perfect for special occasions. Features classic carbonara with wine pairing suggestions.",
        "notes": "Perfect for romantic evenings, pairs well with Pinot Grigio or Chianti. Allow 2 hours for full preparation and dining experience.",
        "tags": ["dinner", "italian", "romantic", "date-night", "pasta"],
        "total_time": 90,
        "like": True,
        "calorie_density": 380.0,
        "carbo_percentage": 45.0,
        "protein_percentage": 25.0,
        "total_fat_percentage": 30.0,
        "weight_in_grams": 650,
    },
    {
        "name": "Quick Healthy Lunch Bowl",
        "description": "Light, nutritious meal packed with vegetables, quinoa, and Mediterranean flavors. Perfect for meal prep and busy weekdays.",
        "notes": "Great for meal prep - can be prepared in advance and stored for up to 3 days. Customize with your favorite seasonal vegetables.",
        "tags": [
            "lunch",
            "mediterranean",
            "vegetarian",
            "healthy",
            "meal-prep",
            "quick",
        ],
        "total_time": 25,
        "like": True,
        "calorie_density": 280.0,
        "carbo_percentage": 55.0,
        "protein_percentage": 20.0,
        "total_fat_percentage": 25.0,
        "weight_in_grams": 450,
    },
    {
        "name": "Comfort Food Evening",
        "description": "Hearty, satisfying meal perfect for cold evenings. Classic comfort food with rich, creamy flavors.",
        "notes": "Ultimate comfort food for chilly days. Serve with warm bread and a side salad to balance the richness.",
        "tags": ["dinner", "comfort-food", "american", "hearty", "winter"],
        "total_time": 75,
        "like": True,
        "calorie_density": 420.0,
        "carbo_percentage": 40.0,
        "protein_percentage": 30.0,
        "total_fat_percentage": 30.0,
        "weight_in_grams": 750,
    },
    {
        "name": "Asian Fusion Feast",
        "description": "Spicy and aromatic Asian-inspired meal with balanced flavors and fresh ingredients. Great for adventurous eaters.",
        "notes": "Adjust spice levels to taste. Fresh herbs and vegetables are key to authentic flavors. Best served immediately while hot.",
        "tags": ["dinner", "asian", "spicy", "healthy", "fusion"],
        "total_time": 45,
        "like": True,
        "calorie_density": 320.0,
        "carbo_percentage": 50.0,
        "protein_percentage": 28.0,
        "total_fat_percentage": 22.0,
        "weight_in_grams": 550,
    },
    {
        "name": "Light Summer Meal",
        "description": "Fresh, seasonal meal with crisp vegetables and light proteins. Perfect for warm weather dining.",
        "notes": "Best with fresh, seasonal ingredients. Can be served cold as a refreshing summer option.",
        "tags": ["lunch", "summer", "light", "fresh", "seasonal"],
        "total_time": 20,
        "like": True,
        "calorie_density": 220.0,
        "carbo_percentage": 60.0,
        "protein_percentage": 20.0,
        "total_fat_percentage": 20.0,
        "weight_in_grams": 400,
    },
]

# =============================================================================
# MEAL DATA FACTORIES (ORM)
# =============================================================================


def create_meal_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create meal ORM kwargs with deterministic values.

    Similar to create_meal_kwargs but includes ORM-specific fields like preprocessed_name
    and nutritional calculation fields.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required ORM meal creation parameters
    """
    meal_counter = get_next_meal_id()

    # Get the meal's author_id early so we can use it consistently
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    # Get realistic test data for deterministic values
    realistic_meal = REALISTIC_MEALS[(meal_counter - 1) % len(REALISTIC_MEALS)]

    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Default nutritional values (all fields from NutriFactsSaModel)
    default_nutri_facts = {
        "calories": kwargs.get("calories", 350.0 + (meal_counter * 25)),
        "protein": kwargs.get("protein", 20.0 + (meal_counter * 2)),
        "carbohydrate": kwargs.get("carbohydrate", 45.0 + (meal_counter * 3)),
        "total_fat": kwargs.get("total_fat", 15.0 + (meal_counter * 1)),
        "saturated_fat": kwargs.get("saturated_fat", 5.0 + (meal_counter * 0.5)),
        "trans_fat": kwargs.get("trans_fat", 0.0),
        "dietary_fiber": kwargs.get("dietary_fiber", 8.0 + (meal_counter * 0.5)),
        "sodium": kwargs.get("sodium", 650.0 + (meal_counter * 25)),
        "arachidonic_acid": kwargs.get("arachidonic_acid"),
        "ashes": kwargs.get("ashes"),
        "dha": kwargs.get("dha"),
        "epa": kwargs.get("epa"),
        "sugar": kwargs.get("sugar", 12.0 + (meal_counter * 1)),
        "starch": kwargs.get("starch"),
        "biotin": kwargs.get("biotin"),
        "boro": kwargs.get("boro"),
        "caffeine": kwargs.get("caffeine"),
        "calcium": kwargs.get("calcium", 150.0 + (meal_counter * 10)),
        "chlorine": kwargs.get("chlorine"),
        "copper": kwargs.get("copper"),
        "cholesterol": kwargs.get("cholesterol"),
        "choline": kwargs.get("choline"),
        "chrome": kwargs.get("chrome"),
        "dextrose": kwargs.get("dextrose"),
        "sulfur": kwargs.get("sulfur"),
        "phenylalanine": kwargs.get("phenylalanine"),
        "iron": kwargs.get("iron", 8.0 + (meal_counter * 0.5)),
        "insoluble_fiber": kwargs.get("insoluble_fiber"),
        "soluble_fiber": kwargs.get("soluble_fiber"),
        "fluor": kwargs.get("fluor"),
        "phosphorus": kwargs.get("phosphorus"),
        "fructo_oligosaccharides": kwargs.get("fructo_oligosaccharides"),
        "fructose": kwargs.get("fructose"),
        "galacto_oligosaccharides": kwargs.get("galacto_oligosaccharides"),
        "galactose": kwargs.get("galactose"),
        "glucose": kwargs.get("glucose"),
        "glucoronolactone": kwargs.get("glucoronolactone"),
        "monounsaturated_fat": kwargs.get("monounsaturated_fat"),
        "polyunsaturated_fat": kwargs.get("polyunsaturated_fat"),
        "guarana": kwargs.get("guarana"),
        "inositol": kwargs.get("inositol"),
        "inulin": kwargs.get("inulin"),
        "iodine": kwargs.get("iodine"),
        "l_carnitine": kwargs.get("l_carnitine"),
        "l_methionine": kwargs.get("l_methionine"),
        "lactose": kwargs.get("lactose"),
        "magnesium": kwargs.get("magnesium"),
        "maltose": kwargs.get("maltose"),
        "manganese": kwargs.get("manganese"),
        "molybdenum": kwargs.get("molybdenum"),
        "linolenic_acid": kwargs.get("linolenic_acid"),
        "linoleic_acid": kwargs.get("linoleic_acid"),
        "omega_7": kwargs.get("omega_7"),
        "omega_9": kwargs.get("omega_9"),
        "oleic_acid": kwargs.get("oleic_acid"),
        "other_carbo": kwargs.get("other_carbo"),
        "polydextrose": kwargs.get("polydextrose"),
        "polyols": kwargs.get("polyols"),
        "potassium": kwargs.get("potassium"),
        "sacarose": kwargs.get("sacarose"),
        "selenium": kwargs.get("selenium"),
        "silicon": kwargs.get("silicon"),
        "sorbitol": kwargs.get("sorbitol"),
        "sucralose": kwargs.get("sucralose"),
        "taurine": kwargs.get("taurine"),
        "vitamin_a": kwargs.get("vitamin_a", 750.0 + (meal_counter * 25)),
        "vitamin_b1": kwargs.get("vitamin_b1"),
        "vitamin_b2": kwargs.get("vitamin_b2"),
        "vitamin_b3": kwargs.get("vitamin_b3"),
        "vitamin_b5": kwargs.get("vitamin_b5"),
        "vitamin_b6": kwargs.get("vitamin_b6"),
        "folic_acid": kwargs.get("folic_acid"),
        "vitamin_b12": kwargs.get("vitamin_b12"),
        "vitamin_c": kwargs.get("vitamin_c", 60.0 + (meal_counter * 5)),
        "vitamin_d": kwargs.get("vitamin_d"),
        "vitamin_e": kwargs.get("vitamin_e"),
        "vitamin_k": kwargs.get("vitamin_k"),
        "zinc": kwargs.get("zinc"),
        "retinol": kwargs.get("retinol"),
        "thiamine": kwargs.get("thiamine"),
        "riboflavin": kwargs.get("riboflavin"),
        "pyridoxine": kwargs.get("pyridoxine"),
        "niacin": kwargs.get("niacin"),
        # Additional calculated fields that might be expected by ORM
        "metadata": kwargs.get("metadata"),
        "registry": kwargs.get("registry"),
        "type_annotation_map": kwargs.get("type_annotation_map"),
    }

    final_kwargs = {
        "id": kwargs.get("id", str(uuid.uuid4())),
        "name": kwargs.get("name", realistic_meal["name"]),
        "preprocessed_name": kwargs.get(
            "preprocessed_name", StrProcessor(realistic_meal["name"]).output
        ),
        "description": kwargs.get("description", realistic_meal.get("description")),
        "author_id": meal_author_id,
        "menu_id": kwargs.get("menu_id"),
        "notes": kwargs.get("notes", realistic_meal.get("notes")),
        "total_time": kwargs.get(
            "total_time", realistic_meal.get("total_time", 30 + (meal_counter * 5))
        ),
        "like": kwargs.get("like", meal_counter % 3 == 0),
        "weight_in_grams": kwargs.get(
            "weight_in_grams",
            realistic_meal.get("weight_in_grams", 400 + (meal_counter * 50)),
        ),
        "calorie_density": kwargs.get(
            "calorie_density",
            realistic_meal.get("calorie_density", 1.5 + (meal_counter % 2)),
        ),
        "carbo_percentage": kwargs.get(
            "carbo_percentage",
            realistic_meal.get("carbo_percentage", 45.0 + (meal_counter % 15)),
        ),
        "protein_percentage": kwargs.get(
            "protein_percentage",
            realistic_meal.get("protein_percentage", 20.0 + (meal_counter % 10)),
        ),
        "total_fat_percentage": kwargs.get(
            "total_fat_percentage",
            realistic_meal.get("total_fat_percentage", 25.0 + (meal_counter % 15)),
        ),
        "image_url": kwargs.get(
            "image_url",
            (
                f"https://example.com/meal_{meal_counter}.jpg"
                if meal_counter % 2 == 0
                else None
            ),
        ),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=meal_counter)
        ),
        "updated_at": kwargs.get(
            "updated_at", base_time + timedelta(hours=meal_counter, minutes=30)
        ),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get("tags", []),
        # Add nutri_facts composite field (required by MealSaModel even though we have individual fields)
        "nutri_facts": kwargs.get(
            "nutri_facts"
        ),  # Will be created as composite from individual fields
    }

    # Add all nutritional fields
    final_kwargs.update(default_nutri_facts)

    # Allow override of any attribute except author_id (to maintain consistency with tags)
    final_kwargs.update({k: v for k, v in kwargs.items() if k != "author_id"})

    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(MealSaModel, final_kwargs)
    assert not missing, f"Missing attributes for MealSaModel: {missing}"

    return final_kwargs


def create_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a MealSaModel ORM instance with deterministic data and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel ORM instance with comprehensive validation
    """
    meal_kwargs = create_meal_orm_kwargs(**kwargs)
    return MealSaModel(**meal_kwargs)


def create_meals_with_tags_orm(
    count: int = 3, tags_per_meal: int = 2
) -> list[MealSaModel]:
    """Create multiple ORM meals with various tag combinations for testing"""
    meals = []

    # Create a pool of unique tags first to avoid constraint violations
    unique_tags = {}  # Key: (key, value, author_id, type), Value: TagSaModel

    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"],
    }

    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx

                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]

                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]

                # Use UUID for author_id instead of deterministic pattern
                author_id = str(uuid.uuid4())

                type_idx = (
                    total_tag_index
                    // (len(keys) * max(len(v) for v in values_by_key.values()))
                ) % len(tag_types)
                tag_type = tag_types[type_idx]

                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)

                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag_orm(
                        key=key, value=value, author_id=author_id, type=tag_type
                    )
                    unique_tags[tag_key] = tag

    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())

    for i in range(count):
        # Create tags for this meal
        tags = []
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])

        meal_kwargs = create_meal_orm_kwargs()
        meal_kwargs["tags"] = tags
        meal = create_meal_orm(**meal_kwargs)
        meals.append(meal)
    return meals


def create_test_meal_dataset_orm(
    meal_count: int = 100, tags_per_meal: int = 0
) -> dict[str, Any]:
    """Create a dataset of ORM meals for performance testing"""
    meals = []
    all_tags = []

    # Create a pool of unique tags first to avoid constraint violations
    unique_tags = {}  # Key: (key, value, author_id, type), Value: TagSaModel

    # Calculate maximum possible unique tags
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"],
    }

    # Pre-create unique tags if we need them
    if tags_per_meal > 0:
        # Create unique tag combinations as needed
        for meal_idx in range(meal_count):
            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx

                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]

                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]

                # Use UUID for author_id instead of deterministic pattern
                author_id = str(uuid.uuid4())

                type_idx = (
                    total_tag_index
                    // (len(keys) * max(len(v) for v in values_by_key.values()))
                ) % len(tag_types)
                tag_type = tag_types[type_idx]

                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)

                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag_orm(
                        key=key, value=value, author_id=author_id, type=tag_type
                    )
                    unique_tags[tag_key] = tag
                    all_tags.append(tag)

    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())

    for i in range(meal_count):
        # Create tags for this meal if requested
        tags = []
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])

        meal_kwargs = create_meal_orm_kwargs()
        if tags:
            meal_kwargs["tags"] = tags
        meal = create_meal_orm(**meal_kwargs)
        meals.append(meal)

    return {"meals": meals, "all_tags": all_tags}


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (ORM)
# =============================================================================


def create_low_calorie_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with low calorie characteristics and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel with low calorie density and appropriate tags
    """
    # Get the meal's author_id early so we can use it for tags
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    final_kwargs = {
        "author_id": meal_author_id,
        "name": kwargs.get("name", "Light Mediterranean Bowl"),
        "description": kwargs.get(
            "description",
            "A nutritious, low-calorie meal packed with fresh vegetables and lean proteins",
        ),
        "notes": kwargs.get(
            "notes",
            "Perfect for weight management goals. Rich in fiber and nutrients while being calorie-conscious.",
        ),
        "calorie_density": kwargs.get("calorie_density", 180.0),  # Low calorie density
        "carbo_percentage": kwargs.get("carbo_percentage", 60.0),
        "protein_percentage": kwargs.get("protein_percentage", 25.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 15.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 350),
        "total_time": kwargs.get("total_time", 20),
        "like": kwargs.get("like", True),
        "tags": kwargs.get(
            "tags",
            [
                create_meal_tag_orm(
                    key="diet",
                    value="low-calorie",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="category",
                    value="health",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="style", value="healthy", type="meal", author_id=meal_author_id
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "description",
                "notes",
                "calorie_density",
                "carbo_percentage",
                "protein_percentage",
                "total_fat_percentage",
                "weight_in_grams",
                "total_time",
                "like",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal_orm(**final_kwargs)


def create_quick_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with quick preparation time and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel with short total_time and appropriate tags
    """
    # Get the meal's author_id early so we can use it for tags
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    final_kwargs = {
        "author_id": meal_author_id,
        "name": kwargs.get("name", "15-Minute Power Bowl"),
        "description": kwargs.get(
            "description",
            "Fast preparation meal for busy schedules with maximum nutrition",
        ),
        "notes": kwargs.get(
            "notes",
            "Perfect for weeknight dinners or quick lunches. Pre-prep ingredients on weekends for even faster assembly.",
        ),
        "total_time": kwargs.get("total_time", 15),  # Quick preparation
        "calorie_density": kwargs.get("calorie_density", 300.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 400),
        "like": kwargs.get("like", True),
        "tags": kwargs.get(
            "tags",
            [
                create_meal_tag_orm(
                    key="difficulty",
                    value="easy",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="occasion", value="quick", type="meal", author_id=meal_author_id
                ),
                create_meal_tag_orm(
                    key="style", value="healthy", type="meal", author_id=meal_author_id
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "description",
                "notes",
                "total_time",
                "calorie_density",
                "weight_in_grams",
                "like",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal_orm(**final_kwargs)


def create_vegetarian_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a vegetarian meal ORM instance with appropriate tags and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel with vegetarian tags and characteristics
    """
    # Get the meal's author_id early so we can use it for tags
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    final_kwargs = {
        "author_id": meal_author_id,
        "name": kwargs.get("name", "Garden Harvest Feast"),
        "description": kwargs.get(
            "description",
            "Plant-based nutritious meal celebrating seasonal vegetables and grains",
        ),
        "notes": kwargs.get(
            "notes",
            "Bursting with fresh flavors and plant-based proteins. Easily adaptable to vegan by omitting dairy.",
        ),
        "calorie_density": kwargs.get("calorie_density", 250.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 55.0),
        "protein_percentage": kwargs.get("protein_percentage", 20.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 25.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 500),
        "total_time": kwargs.get("total_time", 35),
        "like": kwargs.get("like", True),
        "tags": kwargs.get(
            "tags",
            [
                create_meal_tag_orm(
                    key="diet",
                    value="vegetarian",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="style", value="healthy", type="meal", author_id=meal_author_id
                ),
                create_meal_tag_orm(
                    key="category", value="lunch", type="meal", author_id=meal_author_id
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "description",
                "notes",
                "calorie_density",
                "carbo_percentage",
                "protein_percentage",
                "total_fat_percentage",
                "weight_in_grams",
                "total_time",
                "like",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal_orm(**final_kwargs)


def create_high_protein_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance with high protein content and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel with high protein characteristics and tags
    """
    # Get the meal's author_id early so we can use it for tags
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    final_kwargs = {
        "author_id": meal_author_id,
        "name": kwargs.get("name", "Athlete's Power Plate"),
        "description": kwargs.get(
            "description", "High-protein meal designed for muscle building and recovery"
        ),
        "notes": kwargs.get(
            "notes",
            "Ideal post-workout meal with complete amino acid profile. Great for fitness enthusiasts and athletes.",
        ),
        "calorie_density": kwargs.get("calorie_density", 350.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 35.0),
        "protein_percentage": kwargs.get("protein_percentage", 40.0),  # High protein
        "total_fat_percentage": kwargs.get("total_fat_percentage", 25.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 600),
        "total_time": kwargs.get("total_time", 45),
        "like": kwargs.get("like", True),
        "tags": kwargs.get(
            "tags",
            [
                create_meal_tag_orm(
                    key="diet",
                    value="high-protein",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="style", value="fitness", type="meal", author_id=meal_author_id
                ),
                create_meal_tag_orm(
                    key="occasion",
                    value="post-workout",
                    type="meal",
                    author_id=meal_author_id,
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "description",
                "notes",
                "calorie_density",
                "carbo_percentage",
                "protein_percentage",
                "total_fat_percentage",
                "weight_in_grams",
                "total_time",
                "like",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal_orm(**final_kwargs)


def create_family_meal_orm(**kwargs) -> MealSaModel:
    """
    Create a meal ORM instance suitable for families with validation.

    Args:
        **kwargs: Override any default values

    Returns:
        MealSaModel with family-friendly characteristics
    """
    # Get the meal's author_id early so we can use it for tags
    meal_author_id = kwargs.get("author_id", str(uuid.uuid4()))

    final_kwargs = {
        "author_id": meal_author_id,
        "name": kwargs.get("name", "Sunday Family Dinner"),
        "description": kwargs.get(
            "description",
            "Hearty, comforting meal perfect for bringing the whole family together",
        ),
        "notes": kwargs.get(
            "notes",
            "Kid-friendly flavors with hidden vegetables. Makes great leftovers for the next day's lunch.",
        ),
        "calorie_density": kwargs.get("calorie_density", 320.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 45.0),
        "protein_percentage": kwargs.get("protein_percentage", 25.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 30.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 700),
        "total_time": kwargs.get("total_time", 60),
        "like": kwargs.get("like", True),  # Families usually like their regular meals
        "tags": kwargs.get(
            "tags",
            [
                create_meal_tag_orm(
                    key="occasion",
                    value="family",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="difficulty",
                    value="medium",
                    type="meal",
                    author_id=meal_author_id,
                ),
                create_meal_tag_orm(
                    key="category",
                    value="dinner",
                    type="meal",
                    author_id=meal_author_id,
                ),
            ],
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "name",
                "description",
                "notes",
                "calorie_density",
                "carbo_percentage",
                "protein_percentage",
                "total_fat_percentage",
                "weight_in_grams",
                "total_time",
                "like",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal_orm(**final_kwargs)
