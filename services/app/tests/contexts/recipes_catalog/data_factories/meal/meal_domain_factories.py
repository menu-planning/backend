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

from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

# Import check_missing_attributes for validation
from tests.contexts.recipes_catalog.data_factories.shared_domain_factories import create_meal_tag
from tests.utils import check_missing_attributes

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
        "weight_in_grams": 650
    },
    {
        "name": "Quick Healthy Lunch Bowl",
        "description": "Light, nutritious meal packed with vegetables, quinoa, and Mediterranean flavors. Perfect for meal prep and busy weekdays.",
        "notes": "Great for meal prep - can be prepared in advance and stored for up to 3 days. Customize with your favorite seasonal vegetables.",
        "tags": ["lunch", "mediterranean", "vegetarian", "healthy", "meal-prep", "quick"],
        "total_time": 25,
        "like": True,
        "calorie_density": 280.0,
        "carbo_percentage": 55.0,
        "protein_percentage": 20.0,
        "total_fat_percentage": 25.0,
        "weight_in_grams": 450
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
        "weight_in_grams": 750
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
        "weight_in_grams": 550
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
        "weight_in_grams": 400
    }
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_MEAL_COUNTER = 1


def reset_meal_domain_counters() -> None:
    """Reset all counters for test isolation"""
    global _MEAL_COUNTER
    _MEAL_COUNTER = 1


# =============================================================================
# MEAL DATA FACTORIES (DOMAIN)
# =============================================================================

def create_meal_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create meal kwargs with deterministic values and comprehensive validation.
    
    Uses check_missing_attributes to ensure completeness.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required meal creation parameters
    """
    global _MEAL_COUNTER
    
    # Get realistic test data for deterministic values
    realistic_meal = REALISTIC_MEALS[(_MEAL_COUNTER - 1) % len(REALISTIC_MEALS)]
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", realistic_meal["name"]),
        "author_id": kwargs.get("author_id", f"author_{(_MEAL_COUNTER % 5) + 1}"),
        "menu_id": kwargs.get("menu_id", None),
        "description": kwargs.get("description", realistic_meal.get("description")),
        "notes": kwargs.get("notes", realistic_meal.get("notes")),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),
        "image_url": kwargs.get("image_url", f"https://example.com/meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get("tags", set()),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(Meal, final_kwargs)
    assert not missing, f"Missing attributes for Meal: {missing}"
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
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
    final_kwargs = {
        "name": kwargs.get("name", "Light Mediterranean Bowl"),
        "description": kwargs.get("description", "A nutritious, low-calorie meal packed with fresh vegetables and lean proteins"),
        "notes": kwargs.get("notes", "Perfect for weight management goals. Rich in fiber and nutrients while being calorie-conscious."),
        "calorie_density": kwargs.get("calorie_density", 180.0),  # Low calorie density
        "carbo_percentage": kwargs.get("carbo_percentage", 60.0),
        "protein_percentage": kwargs.get("protein_percentage", 25.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 15.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 350),
        "total_time": kwargs.get("total_time", 20),
        "like": kwargs.get("like", True),
        "tags": kwargs.get("tags", {
            create_meal_tag(key="diet", value="low-calorie", type="meal"),
            create_meal_tag(key="category", value="health", type="meal"),
            create_meal_tag(key="style", value="healthy", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
    final_kwargs = {
        "name": kwargs.get("name", "15-Minute Power Bowl"),
        "description": kwargs.get("description", "Fast preparation meal for busy schedules with maximum nutrition"),
        "notes": kwargs.get("notes", "Perfect for weeknight dinners or quick lunches. Pre-prep ingredients on weekends for even faster assembly."),
        "total_time": kwargs.get("total_time", 15),
        "calorie_density": kwargs.get("calorie_density", 300.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 400),
        "like": kwargs.get("like", True),
        "tags": kwargs.get("tags", {
            create_meal_tag(key="difficulty", value="easy", type="meal"),
            create_meal_tag(key="occasion", value="quick", type="meal"),
            create_meal_tag(key="style", value="healthy", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "total_time", "calorie_density", "weight_in_grams", "like", "tags"]}
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
    final_kwargs = {
        "name": kwargs.get("name", "Garden Harvest Feast"),
        "description": kwargs.get("description", "Plant-based nutritious meal celebrating seasonal vegetables and grains"),
        "notes": kwargs.get("notes", "Bursting with fresh flavors and plant-based proteins. Easily adaptable to vegan by omitting dairy."),
        "calorie_density": kwargs.get("calorie_density", 250.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 55.0),
        "protein_percentage": kwargs.get("protein_percentage", 20.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 25.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 500),
        "total_time": kwargs.get("total_time", 35),
        "like": kwargs.get("like", True),
        "tags": kwargs.get("tags", {
            create_meal_tag(key="diet", value="vegetarian", type="meal"),
            create_meal_tag(key="style", value="healthy", type="meal"),
            create_meal_tag(key="category", value="lunch", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
    final_kwargs = {
        "name": kwargs.get("name", "Athlete's Power Plate"),
        "description": kwargs.get("description", "High-protein meal designed for muscle building and recovery"),
        "notes": kwargs.get("notes", "Ideal post-workout meal with complete amino acid profile. Great for fitness enthusiasts and athletes."),
        "calorie_density": kwargs.get("calorie_density", 350.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 35.0),
        "protein_percentage": kwargs.get("protein_percentage", 40.0),  # High protein
        "total_fat_percentage": kwargs.get("total_fat_percentage", 25.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 600),
        "total_time": kwargs.get("total_time", 45),
        "like": kwargs.get("like", True),
        "tags": kwargs.get("tags", {
            create_meal_tag(key="diet", value="high-protein", type="meal"),
            create_meal_tag(key="style", value="fitness", type="meal"),
            create_meal_tag(key="occasion", value="post-workout", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
    final_kwargs = {
        "name": kwargs.get("name", "Sunday Family Dinner"),
        "description": kwargs.get("description", "Hearty, comforting meal perfect for bringing the whole family together"),
        "notes": kwargs.get("notes", "Kid-friendly flavors with hidden vegetables. Makes great leftovers for the next day's lunch."),
        "calorie_density": kwargs.get("calorie_density", 320.0),
        "carbo_percentage": kwargs.get("carbo_percentage", 45.0),
        "protein_percentage": kwargs.get("protein_percentage", 25.0),
        "total_fat_percentage": kwargs.get("total_fat_percentage", 30.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 700),
        "total_time": kwargs.get("total_time", 60),
        "like": kwargs.get("like", True),  # Families usually like their regular meals
        "tags": kwargs.get("tags", {
            create_meal_tag(key="occasion", value="family", type="meal"),
            create_meal_tag(key="difficulty", value="medium", type="meal"),
            create_meal_tag(key="category", value="dinner", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
    }
    return create_meal(**final_kwargs)

# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP (DOMAIN)
# =============================================================================

def create_meals_with_tags(count: int = 3, tags_per_meal: int = 2) -> List[Meal]:
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
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
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
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag(key=key, value=value, author_id=author_id, type=tag_type)
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


def create_test_dataset(meal_count: int = 100, tags_per_meal: int = 0) -> Dict[str, Any]:
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
        "season": ["spring", "summer", "fall", "winter"]
    }
    max_authors = 5  # author_1 to author_5
    
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
                
                author_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                type_idx = (total_tag_index // (len(keys) * max(len(v) for v in values_by_key.values()) * max_authors)) % len(tag_types)
                tag_type = tag_types[type_idx]
                
                # Create unique combination key
                tag_key = (key, value, author_id, tag_type)
                
                # Only create if we haven't seen this combination before
                if tag_key not in unique_tags:
                    tag = create_meal_tag(key=key, value=value, author_id=author_id, type=tag_type)
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
    
    return {
        "meals": meals,
        "all_tags": all_tags
    }


