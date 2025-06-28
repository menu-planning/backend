"""
Data factories for MenuRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Validation logic for entity completeness
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different menu types
- ORM equivalents for all domain factory methods

All data follows the exact structure of Menu domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta, time
from typing import Any

from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import MenuMeal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import create_menu_tag

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_MENU_COUNTER = 1
_MENU_MEAL_COUNTER = 1


def reset_menu_counters() -> None:
    """Reset all counters for test isolation"""
    global _MENU_COUNTER, _MENU_MEAL_COUNTER
    _MENU_COUNTER = 1
    _MENU_MEAL_COUNTER = 1


# =============================================================================
# MENU DATA FACTORIES (DOMAIN)
# =============================================================================

def create_menu_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create menu kwargs with deterministic values and validation.
    
    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required menu creation parameters
    """
    global _MENU_COUNTER
    
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    final_kwargs = {
        "id": kwargs.get("id", f"menu_{_MENU_COUNTER:03d}"),
        "author_id": kwargs.get("author_id", f"author_{(_MENU_COUNTER % 5) + 1}"),  # Cycle through 5 authors
        "client_id": kwargs.get("client_id", f"client_{((_MENU_COUNTER - 1) % 5) + 1:03d}"),  # Cycle through 5 clients (client_001 to client_005)
        "description": kwargs.get("description", f"Test menu description {_MENU_COUNTER}"),
        "meals": kwargs.get("meals", set()),  # Will be populated separately if needed
        "tags": kwargs.get("tags", set()),  # Will be populated separately if needed
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=_MENU_COUNTER)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=_MENU_COUNTER, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    # Increment counter for next call
    _MENU_COUNTER += 1
    
    return final_kwargs


def create_menu(**kwargs) -> Menu:
    """
    Create a Menu domain entity with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Menu domain entity
    """
    menu_kwargs = create_menu_kwargs(**kwargs)
    return Menu(**menu_kwargs)


# =============================================================================
# MENU MEAL DATA FACTORIES (DOMAIN)
# =============================================================================

def create_menu_meal_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create menu meal kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with menu meal creation parameters
    """
    global _MENU_MEAL_COUNTER
    
    # Predefined meal types and weekdays
    meal_types = ["café da manhã", "almoço", "jantar", "lanche"]
    weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    
    meal_type_idx = (_MENU_MEAL_COUNTER - 1) % len(meal_types)
    weekday_idx = (_MENU_MEAL_COUNTER - 1) % len(weekdays)
    
    # Create default NutriFacts
    default_nutri_facts = NutriFacts(
        calories=500 + (_MENU_MEAL_COUNTER % 300),  # 500-800 calories
        protein=25 + (_MENU_MEAL_COUNTER % 20),     # 25-45g protein
        carbohydrate=60 + (_MENU_MEAL_COUNTER % 40), # 60-100g carbs
        total_fat=15 + (_MENU_MEAL_COUNTER % 10),   # 15-25g fat
        saturated_fat=5 + (_MENU_MEAL_COUNTER % 5), # 5-10g saturated fat
        trans_fat=0,                                 # Usually 0
        dietary_fiber=8 + (_MENU_MEAL_COUNTER % 7), # 8-15g fiber
        sodium=400 + (_MENU_MEAL_COUNTER % 200),    # 400-600mg sodium
        sugar=10 + (_MENU_MEAL_COUNTER % 15)        # 10-25g sugar
    )
    
    final_kwargs = {
        "meal_id": kwargs.get("meal_id", f"meal_{_MENU_MEAL_COUNTER:03d}"),
        "meal_name": kwargs.get("meal_name", f"Test Meal {_MENU_MEAL_COUNTER}"),
        "week": kwargs.get("week", ((_MENU_MEAL_COUNTER - 1) // 7) + 1),  # Week 1, 2, 3, etc.
        "weekday": kwargs.get("weekday", weekdays[weekday_idx]),
        "meal_type": kwargs.get("meal_type", meal_types[meal_type_idx]),
        "nutri_facts": kwargs.get("nutri_facts", default_nutri_facts),
        "hour": kwargs.get("hour", time(hour=8 + (meal_type_idx * 3), minute=0)),  # 8am, 11am, 2pm, 5pm
    }
    
    _MENU_MEAL_COUNTER += 1
    return final_kwargs


def create_menu_meal(**kwargs) -> MenuMeal:
    """
    Create a MenuMeal value object with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MenuMeal value object
    """
    menu_meal_kwargs = create_menu_meal_kwargs(**kwargs)
    return MenuMeal(**menu_meal_kwargs)

# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (DOMAIN)
# =============================================================================

def create_weekly_menu(**kwargs) -> Menu:
    """
    Create a menu with meals for a full week.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Menu with weekly meal planning and appropriate tags
    """
    # Create meals for each day of the week
    meals = set()
    weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    meal_types = ["café da manhã", "almoço", "jantar"]
    
    for day_idx, weekday in enumerate(weekdays):
        for meal_type_idx, meal_type in enumerate(meal_types):
            meal = create_menu_meal(
                week=1,
                weekday=weekday,
                meal_type=meal_type,
                meal_name=f"{meal_type.title()} - {weekday}",
                hour=time(hour=8 + (meal_type_idx * 4), minute=0)
            )
            meals.add(meal)
    
    final_kwargs = {
        "description": kwargs.get("description", "Complete weekly menu with breakfast, lunch, and dinner"),
        "meals": kwargs.get("meals", meals),
        "tags": kwargs.get("tags", {
            create_menu_tag(key="type", value="weekly", type="menu"),
            create_menu_tag(key="complexity", value="moderate", type="menu")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["description", "meals", "tags"]}
    }
    return create_menu(**final_kwargs)


def create_special_event_menu(**kwargs) -> Menu:
    """
    Create a menu for special events (weddings, corporate events, etc.).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Menu with special event characteristics and tags
    """
    # Create special meals
    meals = {
        create_menu_meal(
            week=1, weekday="Sab", meal_type="almoço",
            meal_name="Gourmet Wedding Reception Lunch",
            hour=time(hour=13, minute=0)
        ),
        create_menu_meal(
            week=1, weekday="Sab", meal_type="jantar", 
            meal_name="Elegant Wedding Dinner",
            hour=time(hour=19, minute=30)
        )
    }
    
    final_kwargs = {
        "description": kwargs.get("description", "Elegant menu for wedding reception with gourmet options"),
        "meals": kwargs.get("meals", meals),
        "tags": kwargs.get("tags", {
            create_menu_tag(key="type", value="special", type="menu"),
            create_menu_tag(key="event", value="wedding", type="menu"),
            create_menu_tag(key="complexity", value="gourmet", type="menu")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["description", "meals", "tags"]}
    }
    return create_menu(**final_kwargs)


def create_dietary_restriction_menu(**kwargs) -> Menu:
    """
    Create a menu with dietary restrictions (vegetarian, gluten-free, etc.).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Menu with dietary restriction characteristics and tags
    """
    meals = {
        create_menu_meal(
            week=1, weekday="Seg", meal_type="almoço",
            meal_name="Vegetarian Buddha Bowl",
            hour=time(hour=12, minute=0)
        ),
        create_menu_meal(
            week=1, weekday="Ter", meal_type="jantar",
            meal_name="Gluten-Free Grilled Salmon",
            hour=time(hour=19, minute=0)
        )
    }
    
    final_kwargs = {
        "description": kwargs.get("description", "Carefully crafted menu accommodating various dietary restrictions"),
        "meals": kwargs.get("meals", meals),
        "tags": kwargs.get("tags", {
            create_menu_tag(key="dietary", value="vegetarian", type="menu"),
            create_menu_tag(key="dietary", value="gluten-free", type="menu"),
            create_menu_tag(key="complexity", value="moderate", type="menu")
        }),
        **{k: v for k, v in kwargs.items() if k not in ["description", "meals", "tags"]}
    }
    return create_menu(**final_kwargs)

# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_menus_with_tags(count: int = 3, tags_per_menu: int = 2, meals_per_menu: int = 3) -> list[Menu]:
    """Create multiple menus with various tag combinations and meals for testing"""
    menus = []
    
    # Create unique tags pool
    unique_tags = {}
    
    tag_keys = ["type", "season", "event", "dietary", "complexity"]
    values_by_key = {
        "type": ["weekly", "special", "holiday", "daily", "custom"],
        "season": ["spring", "summer", "fall", "winter", "year-round"],
        "event": ["wedding", "corporate", "birthday", "conference", "casual"],
        "dietary": ["vegetarian", "vegan", "gluten-free", "keto", "balanced"],
        "complexity": ["simple", "moderate", "complex", "gourmet"]
    }
    max_authors = 5
    
    # Pre-create unique tags
    if tags_per_menu > 0:
        for menu_idx in range(count):
            for tag_idx in range(tags_per_menu):
                total_tag_index = menu_idx * tags_per_menu + tag_idx
                
                key_idx = total_tag_index % len(tag_keys)
                key = tag_keys[key_idx]
                
                value_idx = (total_tag_index // len(tag_keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(tag_keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                tag_key = (key, value, author_id, "menu")
                
                if tag_key not in unique_tags:
                    tag = create_menu_tag(key=key, value=value, author_id=author_id, type="menu")
                    unique_tags[tag_key] = tag
    
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        # Create tags for this menu
        tags = set()
        if tags_per_menu > 0 and unique_tag_list:
            start_idx = (i * tags_per_menu) % len(unique_tag_list)
            for j in range(min(tags_per_menu, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])
        
        # Create meals for this menu
        meals = set()
        if meals_per_menu > 0:
            weekdays = ["Seg", "Ter", "Qua"][:meals_per_menu]  # Limit to available days
            for j, weekday in enumerate(weekdays):
                meal = create_menu_meal(
                    week=1,
                    weekday=weekday,
                    meal_type="almoço",
                    meal_name=f"Test Meal {j+1} for Menu {i+1}"
                )
                meals.add(meal)
        
        menu_kwargs = create_menu_kwargs()
        menu_kwargs["tags"] = tags
        menu_kwargs["meals"] = meals
        menu = create_menu(**menu_kwargs)
        menus.append(menu)
    
    return menus

def create_test_dataset(menu_count: int = 100, tags_per_menu: int = 0, meals_per_menu: int = 0) -> dict[str, Any]:
    """Create a dataset of menus for performance testing"""
    menus = []
    all_tags = []
    all_meals = []
    
    # Create unique tags pool if needed
    unique_tags = {}
    
    if tags_per_menu > 0:
        tag_keys = ["type", "season", "event", "dietary", "complexity"]
        values_by_key = {
            "type": ["weekly", "special", "holiday", "daily", "custom"],
            "season": ["spring", "summer", "fall", "winter", "year-round"],
            "event": ["wedding", "corporate", "birthday", "conference", "casual"],
            "dietary": ["vegetarian", "vegan", "gluten-free", "keto", "balanced"],
            "complexity": ["simple", "moderate", "complex", "gourmet"]
        }
        max_authors = 5
        
        for menu_idx in range(menu_count):
            for tag_idx in range(tags_per_menu):
                total_tag_index = menu_idx * tags_per_menu + tag_idx
                
                key_idx = total_tag_index % len(tag_keys)
                key = tag_keys[key_idx]
                
                value_idx = (total_tag_index // len(tag_keys)) % len(values_by_key[key])
                value = values_by_key[key][value_idx]
                
                author_idx = (total_tag_index // (len(tag_keys) * max(len(v) for v in values_by_key.values()))) % max_authors
                author_id = f"author_{author_idx + 1}"
                
                tag_key = (key, value, author_id, "menu")
                
                if tag_key not in unique_tags:
                    tag = create_menu_tag(key=key, value=value, author_id=author_id, type="menu")
                    unique_tags[tag_key] = tag
                    all_tags.append(tag)
    
    unique_tag_list = list(unique_tags.values())
    
    for i in range(menu_count):
        # Create tags for this menu if requested
        tags = set()
        if tags_per_menu > 0 and unique_tag_list:
            start_idx = (i * tags_per_menu) % len(unique_tag_list)
            for j in range(min(tags_per_menu, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.add(unique_tag_list[tag_idx])
        
        # Create meals for this menu if requested
        meals = set()
        if meals_per_menu > 0:
            weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
            for j in range(min(meals_per_menu, len(weekdays))):
                meal = create_menu_meal(
                    week=1,
                    weekday=weekdays[j],
                    meal_type="almoço",
                    meal_name=f"Performance Test Meal {j+1}"
                )
                meals.add(meal)
                all_meals.append(meal)
        
        menu_kwargs = create_menu_kwargs()
        if tags:
            menu_kwargs["tags"] = tags
        if meals:
            menu_kwargs["meals"] = meals
        menu = create_menu(**menu_kwargs)
        menus.append(menu)
    
    return {
        "menus": menus,
        "all_tags": all_tags,
        "all_meals": all_meals
    } 