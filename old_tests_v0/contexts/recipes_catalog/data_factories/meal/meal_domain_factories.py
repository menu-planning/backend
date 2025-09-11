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
- Nested recipe integration with proper ID relationships
- Invalid computed properties testing for robust validation

All data follows the exact structure of Meal domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Import recipe factories for nested recipe creation
from old_tests_v0.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_complex_recipe,
    create_dessert_recipe,
    create_minimal_recipe,
    create_quick_recipe,
    create_recipe,
    create_simple_recipe,
)

# Import check_missing_attributes for validation
from old_tests_v0.contexts.recipes_catalog.data_factories.shared_domain_factories import (
    create_meal_tag,
)

# Import counter manager for centralized counter management
from old_tests_v0.utils.counter_manager import get_next_meal_id, reset_all_counters
from old_tests_v0.utils.utils import check_missing_attributes
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_MEALS = [
    {
        "name": "Italian Date Night Dinner",
        "description": "Romantic three-course Italian meal perfect for special occasions. Features classic carbonara with wine pairing suggestions.",
        "notes": "Perfect for romantic evenings, pairs well with Pinot Grigio or Chianti. Allow 2 hours for full preparation and dining experience.",
        "tags": ["dinner", "italian", "romantic", "date-night", "pasta"],
        "like": True,
        "recipe_count": 3,  # Appetizer, main course, dessert
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
        "like": True,
        "recipe_count": 2,  # Main bowl, dressing
    },
    {
        "name": "Comfort Food Evening",
        "description": "Hearty, satisfying meal perfect for cold evenings. Classic comfort food with rich, creamy flavors.",
        "notes": "Ultimate comfort food for chilly days. Serve with warm bread and a side salad to balance the richness.",
        "tags": ["dinner", "comfort-food", "american", "hearty", "winter"],
        "like": True,
        "recipe_count": 2,  # Main dish, side
    },
    {
        "name": "Asian Fusion Feast",
        "description": "Spicy and aromatic Asian-inspired meal with balanced flavors and fresh ingredients. Great for adventurous eaters.",
        "notes": "Adjust spice levels to taste. Fresh herbs and vegetables are key to authentic flavors. Best served immediately while hot.",
        "tags": ["dinner", "asian", "spicy", "healthy", "fusion"],
        "like": True,
        "recipe_count": 4,  # Appetizer, main, side, sauce
    },
    {
        "name": "Light Summer Meal",
        "description": "Fresh, seasonal meal with crisp vegetables and light proteins. Perfect for warm weather dining.",
        "notes": "Best with fresh, seasonal ingredients. Can be served cold as a refreshing summer option.",
        "tags": ["lunch", "summer", "light", "fresh", "seasonal"],
        "like": True,
        "recipe_count": 2,  # Salad, protein
    },
    {
        "name": "Breakfast Power Start",
        "description": "Energizing breakfast with protein, healthy fats, and complex carbs. Perfect for starting busy days.",
        "notes": "Can be prepared the night before. Add fresh fruit just before serving for extra nutrition.",
        "tags": ["breakfast", "protein", "healthy", "quick", "energy"],
        "like": True,
        "recipe_count": 3,  # Main dish, side, beverage
    },
    {
        "name": "Festive Holiday Feast",
        "description": "Special occasion meal with traditional flavors and elegant presentation. Perfect for celebrations.",
        "notes": "Plan ahead for special occasions. Requires advance preparation but results in memorable dining experience.",
        "tags": ["dinner", "festive", "holiday", "special", "traditional"],
        "like": True,
        "recipe_count": 5,  # Multiple courses
    },
    {
        "name": "Plant-Based Power Bowl",
        "description": "Nutrient-dense vegan meal with legumes, grains, and fresh vegetables. Satisfying and wholesome.",
        "notes": "Excellent source of plant-based protein and fiber. Customize with seasonal vegetables and favorite dressings.",
        "tags": ["lunch", "vegan", "plant-based", "healthy", "protein"],
        "like": True,
        "recipe_count": 3,  # Bowl, dressing, topping
    },
    {
        "name": "Mediterranean Tapas Night",
        "description": "Collection of small Mediterranean dishes perfect for sharing. Light, flavorful, and social.",
        "notes": "Great for entertaining. Prepare dishes in advance and serve at room temperature or slightly warm.",
        "tags": ["dinner", "mediterranean", "tapas", "social", "light"],
        "like": True,
        "recipe_count": 6,  # Multiple small dishes
    },
    {
        "name": "Keto-Friendly Indulgence",
        "description": "High-fat, low-carb meal that doesn't compromise on flavor. Perfect for ketogenic diet followers.",
        "notes": "Focus on healthy fats and quality proteins. Track macros carefully to maintain ketosis.",
        "tags": ["dinner", "keto", "low-carb", "high-fat", "protein"],
        "like": True,
        "recipe_count": 2,  # Main dish, side
    },
]

# Constants for comprehensive testing
COMMON_MEAL_TYPES = [
    "breakfast",
    "brunch",
    "lunch",
    "dinner",
    "snack",
    "dessert",
    "appetizer",
    "side_dish",
    "main_course",
    "light_meal",
    "heavy_meal",
]

CUISINE_TYPES = [
    "italian",
    "french",
    "chinese",
    "japanese",
    "thai",
    "indian",
    "mexican",
    "american",
    "mediterranean",
    "middle_eastern",
    "korean",
    "vietnamese",
    "greek",
    "spanish",
    "german",
    "brazilian",
    "moroccan",
    "british",
    "modern",
    "fusion",
    "traditional",
    "contemporary",
]

DIETARY_TAGS = [
    "vegetarian",
    "vegan",
    "gluten-free",
    "dairy-free",
    "low-carb",
    "keto",
    "paleo",
    "pescatarian",
    "healthy",
    "light",
    "hearty",
    "comfort-food",
    "low-calorie",
    "high-protein",
    "plant-based",
    "organic",
    "whole-food",
    "raw",
    "sugar-free",
    "low-sodium",
]

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

OCCASION_TYPES = [
    "everyday",
    "quick",
    "family",
    "date-night",
    "entertaining",
    "holiday",
    "special",
    "casual",
    "formal",
    "outdoor",
    "picnic",
    "party",
    "romantic",
    "festive",
    "comfort",
    "seasonal",
    "summer",
    "winter",
    "spring",
    "fall",
]

MEAL_STYLES = [
    "healthy",
    "comfort",
    "elegant",
    "rustic",
    "modern",
    "traditional",
    "fusion",
    "simple",
    "complex",
    "gourmet",
    "casual",
    "fine-dining",
    "homestyle",
    "restaurant-style",
    "fresh",
    "hearty",
    "light",
]

# =============================================================================
# DETERMINISTIC VALUE GENERATORS
# =============================================================================


def generate_meal_like_value(counter: int | None = None) -> bool:
    """
    Generate deterministic like values for meals based on counter.

    Args:
        counter: Counter value to use for variation (defaults to current meal counter)

    Returns:
        Boolean like value
    """
    if counter is None:
        counter = (
            get_next_meal_id() - 1
        )  # Get current counter value without incrementing

    # Create pattern: mostly liked (75% chance)
    return counter % 4 != 0


# =============================================================================
# RECIPE CREATION WITH PROPER RELATIONSHIPS
# =============================================================================


def create_recipe_for_meal(
    meal_id: str, author_id: str, recipe_type: str = "main", **kwargs
) -> Any:
    """
    Create a recipe with proper meal_id and author_id relationships.

    Args:
        meal_id: ID of the meal this recipe belongs to
        author_id: ID of the author (should match meal's author_id)
        recipe_type: Type of recipe (appetizer, main, dessert, side, etc.)
        **kwargs: Additional recipe parameters

    Returns:
        Recipe domain entity with proper relationships
    """
    # Create recipe with proper relationships
    recipe_kwargs = {"meal_id": meal_id, "author_id": author_id, **kwargs}

    # Choose appropriate recipe factory based on type
    if recipe_type == "appetizer":
        recipe_kwargs.setdefault("name", f"Appetizer Recipe for Meal {meal_id[-8:]}")
        recipe_kwargs.setdefault("description", "Light starter to begin the meal")
        return create_quick_recipe(**recipe_kwargs)
    elif recipe_type == "main":
        recipe_kwargs.setdefault("name", f"Main Course Recipe for Meal {meal_id[-8:]}")
        recipe_kwargs.setdefault("description", "Hearty main course as the centerpiece")
        return create_complex_recipe(**recipe_kwargs)
    elif recipe_type == "dessert":
        recipe_kwargs.setdefault("name", f"Dessert Recipe for Meal {meal_id[-8:]}")
        recipe_kwargs.setdefault("description", "Sweet finale to the meal")
        return create_dessert_recipe(**recipe_kwargs)
    elif recipe_type == "side":
        recipe_kwargs.setdefault("name", f"Side Recipe for Meal {meal_id[-8:]}")
        recipe_kwargs.setdefault("description", "Complementary side dish")
        return create_simple_recipe(**recipe_kwargs)
    elif recipe_type == "sauce":
        recipe_kwargs.setdefault("name", f"Sauce Recipe for Meal {meal_id[-8:]}")
        recipe_kwargs.setdefault("description", "Flavorful sauce to enhance the meal")
        return create_minimal_recipe(**recipe_kwargs)
    else:
        # Default to creating a simple recipe
        recipe_kwargs.setdefault(
            "name", f"{recipe_type.title()} Recipe for Meal {meal_id[-8:]}"
        )
        return create_recipe(**recipe_kwargs)


def create_multiple_recipes_for_meal(
    meal_id: str, author_id: str, recipe_count: int = 3, **kwargs
) -> list[Any]:
    """
    Create multiple recipes for a meal with proper relationships.

    Args:
        meal_id: ID of the meal these recipes belong to
        author_id: ID of the author (should match meal's author_id)
        recipe_count: Number of recipes to create
        **kwargs: Additional parameters for recipe creation

    Returns:
        List of Recipe domain entities with proper relationships
    """
    recipes = []
    recipe_types = ["appetizer", "main", "dessert", "side", "sauce", "beverage"]

    for i in range(recipe_count):
        recipe_type = recipe_types[i % len(recipe_types)]
        recipe = create_recipe_for_meal(
            meal_id=meal_id, author_id=author_id, recipe_type=recipe_type, **kwargs
        )
        recipes.append(recipe)

    return recipes


def create_recipes_with_invalid_computed_properties(
    meal_id: str, author_id: str, count: int = 2
) -> list[Any]:
    """
    Create recipes with invalid computed properties for testing correction.

    Args:
        meal_id: ID of the meal these recipes belong to
        author_id: ID of the author
        count: Number of recipes to create

    Returns:
        List of Recipe domain entities with invalid computed properties
    """
    recipes = []
    for i in range(count):
        # Create recipe with specific ratings but don't rely on computed averages
        recipe = create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="main" if i % 2 == 0 else "side",
            name=f"Recipe with Invalid Computed Properties {i+1}",
        )
        recipes.append(recipe)

    return recipes


# =============================================================================
# MEAL COMPUTED PROPERTIES TESTING
# =============================================================================


def create_meal_with_computed_property_issues(**kwargs) -> Meal:
    """
    Create a meal with recipes that might cause computed property issues.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with potential computed property issues
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create recipes with varying properties that affect meal computations
    recipes = [
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="main",
            name="Recipe with No Ratings",
            ratings=[],  # No ratings for average calculations
        ),
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="side",
            name="Recipe with No Nutrition",
            nutri_facts=None,  # No nutrition for aggregations
        ),
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="dessert",
            name="Recipe with No Time",
            total_time=None,  # No time for total calculations
        ),
    ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Meal with Computed Property Issues"),
        "description": kwargs.get(
            "description", "Meal for testing computed property edge cases"
        ),
        "notes": kwargs.get(
            "notes",
            "This meal has recipes with missing data that affects computed properties",
        ),
        "recipes": kwargs.get("recipes", recipes),
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="test", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="purpose",
                    value="computed-properties",
                    author_id=author_id,
                    type="meal",
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "author_id",
                "name",
                "description",
                "notes",
                "recipes",
                "tags",
            ]
        },
    }

    return create_meal(**final_kwargs)


def create_meal_with_aggregation_edge_cases(**kwargs) -> Meal:
    """
    Create a meal with recipes that test aggregation edge cases.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with aggregation edge cases
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create recipes with extreme values for aggregation testing
    recipes = [
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="main",
            name="Recipe with Extreme Values",
            total_time=300,  # Very high time
            weight_in_grams=2000,  # Very high weight
        ),
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="side",
            name="Recipe with Minimal Values",
            total_time=1,  # Very low time
            weight_in_grams=10,  # Very low weight
        ),
        create_recipe_for_meal(
            meal_id=meal_id,
            author_id=author_id,
            recipe_type="dessert",
            name="Recipe with Zero Values",
            total_time=0,  # Zero time
            weight_in_grams=0,  # Zero weight
        ),
    ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Meal with Aggregation Edge Cases"),
        "description": kwargs.get(
            "description", "Meal for testing aggregation edge cases and extreme values"
        ),
        "notes": kwargs.get(
            "notes",
            "This meal has recipes with extreme values to test aggregation logic",
        ),
        "recipes": kwargs.get("recipes", recipes),
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="test", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="purpose", value="aggregation", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "author_id",
                "name",
                "description",
                "notes",
                "recipes",
                "tags",
            ]
        },
    }

    return create_meal(**final_kwargs)


def create_meal_without_recipes(**kwargs) -> Meal:
    """
    Create a meal without any recipes for testing edge cases.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with no recipes
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    final_kwargs = {
        "author_id": author_id,
        "name": kwargs.get("name", "Meal Without Recipes"),
        "description": kwargs.get(
            "description", "Meal for testing scenarios without recipes"
        ),
        "notes": kwargs.get("notes", "This meal has no recipes for testing edge cases"),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="test", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="purpose", value="no-recipes", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k not in ["author_id", "name", "description", "notes", "recipes", "tags"]
        },
    }

    return create_meal(**final_kwargs)


# =============================================================================
# MEAL DATA FACTORIES (DOMAIN)
# =============================================================================


def create_meal_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create meal kwargs with deterministic values and comprehensive validation.

    Uses check_missing_attributes to ensure completeness.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required meal creation parameters
    """
    # Get the next meal ID for this meal
    meal_counter = get_next_meal_id()

    # Get realistic test data for deterministic values
    realistic_meal = REALISTIC_MEALS[(meal_counter - 1) % len(REALISTIC_MEALS)]

    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Generate IDs
    meal_id = kwargs.get("id", str(uuid4()))
    author_id = kwargs.get("author_id", str(uuid4()))

    # Create recipes if specified in realistic data and not overridden
    recipes = kwargs.get("recipes")
    if recipes is None and realistic_meal.get("recipe_count", 0) > 0:
        recipe_count = realistic_meal["recipe_count"]
        recipes = create_multiple_recipes_for_meal(
            meal_id=meal_id, author_id=author_id, recipe_count=recipe_count
        )

    final_kwargs = {
        "id": meal_id,
        "name": kwargs.get("name", realistic_meal["name"]),
        "author_id": author_id,
        "menu_id": kwargs.get("menu_id"),
        "description": kwargs.get("description", realistic_meal.get("description")),
        "notes": kwargs.get("notes", realistic_meal.get("notes")),
        "like": kwargs.get("like", meal_counter % 3 == 0),
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
        "recipes": recipes,
        "tags": kwargs.get("tags", set()),
    }

    # Allow override of any attribute
    final_kwargs.update(kwargs)

    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(Meal, final_kwargs)
    assert not missing, f"Missing attributes for Meal: {missing}"

    return final_kwargs


def create_meal(**kwargs) -> Meal:
    """
    Create a Meal domain entity with deterministic data and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with comprehensive validation
    """
    meal_kwargs = create_meal_kwargs(**kwargs)
    return Meal(**meal_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (DOMAIN)
# =============================================================================


def create_low_calorie_meal(**kwargs) -> Meal:
    """
    Create a meal with low calorie characteristics and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal with low calorie density and appropriate tags
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create recipes with low calorie focus
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Low Calorie Main Course",
                description="Light and nutritious main course with minimal calories",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Low Calorie Side Dish",
                description="Fresh vegetable side dish with minimal calories",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Light Mediterranean Bowl"),
        "description": kwargs.get(
            "description",
            "A nutritious, low-calorie meal packed with fresh vegetables and lean proteins",
        ),
        "notes": kwargs.get(
            "notes",
            "Perfect for weight management goals. Rich in fiber and nutrients while being calorie-conscious.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="diet", value="low-calorie", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="health", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="healthy", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_quick_meal(**kwargs) -> Meal:
    """
    Create a meal with quick preparation time and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal with short total_time and appropriate tags
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create recipes with quick preparation focus
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Quick Power Bowl",
                description="Fast and nutritious main course ready in minutes",
                total_time=10,
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="sauce",
                name="Quick Dressing",
                description="Simple dressing mixed in seconds",
                total_time=2,
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "15-Minute Power Bowl"),
        "description": kwargs.get(
            "description",
            "Fast preparation meal for busy schedules with maximum nutrition",
        ),
        "notes": kwargs.get(
            "notes",
            "Perfect for weeknight dinners or quick lunches. Pre-prep ingredients on weekends for even faster assembly.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="difficulty", value="easy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="occasion", value="quick", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="healthy", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_vegetarian_meal(**kwargs) -> Meal:
    """
    Create a vegetarian meal with appropriate tags and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal with vegetarian tags and characteristics
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create vegetarian recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Garden Vegetable Main",
                description="Hearty vegetarian main course with seasonal vegetables",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Herb-Roasted Vegetables",
                description="Colorful roasted vegetables with fresh herbs",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="sauce",
                name="Tahini Dressing",
                description="Creamy plant-based dressing with tahini",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Garden Harvest Feast"),
        "description": kwargs.get(
            "description",
            "Plant-based nutritious meal celebrating seasonal vegetables and grains",
        ),
        "notes": kwargs.get(
            "notes",
            "Bursting with fresh flavors and plant-based proteins. Easily adaptable to vegan by omitting dairy.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="diet", value="vegetarian", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="healthy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="lunch", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_high_protein_meal(**kwargs) -> Meal:
    """
    Create a meal with high protein content and validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal with high protein characteristics and tags
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create high protein recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="High Protein Main Course",
                description="Protein-rich main course for muscle building and recovery",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Protein-Packed Side",
                description="Additional protein source to complement the main dish",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Athlete's Power Plate"),
        "description": kwargs.get(
            "description", "High-protein meal designed for muscle building and recovery"
        ),
        "notes": kwargs.get(
            "notes",
            "Ideal post-workout meal with complete amino acid profile. Great for fitness enthusiasts and athletes.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="diet", value="high-protein", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="fitness", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="occasion",
                    value="post-workout",
                    author_id=author_id,
                    type="meal",
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_family_meal(**kwargs) -> Meal:
    """
    Create a meal suitable for families with validation.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal with family-friendly characteristics
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create family-friendly recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Family-Style Main Course",
                description="Hearty main course that pleases all ages",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Kid-Friendly Side Dish",
                description="Simple and nutritious side dish kids will love",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="dessert",
                name="Family Dessert",
                description="Sweet treat to end the family meal",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Sunday Family Dinner"),
        "description": kwargs.get(
            "description",
            "Hearty, comforting meal perfect for bringing the whole family together",
        ),
        "notes": kwargs.get(
            "notes",
            "Kid-friendly flavors with hidden vegetables. Makes great leftovers for the next day's lunch.",
        ),
        "like": kwargs.get("like", True),  # Families usually like their regular meals
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="occasion", value="family", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="difficulty", value="medium", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="dinner", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


# =============================================================================
# ENHANCED SPECIALIZED FACTORY FUNCTIONS (DOMAIN)
# =============================================================================


def create_simple_meal(**kwargs) -> Meal:
    """
    Create a simple meal with minimal complexity for basic testing.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with simple structure
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create simple recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Simple Main Course",
                description="Basic main course for simple meal",
            )
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Simple Daily Meal"),
        "description": kwargs.get("description", "A simple, everyday meal for testing"),
        "notes": kwargs.get(
            "notes", "Basic meal with straightforward preparation and familiar flavors."
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="difficulty", value="easy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="simple", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_complex_meal(**kwargs) -> Meal:
    """
    Create a complex meal with many detailed attributes for comprehensive testing.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with complex structure
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Get meal counter for deterministic values
    meal_counter = get_next_meal_id()

    # Create complex recipes with multiple courses
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="appetizer",
                name="Gourmet Appetizer",
                description="Sophisticated starter with complex flavors",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Multi-Course Main",
                description="Elaborate main course with multiple preparation techniques",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Artisanal Side Dish",
                description="Carefully crafted side dish with seasonal ingredients",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="dessert",
                name="Decadent Dessert",
                description="Rich dessert to complete the gourmet experience",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="sauce",
                name="Signature Sauce",
                description="Complex sauce to elevate the meal",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Gourmet Multi-Course Experience"),
        "description": kwargs.get(
            "description",
            "A sophisticated meal with multiple courses and complex flavors designed for comprehensive testing scenarios",
        ),
        "notes": kwargs.get(
            "notes",
            "This meal features multiple preparation techniques, seasonal ingredients, and requires careful timing. Perfect for special occasions and testing complex scenarios.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "image_url": kwargs.get(
            "image_url", f"https://example.com/complex-meal-{meal_counter}.jpg"
        ),
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="difficulty", value="hard", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="gourmet", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="occasion", value="special", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="cuisine", value="fusion", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="dinner", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "image_url",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_minimal_meal(**kwargs) -> Meal:
    """
    Create a minimal meal with only required fields for edge case testing.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with minimal data
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Get meal counter for deterministic values
    meal_counter = get_next_meal_id()

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Minimal Meal"),
        "description": kwargs.get("description"),
        "notes": kwargs.get("notes"),
        "like": kwargs.get("like", generate_meal_like_value(counter=meal_counter)),
        "image_url": kwargs.get("image_url"),
        "tags": kwargs.get("tags", set()),
        "recipes": kwargs.get("recipes", []),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "image_url",
                "tags",
                "recipes",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_meal_with_max_fields(**kwargs) -> Meal:
    """
    Create a meal with maximum fields populated for comprehensive testing.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with all possible fields populated
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Get meal counter for deterministic values
    meal_counter = get_next_meal_id()

    # Create comprehensive recipes with maximum fields
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="appetizer",
                name="Maximum Field Appetizer",
                description="Appetizer with all possible fields populated",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Maximum Field Main Course",
                description="Main course with comprehensive data",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Maximum Field Side",
                description="Side dish with all metadata",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="dessert",
                name="Maximum Field Dessert",
                description="Dessert with full field coverage",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="sauce",
                name="Maximum Field Sauce",
                description="Sauce with complete attributes",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="beverage",
                name="Maximum Field Beverage",
                description="Beverage with all fields populated",
            ),
        ]

    # Create comprehensive tags
    tags = set()
    tag_combinations = [
        ("difficulty", "medium"),
        ("cuisine", "international"),
        ("style", "fusion"),
        ("occasion", "entertaining"),
        ("category", "dinner"),
        ("diet", "balanced"),
        ("season", "all-season"),
        ("mood", "celebratory"),
    ]

    for key, value in tag_combinations:
        tags.add(
            create_meal_tag(key=key, value=value, author_id=author_id, type="meal")
        )

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Complete Meal Experience with Maximum Fields"),
        "description": kwargs.get(
            "description",
            "A comprehensive meal with all possible fields populated for testing maximum data scenarios and edge cases",
        ),
        "notes": kwargs.get(
            "notes",
            "This meal represents the maximum complexity scenario with detailed notes about preparation, dietary considerations, flavor profiles, and serving suggestions. Perfect for testing data handling limits.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "image_url": kwargs.get(
            "image_url", f"https://example.com/max-meal-{meal_counter}.jpg"
        ),
        "tags": kwargs.get("tags", tags),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "image_url",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_breakfast_meal(**kwargs) -> Meal:
    """
    Create a breakfast meal with morning-specific characteristics.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity optimized for breakfast
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create breakfast-specific recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Energizing Breakfast Main",
                description="Nutritious main course to start the day",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Fresh Fruit Side",
                description="Vitamin-rich fruit accompaniment",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="beverage",
                name="Morning Beverage",
                description="Refreshing drink to complement breakfast",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Energizing Morning Start"),
        "description": kwargs.get(
            "description",
            "Perfect breakfast meal to start the day with sustained energy and nutrition",
        ),
        "notes": kwargs.get(
            "notes",
            "Balanced breakfast with protein, healthy fats, and complex carbs for sustained energy throughout the morning.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="breakfast", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="healthy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="difficulty", value="easy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="occasion", value="everyday", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_dessert_meal(**kwargs) -> Meal:
    """
    Create a dessert meal with sweet characteristics.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity optimized for dessert
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create dessert-focused recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="dessert",
                name="Main Dessert Course",
                description="Rich and indulgent main dessert",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Sweet Accompaniment",
                description="Light side to complement the main dessert",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Decadent Sweet Finale"),
        "description": kwargs.get(
            "description",
            "Indulgent dessert meal perfect for special occasions and sweet cravings",
        ),
        "notes": kwargs.get(
            "notes",
            "Rich and satisfying dessert with balanced sweetness. Best enjoyed in moderate portions.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="dessert", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="sweet", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="occasion", value="special", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="diet", value="vegetarian", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_vegan_meal(**kwargs) -> Meal:
    """
    Create a vegan meal with plant-based characteristics.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity optimized for vegan diet
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create vegan recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Plant-Based Main Course",
                description="Nutritious vegan main course with complete proteins",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Seasonal Vegetable Side",
                description="Fresh seasonal vegetables prepared vegan-style",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="sauce",
                name="Plant-Based Sauce",
                description="Dairy-free sauce with rich umami flavors",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Plant-Based Nourishment"),
        "description": kwargs.get(
            "description",
            "Completely plant-based meal rich in nutrients and satisfying flavors",
        ),
        "notes": kwargs.get(
            "notes",
            "Nutrient-dense vegan meal with complete amino acids and essential vitamins. Perfect for plant-based lifestyle.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="diet", value="vegan", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="plant-based", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="healthy", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="difficulty", value="medium", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_keto_meal(**kwargs) -> Meal:
    """
    Create a ketogenic meal with high fat, low carb characteristics.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity optimized for ketogenic diet
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Create keto-friendly recipes
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Keto Main Course",
                description="High-fat, low-carb main course for ketosis",
            ),
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="side",
                name="Low-Carb Side Dish",
                description="Ketogenic side dish with minimal carbohydrates",
            ),
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Keto-Friendly Feast"),
        "description": kwargs.get(
            "description", "High-fat, low-carb meal perfect for ketogenic lifestyle"
        ),
        "notes": kwargs.get(
            "notes",
            "Carefully balanced for ketosis with high-quality fats and minimal carbs. Track macros for best results.",
        ),
        "like": kwargs.get("like", True),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="diet", value="keto", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="style", value="low-carb", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="category", value="high-fat", author_id=author_id, type="meal"
                ),
                create_meal_tag(
                    key="difficulty", value="medium", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


def create_meal_without_nutrition(**kwargs) -> Meal:
    """
    Create a meal without nutrition information for testing edge cases.

    Args:
        **kwargs: Override any default values

    Returns:
        Meal domain entity with no nutrition data
    """
    author_id = kwargs.get("author_id", str(uuid4()))
    meal_id = kwargs.get("id", str(uuid4()))

    # Get meal counter for deterministic values
    meal_counter = get_next_meal_id()

    # Create recipes without nutrition data
    recipes = kwargs.get("recipes", [])
    if not recipes:
        recipes = [
            create_recipe_for_meal(
                meal_id=meal_id,
                author_id=author_id,
                recipe_type="main",
                name="Recipe Without Nutrition",
                description="Recipe without nutrition information",
                nutri_facts=None,
            )
        ]

    final_kwargs = {
        "id": meal_id,
        "author_id": author_id,
        "name": kwargs.get("name", "Meal Without Nutrition Data"),
        "description": kwargs.get(
            "description", "Meal for testing scenarios without nutrition information"
        ),
        "notes": kwargs.get(
            "notes", "This meal has no nutrition data for testing edge cases."
        ),
        "like": kwargs.get("like", generate_meal_like_value(counter=meal_counter)),
        "recipes": recipes,
        "tags": kwargs.get(
            "tags",
            {
                create_meal_tag(
                    key="category", value="test", author_id=author_id, type="meal"
                ),
            },
        ),
        **{
            k: v
            for k, v in kwargs.items()
            if k
            not in [
                "id",
                "name",
                "description",
                "notes",
                "like",
                "recipes",
                "tags",
                "author_id",
            ]
        },
    }
    return create_meal(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP (DOMAIN)
# =============================================================================


def create_meals_with_tags(count: int = 3, tags_per_meal: int = 2) -> list[Meal]:
    """Create multiple meals with various tag combinations for testing"""
    meals = []

    # Create a pool of unique tags first to avoid potential duplicates
    unique_tags = {}  # Key: (key, value, author_id, type), Value: Tag

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
            # Generate unique author_id for each meal
            author_id = str(uuid4())

            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx

                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]

                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]

                type_idx = (
                    total_tag_index
                    // (len(keys) * max(len(v) for v in values_by_key.values()))
                ) % len(tag_types)
                tag_type = tag_types[type_idx]

                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)

                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag(
                        key=key, value=value, author_id=author_id, type=tag_type
                    )
                    unique_tags[tag_key] = tag

    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())

    for i in range(count):
        # Create tags for this meal
        tags = set()
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])

        meal_kwargs = create_meal_kwargs()
        meal_kwargs["tags"] = tags
        meal = create_meal(**meal_kwargs)
        meals.append(meal)
    return meals


def create_test_dataset(
    meal_count: int = 100, tags_per_meal: int = 0
) -> dict[str, Any]:
    """Create a dataset of meals for performance testing"""
    meals = []
    all_tags = []

    # Create a pool of unique tags first to avoid potential duplicates
    unique_tags = {}  # Key: (key, value, author_id, type), Value: Tag

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
            # Generate unique author_id for each meal
            author_id = str(uuid4())

            for tag_idx in range(tags_per_meal):
                # Use a deterministic approach to create unique combinations
                total_tag_index = meal_idx * tags_per_meal + tag_idx

                # Cycle through combinations to maximize uniqueness
                key_idx = total_tag_index % len(keys)
                key = keys[key_idx]

                value_idx = (total_tag_index // len(keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]

                type_idx = (
                    total_tag_index
                    // (len(keys) * max(len(v) for v in values_by_key.values()))
                ) % len(tag_types)
                tag_type = tag_types[type_idx]

                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)

                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag(
                        key=key, value=value, author_id=author_id, type=tag_type
                    )
                    unique_tags[tag_key] = tag
                    all_tags.append(tag)

    # Now create meals and assign tags from the unique pool
    unique_tag_list = list(unique_tags.values())

    for i in range(meal_count):
        # Create tags for this meal if requested
        tags = set()
        if tags_per_meal > 0 and unique_tag_list:
            # Select tags for this meal from the unique pool
            start_idx = (i * tags_per_meal) % len(unique_tag_list)
            for j in range(min(tags_per_meal, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])

        meal_kwargs = create_meal_kwargs()
        if tags:
            meal_kwargs["tags"] = tags
        meal = create_meal(**meal_kwargs)
        meals.append(meal)

    return {"meals": meals, "all_tags": all_tags}


# =============================================================================
# COLLECTION CREATION UTILITIES (DOMAIN)
# =============================================================================


def create_meal_collection(count: int = 5) -> list[Meal]:
    """
    Create a collection of diverse meals for batch testing.

    Args:
        count: Number of meals to create

    Returns:
        List of Meal domain entities
    """
    meals = []
    for i in range(count):
        if i % 9 == 0:
            meal = create_simple_meal()
        elif i % 9 == 1:
            meal = create_complex_meal()
        elif i % 9 == 2:
            meal = create_quick_meal()
        elif i % 9 == 3:
            meal = create_vegetarian_meal()
        elif i % 9 == 4:
            meal = create_high_protein_meal()
        elif i % 9 == 5:
            meal = create_breakfast_meal()
        elif i % 9 == 6:
            meal = create_dessert_meal()
        elif i % 9 == 7:
            meal = create_vegan_meal()
        else:
            meal = create_keto_meal()
        meals.append(meal)
    return meals


def create_meals_by_cuisine(cuisine: str, count: int = 3) -> list[Meal]:
    """
    Create meals of a specific cuisine type.

    Args:
        cuisine: Cuisine type to create
        count: Number of meals to create

    Returns:
        List of Meal domain entities of specified cuisine
    """
    author_id = str(uuid4())
    meals = []
    for i in range(count):
        meal = create_meal(
            author_id=author_id,
            name=f"{cuisine.title()} Meal {i+1}",
            description=f"Authentic {cuisine} meal for testing",
            tags={
                create_meal_tag(
                    key="cuisine", value=cuisine, author_id=author_id, type="meal"
                )
            },
        )
        meals.append(meal)
    return meals


def create_meals_by_difficulty(difficulty: str, count: int = 3) -> list[Meal]:
    """
    Create meals of a specific difficulty level.

    Args:
        difficulty: Difficulty level (easy, medium, hard)
        count: Number of meals to create

    Returns:
        List of Meal domain entities of specified difficulty
    """
    author_id = str(uuid4())
    meals = []
    for i in range(count):
        meal = create_meal(
            author_id=author_id,
            name=f"{difficulty.title()} Meal {i+1}",
            description=f"A {difficulty} meal for testing",
            tags={
                create_meal_tag(
                    key="difficulty", value=difficulty, author_id=author_id, type="meal"
                )
            },
        )
        meals.append(meal)
    return meals


def create_meals_by_category(category: str, count: int = 3) -> list[Meal]:
    """
    Create meals of a specific category.

    Args:
        category: Category type (breakfast, lunch, dinner, etc.)
        count: Number of meals to create

    Returns:
        List of Meal domain entities of specified category
    """
    author_id = str(uuid4())
    meals = []
    for i in range(count):
        meal = create_meal(
            author_id=author_id,
            name=f"{category.title()} Meal {i+1}",
            description=f"Perfect {category} meal for testing",
            tags={
                create_meal_tag(
                    key="category", value=category, author_id=author_id, type="meal"
                )
            },
        )
        meals.append(meal)
    return meals


def create_meals_by_diet(diet: str, count: int = 3) -> list[Meal]:
    """
    Create meals of a specific dietary type.

    Args:
        diet: Diet type (vegetarian, vegan, keto, etc.)
        count: Number of meals to create

    Returns:
        List of Meal domain entities of specified diet
    """
    author_id = str(uuid4())
    meals = []
    for i in range(count):
        if diet == "keto":
            meal = create_keto_meal(author_id=author_id, name=f"Keto Meal {i+1}")
        elif diet == "vegan":
            meal = create_vegan_meal(author_id=author_id, name=f"Vegan Meal {i+1}")
        elif diet == "vegetarian":
            meal = create_vegetarian_meal(
                author_id=author_id, name=f"Vegetarian Meal {i+1}"
            )
        elif diet == "high-protein":
            meal = create_high_protein_meal(
                author_id=author_id, name=f"High Protein Meal {i+1}"
            )
        elif diet == "low-calorie":
            meal = create_low_calorie_meal(
                author_id=author_id, name=f"Low Calorie Meal {i+1}"
            )
        else:
            meal = create_meal(
                author_id=author_id,
                name=f"{diet.title()} Meal {i+1}",
                description=f"A {diet} meal for testing",
                tags={
                    create_meal_tag(
                        key="diet", value=diet, author_id=author_id, type="meal"
                    )
                },
            )
        meals.append(meal)
    return meals


def create_test_meal_dataset(meal_count: int = 10) -> dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.

    Args:
        meal_count: Number of meals to create

    Returns:
        Dict containing meals, metadata, and related objects
    """
    reset_all_counters()

    meals = []
    all_tags = []

    for i in range(meal_count):
        # Create varied meals
        if i % 8 == 0:
            meal = create_simple_meal()
        elif i % 8 == 1:
            meal = create_complex_meal()
        elif i % 8 == 2:
            meal = create_minimal_meal()
        elif i % 8 == 3:
            meal = create_meal_with_max_fields()
        elif i % 8 == 4:
            meal = create_breakfast_meal()
        elif i % 8 == 5:
            meal = create_dessert_meal()
        elif i % 8 == 6:
            meal = create_vegan_meal()
        else:
            meal = create_meal()

        # Collect related objects
        if meal.tags:
            all_tags.extend(meal.tags)

        meals.append(meal)

    return {
        "meals": meals,
        "tags": all_tags,
        "total_meals": len(meals),
        "metadata": {
            "meal_count": len(meals),
            "tag_count": len(all_tags),
        },
    }


# =============================================================================
# PERFORMANCE TESTING UTILITIES (DOMAIN)
# =============================================================================


def create_bulk_meal_creation_dataset(count: int = 100) -> list[dict[str, Any]]:
    """
    Create a dataset for bulk meal creation performance testing.

    Args:
        count: Number of meal kwargs to create

    Returns:
        List of meal kwargs dictionaries
    """
    reset_all_counters()

    kwargs_list = []
    for i in range(count):
        kwargs = create_meal_kwargs()
        kwargs_list.append(kwargs)

    return kwargs_list


def create_conversion_performance_dataset(count: int = 100) -> dict[str, Any]:
    """
    Create a dataset for conversion performance testing.

    Args:
        count: Number of meals to create

    Returns:
        Dict containing meals for performance testing
    """
    reset_all_counters()

    domain_meals = []
    for i in range(count):
        if i % 6 == 0:
            meal = create_simple_meal()
        elif i % 6 == 1:
            meal = create_complex_meal()
        elif i % 6 == 2:
            meal = create_meal_with_max_fields()
        elif i % 6 == 3:
            meal = create_breakfast_meal()
        elif i % 6 == 4:
            meal = create_vegan_meal()
        else:
            meal = create_meal()
        domain_meals.append(meal)

    return {"domain_meals": domain_meals, "total_count": count}


def create_nested_object_validation_dataset(
    count: int = 50,
    tags_per_meal: int | None = None,
    recipes_per_meal: int | None = None,
) -> list[Meal]:
    """
    Create a dataset with complex nested objects for validation testing.

    Args:
        count: Number of meals to create
        tags_per_meal: Number of tags per meal (optional)
        recipes_per_meal: Number of recipes per meal (optional)

    Returns:
        List of Meal domain entities with complex nested structures
    """
    reset_all_counters()

    meals = []
    for i in range(count):
        author_id = str(uuid4())
        meal_id = str(uuid4())

        kwargs: dict[str, Any] = {"author_id": author_id, "id": meal_id}

        # Add tags if specified
        if tags_per_meal is not None:
            tags = set()
            for j in range(tags_per_meal):
                tag = create_meal_tag(
                    key=f"test_key_{j}",
                    value=f"test_value_{j}",
                    author_id=author_id,
                    type="meal",
                )
                tags.add(tag)
            kwargs["tags"] = tags

        # Add recipes if specified
        if recipes_per_meal is not None:
            recipes = create_multiple_recipes_for_meal(
                meal_id=meal_id, author_id=author_id, recipe_count=recipes_per_meal
            )
            kwargs["recipes"] = recipes

        # Alternate between complex and max fields meals
        if i % 2 == 0:
            meal = create_complex_meal(**kwargs)
        else:
            meal = create_meal_with_max_fields(**kwargs)
        meals.append(meal)

    return meals


def create_meal_with_nested_recipes_dataset(
    count: int = 20, min_recipes: int = 1, max_recipes: int = 6
) -> list[Meal]:
    """
    Create a dataset of meals with varying numbers of nested recipes for testing.

    Args:
        count: Number of meals to create
        min_recipes: Minimum number of recipes per meal
        max_recipes: Maximum number of recipes per meal

    Returns:
        List of Meal domain entities with varying recipe counts
    """
    reset_all_counters()

    meals = []
    for i in range(count):
        author_id = str(uuid4())
        meal_id = str(uuid4())

        # Vary the number of recipes per meal
        recipe_count = min_recipes + (i % (max_recipes - min_recipes + 1))

        # Create the meal with recipes
        if i % 8 == 0:
            meal = create_simple_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 1:
            meal = create_complex_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 2:
            meal = create_quick_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 3:
            meal = create_vegetarian_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 4:
            meal = create_high_protein_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 5:
            meal = create_breakfast_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        elif i % 8 == 6:
            meal = create_vegan_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )
        else:
            meal = create_keto_meal(
                author_id=author_id,
                id=meal_id,
                recipes=create_multiple_recipes_for_meal(
                    meal_id, author_id, recipe_count
                ),
            )

        meals.append(meal)

    return meals


def create_meal_computed_properties_test_dataset(count: int = 15) -> dict[str, Any]:
    """
    Create a comprehensive dataset for testing meal computed properties.

    Args:
        count: Number of meals to create

    Returns:
        Dict containing meals with various computed property scenarios
    """
    reset_all_counters()

    meals = []
    computed_property_scenarios = []

    for i in range(count):
        if i % 5 == 0:
            meal = create_meal_with_computed_property_issues()
            computed_property_scenarios.append("missing_data")
        elif i % 5 == 1:
            meal = create_meal_with_aggregation_edge_cases()
            computed_property_scenarios.append("extreme_values")
        elif i % 5 == 2:
            meal = create_meal_without_recipes()
            computed_property_scenarios.append("no_recipes")
        elif i % 5 == 3:
            meal = create_meal_without_nutrition()
            computed_property_scenarios.append("no_nutrition")
        else:
            # Create normal meal with proper computed properties
            meal = create_complex_meal()
            computed_property_scenarios.append("normal")

        meals.append(meal)

    return {
        "meals": meals,
        "scenarios": computed_property_scenarios,
        "total_count": count,
        "metadata": {
            "meal_count": len(meals),
            "scenarios_count": len(set(computed_property_scenarios)),
            "computed_property_test_coverage": True,
        },
    }


def create_comprehensive_meal_scenarios() -> dict[str, list[Meal]]:
    """
    Create comprehensive meal scenarios for testing different aspects.

    Returns:
        Dict containing different meal scenarios categorized by purpose
    """
    return {
        "basic_meals": [create_simple_meal(), create_meal(), create_minimal_meal()],
        "complex_meals": [
            create_complex_meal(),
            create_meal_with_max_fields(),
            create_family_meal(),
        ],
        "dietary_meals": [
            create_vegetarian_meal(),
            create_vegan_meal(),
            create_keto_meal(),
            create_high_protein_meal(),
            create_low_calorie_meal(),
        ],
        "category_meals": [
            create_breakfast_meal(),
            create_dessert_meal(),
            create_quick_meal(),
        ],
        "edge_case_meals": [create_meal_without_nutrition(), create_minimal_meal()],
        "computed_property_test_meals": [
            create_meal_with_computed_property_issues(),
            create_meal_with_aggregation_edge_cases(),
            create_meal_without_recipes(),
        ],
    }


def create_meal_performance_benchmark(
    small_count: int = 10, medium_count: int = 50, large_count: int = 100
) -> dict[str, Any]:
    """
    Create datasets for performance benchmarking with nested recipes.

    Args:
        small_count: Number of meals for small dataset
        medium_count: Number of meals for medium dataset
        large_count: Number of meals for large dataset

    Returns:
        Dict containing different sized datasets for benchmarking
    """
    return {
        "small_dataset": create_test_meal_dataset(small_count),
        "medium_dataset": create_test_meal_dataset(medium_count),
        "large_dataset": create_test_meal_dataset(large_count),
        "bulk_creation_data": create_bulk_meal_creation_dataset(large_count),
        "conversion_data": create_conversion_performance_dataset(large_count),
        "nested_recipes_data": create_meal_with_nested_recipes_dataset(medium_count),
        "computed_properties_data": create_meal_computed_properties_test_dataset(
            small_count
        ),
    }
