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
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
# ORM model imports
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.recipes_catalog.core.adapters.name_search import StrProcessor

# Import check_missing_attributes for validation
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
_TAG_COUNTER = 1
_RECIPE_COUNTER = 1


def reset_counters() -> None:
    """Reset all counters for test isolation"""
    global _MEAL_COUNTER, _TAG_COUNTER, _RECIPE_COUNTER
    _MEAL_COUNTER = 1
    _TAG_COUNTER = 1
    _RECIPE_COUNTER = 1


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
# MEAL DATA FACTORIES (ORM)
# =============================================================================

def create_meal_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create meal ORM kwargs with deterministic values.
    
    Similar to create_meal_kwargs but includes ORM-specific fields like preprocessed_name
    and nutritional calculation fields.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM meal creation parameters
    """
    global _MEAL_COUNTER
    
    # Get realistic test data for deterministic values
    realistic_meal = REALISTIC_MEALS[(_MEAL_COUNTER - 1) % len(REALISTIC_MEALS)]
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    # Default nutritional values (all fields from NutriFactsSaModel)
    default_nutri_facts = {
        "calories": kwargs.get("calories", 350.0 + (_MEAL_COUNTER * 25)),
        "protein": kwargs.get("protein", 20.0 + (_MEAL_COUNTER * 2)),
        "carbohydrate": kwargs.get("carbohydrate", 45.0 + (_MEAL_COUNTER * 3)),
        "total_fat": kwargs.get("total_fat", 15.0 + (_MEAL_COUNTER * 1)),
        "saturated_fat": kwargs.get("saturated_fat", 5.0 + (_MEAL_COUNTER * 0.5)),
        "trans_fat": kwargs.get("trans_fat", 0.0),
        "dietary_fiber": kwargs.get("dietary_fiber", 8.0 + (_MEAL_COUNTER * 0.5)),
        "sodium": kwargs.get("sodium", 650.0 + (_MEAL_COUNTER * 25)),
        "arachidonic_acid": kwargs.get("arachidonic_acid", None),
        "ashes": kwargs.get("ashes", None),
        "dha": kwargs.get("dha", None),
        "epa": kwargs.get("epa", None),
        "sugar": kwargs.get("sugar", 12.0 + (_MEAL_COUNTER * 1)),
        "starch": kwargs.get("starch", None),
        "biotin": kwargs.get("biotin", None),
        "boro": kwargs.get("boro", None),
        "caffeine": kwargs.get("caffeine", None),
        "calcium": kwargs.get("calcium", 150.0 + (_MEAL_COUNTER * 10)),
        "chlorine": kwargs.get("chlorine", None),
        "copper": kwargs.get("copper", None),
        "cholesterol": kwargs.get("cholesterol", None),
        "choline": kwargs.get("choline", None),
        "chrome": kwargs.get("chrome", None),
        "dextrose": kwargs.get("dextrose", None),
        "sulfur": kwargs.get("sulfur", None),
        "phenylalanine": kwargs.get("phenylalanine", None),
        "iron": kwargs.get("iron", 8.0 + (_MEAL_COUNTER * 0.5)),
        "insoluble_fiber": kwargs.get("insoluble_fiber", None),
        "soluble_fiber": kwargs.get("soluble_fiber", None),
        "fluor": kwargs.get("fluor", None),
        "phosphorus": kwargs.get("phosphorus", None),
        "fructo_oligosaccharides": kwargs.get("fructo_oligosaccharides", None),
        "fructose": kwargs.get("fructose", None),
        "galacto_oligosaccharides": kwargs.get("galacto_oligosaccharides", None),
        "galactose": kwargs.get("galactose", None),
        "glucose": kwargs.get("glucose", None),
        "glucoronolactone": kwargs.get("glucoronolactone", None),
        "monounsaturated_fat": kwargs.get("monounsaturated_fat", None),
        "polyunsaturated_fat": kwargs.get("polyunsaturated_fat", None),
        "guarana": kwargs.get("guarana", None),
        "inositol": kwargs.get("inositol", None),
        "inulin": kwargs.get("inulin", None),
        "iodine": kwargs.get("iodine", None),
        "l_carnitine": kwargs.get("l_carnitine", None),
        "l_methionine": kwargs.get("l_methionine", None),
        "lactose": kwargs.get("lactose", None),
        "magnesium": kwargs.get("magnesium", None),
        "maltose": kwargs.get("maltose", None),
        "manganese": kwargs.get("manganese", None),
        "molybdenum": kwargs.get("molybdenum", None),
        "linolenic_acid": kwargs.get("linolenic_acid", None),
        "linoleic_acid": kwargs.get("linoleic_acid", None),
        "omega_7": kwargs.get("omega_7", None),
        "omega_9": kwargs.get("omega_9", None),
        "oleic_acid": kwargs.get("oleic_acid", None),
        "other_carbo": kwargs.get("other_carbo", None),
        "polydextrose": kwargs.get("polydextrose", None),
        "polyols": kwargs.get("polyols", None),
        "potassium": kwargs.get("potassium", None),
        "sacarose": kwargs.get("sacarose", None),
        "selenium": kwargs.get("selenium", None),
        "silicon": kwargs.get("silicon", None),
        "sorbitol": kwargs.get("sorbitol", None),
        "sucralose": kwargs.get("sucralose", None),
        "taurine": kwargs.get("taurine", None),
        "vitamin_a": kwargs.get("vitamin_a", 750.0 + (_MEAL_COUNTER * 25)),
        "vitamin_b1": kwargs.get("vitamin_b1", None),
        "vitamin_b2": kwargs.get("vitamin_b2", None),
        "vitamin_b3": kwargs.get("vitamin_b3", None),
        "vitamin_b5": kwargs.get("vitamin_b5", None),
        "vitamin_b6": kwargs.get("vitamin_b6", None),
        "folic_acid": kwargs.get("folic_acid", None),
        "vitamin_b12": kwargs.get("vitamin_b12", None),
        "vitamin_c": kwargs.get("vitamin_c", 60.0 + (_MEAL_COUNTER * 5)),
        "vitamin_d": kwargs.get("vitamin_d", None),
        "vitamin_e": kwargs.get("vitamin_e", None),
        "vitamin_k": kwargs.get("vitamin_k", None),
        "zinc": kwargs.get("zinc", None),
        "retinol": kwargs.get("retinol", None),
        "thiamine": kwargs.get("thiamine", None),
        "riboflavin": kwargs.get("riboflavin", None),
        "pyridoxine": kwargs.get("pyridoxine", None),
        "niacin": kwargs.get("niacin", None),
        # Additional calculated fields that might be expected by ORM
        "metadata": kwargs.get("metadata", None),
        "registry": kwargs.get("registry", None),
        "type_annotation_map": kwargs.get("type_annotation_map", None),
    }
    
    final_kwargs = {
        "id": kwargs.get("id", f"meal_{_MEAL_COUNTER:03d}"),
        "name": kwargs.get("name", realistic_meal["name"]),
        "preprocessed_name": kwargs.get("preprocessed_name", StrProcessor(realistic_meal["name"]).output),
        "description": kwargs.get("description", realistic_meal.get("description")),
        "author_id": kwargs.get("author_id", f"author_{(_MEAL_COUNTER % 5) + 1}"),
        "menu_id": kwargs.get("menu_id", None),
        "notes": kwargs.get("notes", realistic_meal.get("notes")),
        "total_time": kwargs.get("total_time", realistic_meal.get("total_time", 30 + (_MEAL_COUNTER * 5))),
        "like": kwargs.get("like", _MEAL_COUNTER % 3 == 0),
        "weight_in_grams": kwargs.get("weight_in_grams", realistic_meal.get("weight_in_grams", 400 + (_MEAL_COUNTER * 50))),
        "calorie_density": kwargs.get("calorie_density", realistic_meal.get("calorie_density", 1.5 + (_MEAL_COUNTER % 2))),
        "carbo_percentage": kwargs.get("carbo_percentage", realistic_meal.get("carbo_percentage", 45.0 + (_MEAL_COUNTER % 15))),
        "protein_percentage": kwargs.get("protein_percentage", realistic_meal.get("protein_percentage", 20.0 + (_MEAL_COUNTER % 10))),
        "total_fat_percentage": kwargs.get("total_fat_percentage", realistic_meal.get("total_fat_percentage", 25.0 + (_MEAL_COUNTER % 15))),
        "image_url": kwargs.get("image_url", f"https://example.com/meal_{_MEAL_COUNTER}.jpg" if _MEAL_COUNTER % 2 == 0 else None),
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MEAL_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MEAL_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "recipes": kwargs.get("recipes", []),
        "tags": kwargs.get("tags", []),
        
        # Add nutri_facts composite field (required by MealSaModel even though we have individual fields)
        "nutri_facts": kwargs.get("nutri_facts", None),  # Will be created as composite from individual fields
    }
    
    # Add all nutritional fields
    final_kwargs.update(default_nutri_facts)
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(MealSaModel, final_kwargs)
    assert not missing, f"Missing attributes for MealSaModel: {missing}"
    
    # Increment counter for next call
    _MEAL_COUNTER += 1
    
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


# =============================================================================
# TAG DATA FACTORIES (DOMAIN)
# =============================================================================

def create_tag_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag kwargs with deterministic values and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with tag creation parameters
    """
    global _TAG_COUNTER
    
    # Predefined tag types for realistic test data
    tag_types = ["meal", "recipe", "product"]
    keys = ["category", "diet", "cuisine", "difficulty", "season", "style", "occasion"]
    values_by_key = {
        "category": ["breakfast", "lunch", "dinner", "snack", "dessert"],
        "diet": ["vegetarian", "vegan", "keto", "paleo", "mediterranean"],
        "cuisine": ["italian", "mexican", "asian", "american", "french"],
        "difficulty": ["easy", "medium", "hard"],
        "season": ["spring", "summer", "fall", "winter"],
        "style": ["comfort-food", "healthy", "fusion", "traditional"],
        "occasion": ["date-night", "family", "quick", "special"]
    }
    
    key = keys[(_TAG_COUNTER - 1) % len(keys)]
    value = values_by_key[key][(_TAG_COUNTER - 1) % len(values_by_key[key])]
    
    final_kwargs = {
        "key": kwargs.get("key", key),
        "value": kwargs.get("value", value),
        "author_id": kwargs.get("author_id", f"author_{((_TAG_COUNTER - 1) % 5) + 1}"),
        "type": kwargs.get("type", tag_types[(_TAG_COUNTER - 1) % len(tag_types)]),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(Tag, final_kwargs)
    assert not missing, f"Missing attributes for Tag: {missing}"
    
    _TAG_COUNTER += 1
    return final_kwargs


def create_tag(**kwargs) -> Tag:
    """
    Create a Tag value object with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Tag value object with comprehensive validation
    """
    tag_kwargs = create_tag_kwargs(**kwargs)
    return Tag(**tag_kwargs)


# =============================================================================
# TAG DATA FACTORIES (ORM)
# =============================================================================

def create_tag_orm_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create tag ORM kwargs with deterministic values and comprehensive validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM tag creation parameters
    """
    # Use the same logic as domain tags but reuse validation
    tag_kwargs = create_tag_kwargs(**kwargs)
    
    # ORM models use auto-increment for id, so we prepare kwargs accordingly
    final_kwargs = {
        "key": tag_kwargs["key"],
        "value": tag_kwargs["value"],
        "author_id": tag_kwargs["author_id"],
        "type": tag_kwargs["type"],
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(TagSaModel, final_kwargs)
    assert not missing, f"Missing attributes for TagSaModel: {missing}"
    
    return final_kwargs


def create_tag_orm(**kwargs) -> TagSaModel:
    """
    Create a TagSaModel ORM instance with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        TagSaModel ORM instance with comprehensive validation
    """
    tag_kwargs = create_tag_orm_kwargs(**kwargs)
    return TagSaModel(**tag_kwargs)


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
            create_tag(key="diet", value="low-calorie", type="meal"),
            create_tag(key="category", value="health", type="meal"),
            create_tag(key="style", value="healthy", type="meal")
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
            create_tag(key="difficulty", value="easy", type="meal"),
            create_tag(key="occasion", value="quick", type="meal"),
            create_tag(key="style", value="healthy", type="meal")
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
            create_tag(key="diet", value="vegetarian", type="meal"),
            create_tag(key="style", value="healthy", type="meal"),
            create_tag(key="category", value="lunch", type="meal")
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
            create_tag(key="diet", value="high-protein", type="meal"),
            create_tag(key="style", value="fitness", type="meal"),
            create_tag(key="occasion", value="post-workout", type="meal")
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
            create_tag(key="occasion", value="family", type="meal"),
            create_tag(key="difficulty", value="medium", type="meal"),
            create_tag(key="category", value="dinner", type="meal")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
    }
    return create_meal(**final_kwargs)


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
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="low-calorie", type="meal"),
            create_tag_orm(key="category", value="health", type="meal"),
            create_tag_orm(key="style", value="healthy", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
    final_kwargs = {
        "name": kwargs.get("name", "15-Minute Power Bowl"),
        "description": kwargs.get("description", "Fast preparation meal for busy schedules with maximum nutrition"),
        "notes": kwargs.get("notes", "Perfect for weeknight dinners or quick lunches. Pre-prep ingredients on weekends for even faster assembly."),
        "total_time": kwargs.get("total_time", 15),  # Quick preparation
        "calorie_density": kwargs.get("calorie_density", 300.0),
        "weight_in_grams": kwargs.get("weight_in_grams", 400),
        "like": kwargs.get("like", True),
        "tags": kwargs.get("tags", [
            create_tag_orm(key="difficulty", value="easy", type="meal"),
            create_tag_orm(key="occasion", value="quick", type="meal"),
            create_tag_orm(key="style", value="healthy", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "total_time", "calorie_density", "weight_in_grams", "like", "tags"]}
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
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="vegetarian", type="meal"),
            create_tag_orm(key="style", value="healthy", type="meal"),
            create_tag_orm(key="category", value="lunch", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
        "tags": kwargs.get("tags", [
            create_tag_orm(key="diet", value="high-protein", type="meal"),
            create_tag_orm(key="style", value="fitness", type="meal"),
            create_tag_orm(key="occasion", value="post-workout", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
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
        "tags": kwargs.get("tags", [
            create_tag_orm(key="occasion", value="family", type="meal"),
            create_tag_orm(key="difficulty", value="medium", type="meal"),
            create_tag_orm(key="category", value="dinner", type="meal")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["name", "description", "notes", "calorie_density", "carbo_percentage", "protein_percentage", "total_fat_percentage", "weight_in_grams", "total_time", "like", "tags"]}
    }
    return create_meal_orm(**final_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================

def get_meal_filter_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing meal filtering.
    
    Note: total_time is a computed property in the Meal domain object based on recipes,
    so it's not included in meal_kwargs. The filtering still works because the database
    has a total_time column that gets populated separately.
    
    Returns:
        List of test scenarios with meal_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "total_time_gte_match",
            "meal_kwargs": {"name": "Long Cooking Meal", "total_time": 50},
            "filter": {"total_time_gte": 45},
            "should_match": True,
            "description": "Meal with recipes having long total_time should match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_gte_no_match",
            "meal_kwargs": {"name": "Quick Meal", "total_time": 15},
            "filter": {"total_time_gte": 45},
            "should_match": False,
            "description": "Meal with recipes having short total_time should not match gte filter of 45min"
        },
        {
            "scenario_id": "total_time_lte_match",
            "meal_kwargs": {"name": "Quick Meal", "total_time": 15},
            "filter": {"total_time_lte": 45},
            "should_match": True,
            "description": "Meal with recipes having short total_time should match lte filter of 45min"
        },
        {
            "scenario_id": "calorie_density_gte_match",
            "meal_kwargs": {
                "name": "High Calorie Meal",
                "calorie_density": 2.0,
                "recipes": []
            },
            "filter": {"calorie_density_gte": 2.0},
            "should_match": True,
            "description": "High calorie density meal should match gte filter"
        },
        {
            "scenario_id": "like_filter_true",
            "meal_kwargs": {"like": True, "name": "Liked Meal"},
            "filter": {"like": True},
            "should_match": True,
            "description": "Liked meal should match like=True filter"
        },
        {
            "scenario_id": "like_filter_false",
            "meal_kwargs": {"like": False, "name": "Not Liked Meal"},
            "filter": {"like": True},
            "should_match": False,
            "description": "Not liked meal should not match like=True filter"
        },
        {
            "scenario_id": "author_id_match",
            "meal_kwargs": {"author_id": "test_author_123", "name": "Author Meal"},
            "filter": {"author_id": "test_author_123"},
            "should_match": True,
            "description": "Meal should match author_id filter"
        },
        {
            "scenario_id": "name_like_match",
            "meal_kwargs": {"name": "Delicious Pasta Meal"},
            "filter": {"name_like": "Pasta"},
            "should_match": True,
            "description": "Meal name containing 'Pasta' should match like filter"
        },
        {
            "scenario_id": "complex_filter_all_match",
            "meal_kwargs": {
                "like": True,
                "author_id": "complex_author",
                "name": "Complex Filter Test Meal",
                "total_time": 45
            },
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 60,
                "like": True,
                "author_id": "complex_author"
            },
            "should_match": True,
            "description": "Meal should match all filter conditions"
        },
        {
            "scenario_id": "complex_filter_partial_match",
            "meal_kwargs": {
                "like": True,
                "author_id": "complex_author",
                "name": "Partial Match Meal",
                "total_time": 61
            },
            "filter": {
                "total_time_gte": 30,
                "total_time_lte": 60,  # This may fail depending on recipes
                "like": True,
                "author_id": "complex_author"
            },
            "should_match": False,
            "description": "Meal should not match when one filter condition fails"
        }
    ]


def get_tag_filtering_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for testing complex tag filtering logic.
    
    Tests the complex AND/OR logic:
    - Different keys must ALL match (AND logic)
    - Multiple values for same key use OR logic
    - Exact key-value-author combinations
    
    Returns:
        List of tag filtering test scenarios
    """
    return [
        {
            "scenario_id": "single_tag_exact_match",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegetarian", "author_1")],
            "should_match": True,
            "description": "Single tag exact match should work"
        },
        {
            "scenario_id": "single_tag_no_match_value",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegan", "author_1")],
            "should_match": False,
            "description": "Different tag value should not match"
        },
        {
            "scenario_id": "single_tag_no_match_author",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [("diet", "vegetarian", "author_2")],
            "should_match": False,
            "description": "Different author_id should not match"
        },
        {
            "scenario_id": "multiple_values_same_key_or_logic",
            "meal_tags": [
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("cuisine", "italian", "author_1"),
                ("cuisine", "mexican", "author_1")  # OR with italian
            ],
            "should_match": True,
            "description": "Multiple values for same key should use OR logic"
        },
        {
            "scenario_id": "multiple_keys_and_logic",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_1")
            ],
            "should_match": True,
            "description": "Multiple different keys should use AND logic (all must match)"
        },
        {
            "scenario_id": "multiple_keys_and_logic_fail",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "mexican", "author_id": "author_1", "type": "meal"}  # Wrong value
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_1")  # This won't match
            ],
            "should_match": False,
            "description": "AND logic should fail if any key doesn't match"
        },
        {
            "scenario_id": "complex_combination",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_1", "type": "meal"},
                {"key": "difficulty", "value": "easy", "author_id": "author_1", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("diet", "vegan", "author_1"),  # OR with vegetarian
                ("cuisine", "italian", "author_1"),
                ("cuisine", "french", "author_1"),  # OR with italian
                ("difficulty", "easy", "author_1")
            ],
            "should_match": True,
            "description": "Complex AND/OR combination should work correctly"
        },
        {
            "scenario_id": "mixed_authors_same_meal",
            "meal_tags": [
                {"key": "diet", "value": "vegetarian", "author_id": "author_1", "type": "meal"},
                {"key": "cuisine", "value": "italian", "author_id": "author_2", "type": "meal"}
            ],
            "filter_tags": [
                ("diet", "vegetarian", "author_1"),
                ("cuisine", "italian", "author_2")  # Different author
            ],
            "should_match": True,
            "description": "Tags from different authors on same meal should work"
        }
    ]


def get_performance_test_scenarios() -> List[Dict[str, Any]]:
    """
    Get predefined scenarios for performance testing with dataset size expectations.
    
    Returns:
        List of performance test scenarios with entity counts and time limits
    """
    return [
        {
            "scenario_id": "small_dataset_basic_query",
            "entity_count": 100,
            "operation": "basic_query",
            "max_duration_seconds": 0.5,
            "description": "Basic query on 100 meals should complete in < 0.5s"
        },
        {
            "scenario_id": "medium_dataset_basic_query",
            "entity_count": 500,
            "operation": "basic_query",
            "max_duration_seconds": 1.0,
            "description": "Basic query on 500 meals should complete in < 1.0s"
        },
        {
            "scenario_id": "large_dataset_basic_query",
            "entity_count": 1000,
            "operation": "basic_query",
            "max_duration_seconds": 2.0,
            "description": "Basic query on 1000 meals should complete in < 2.0s"
        },
        {
            "scenario_id": "small_dataset_tag_filtering",
            "entity_count": 100,
            "operation": "tag_filtering",
            "max_duration_seconds": 1.0,
            "description": "Tag filtering on 100 meals should complete in < 1.0s"
        },
        {
            "scenario_id": "medium_dataset_tag_filtering",
            "entity_count": 500,
            "operation": "tag_filtering",
            "max_duration_seconds": 2.0,
            "description": "Tag filtering on 500 meals should complete in < 2.0s"
        },
        {
            "scenario_id": "large_dataset_tag_filtering",
            "entity_count": 1000,
            "operation": "tag_filtering",
            "max_duration_seconds": 3.0,
            "description": "Tag filtering on 1000 meals should complete in < 3.0s"
        },
        {
            "scenario_id": "complex_query_with_joins",
            "entity_count": 500,
            "operation": "complex_query",
            "max_duration_seconds": 2.5,
            "description": "Complex query with joins should complete in < 2.5s"
        },
        {
            "scenario_id": "bulk_insert_performance",
            "entity_count": 1000,
            "operation": "bulk_insert",
            "max_duration_seconds": 5.0,
            "max_per_entity_ms": 5,
            "description": "Bulk insert of 1000 meals should complete in < 5s (< 5ms per entity)"
        }
    ]


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP (DOMAIN & ORM)
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
                    tag = create_tag(key=key, value=value, author_id=author_id, type=tag_type)
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


def create_meals_with_tags_orm(count: int = 3, tags_per_meal: int = 2) -> List[MealSaModel]:
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
                    tag = create_tag_orm(key=key, value=value, author_id=author_id, type=tag_type)
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
                    tag = create_tag(key=key, value=value, author_id=author_id, type=tag_type)
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


def create_test_dataset_orm(meal_count: int = 100, tags_per_meal: int = 0) -> Dict[str, Any]:
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
                    tag = create_tag_orm(key=key, value=value, author_id=author_id, type=tag_type)
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
    
    return {
        "meals": meals,
        "all_tags": all_tags
    } 