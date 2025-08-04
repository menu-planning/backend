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

# Import domain factory functions
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_domain_factories import create_menu_meal_kwargs
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_orm_factories import create_menu_tag_orm
from tests.utils.counter_manager import get_next_menu_id, get_next_menu_meal_id

# ORM model imports
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_meal_sa_model import MenuMealSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel

# =============================================================================
# MENU DATA FACTORIES (ORM)
# =============================================================================

def create_menu_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create menu ORM kwargs with deterministic values.
    
    Similar to create_menu_kwargs but for ORM structure.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ORM menu creation parameters
    """
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    
    menu_counter = get_next_menu_id()
    
    final_kwargs = {
        "id": kwargs.get("id", f"menu_{menu_counter:03d}"),
        "author_id": kwargs.get("author_id", f"author_{(menu_counter % 5) + 1}"),
        "client_id": kwargs.get("client_id", f"client_{((menu_counter - 1) % 5) + 1:03d}"),
        "description": kwargs.get("description", f"Test menu description {menu_counter}"),
        "meals": kwargs.get("meals", []),  # List for ORM relationships
        "tags": kwargs.get("tags", []),  # List for ORM relationships
        "created_at": kwargs.get("created_at", base_time + timedelta(hours=menu_counter)),
        "updated_at": kwargs.get("updated_at", base_time + timedelta(hours=menu_counter, minutes=30)),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
    }
    
    return final_kwargs


def create_menu_orm(**kwargs) -> 'MenuSaModel':
    """
    Create a MenuSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MenuSaModel ORM instance
    """
    menu_kwargs = create_menu_orm_kwargs(**kwargs)
    return MenuSaModel(**menu_kwargs)


# =============================================================================
# MENU MEAL DATA FACTORIES (ORM)
# =============================================================================

def create_menu_meal_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create menu meal ORM kwargs with deterministic values.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with ORM menu meal creation parameters
    """
    # Use same logic as domain but add ORM-specific fields
    menu_meal_kwargs = create_menu_meal_kwargs(**kwargs)
    
    # Add ORM-specific fields
    menu_meal_counter = get_next_menu_meal_id()
    final_kwargs = {
        "meal_id": menu_meal_kwargs["meal_id"],
        "meal_name": menu_meal_kwargs["meal_name"],
        "week": menu_meal_kwargs["week"],
        "weekday": menu_meal_kwargs["weekday"],
        "meal_type": menu_meal_kwargs["meal_type"],
        "nutri_facts": menu_meal_kwargs["nutri_facts"],
        "hour": menu_meal_kwargs["hour"],
        "menu_id": kwargs.get("menu_id", f"menu_{((menu_meal_counter - 1) % 10) + 1:03d}"),  # Link to a menu
    }
    
    return final_kwargs


def create_menu_meal_orm(**kwargs) -> MenuMealSaModel:
    """
    Create a MenuMealSaModel ORM instance with deterministic data.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MenuMealSaModel ORM instance
    """
    menu_meal_kwargs = create_menu_meal_orm_kwargs(**kwargs)
    return MenuMealSaModel(**menu_meal_kwargs)


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS (ORM)
# =============================================================================

def create_weekly_menu_orm(**kwargs) -> MenuSaModel:
    """
    Create a menu ORM instance with meals for a full week.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        MenuSaModel with weekly meal planning and appropriate tags
    """
    # Create meals for each day of the week
    meals = []
    weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
    meal_types = ["café da manhã", "almoço", "jantar"]
    
    for day_idx, weekday in enumerate(weekdays):
        for meal_type_idx, meal_type in enumerate(meal_types):
            meal = create_menu_meal_orm(
                week=1,
                weekday=weekday,
                meal_type=meal_type,
                meal_name=f"{meal_type.title()} - {weekday}",
                hour=time(hour=8 + (meal_type_idx * 4), minute=0)
            )
            meals.append(meal)
    
    final_kwargs = {
        "description": kwargs.get("description", "Complete weekly menu with breakfast, lunch, and dinner"),
        "meals": kwargs.get("meals", meals),
        "tags": kwargs.get("tags", [
            create_menu_tag_orm(key="type", value="weekly", type="menu"),
            create_menu_tag_orm(key="complexity", value="moderate", type="menu")
        ]),
        **{k: v for k, v in kwargs.items() if k not in ["description", "meals", "tags"]}
    }
    return create_menu_orm(**final_kwargs)

# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_menus_with_tags_orm(count: int = 3, tags_per_menu: int = 2, meals_per_menu: int = 3) -> list[MenuSaModel]:
    """Create multiple ORM menus with various tag combinations and meals for testing"""
    menus = []
    
    # Similar logic as domain version but for ORM
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
                    tag = create_menu_tag_orm(key=key, value=value, author_id=author_id, type="menu")
                    unique_tags[tag_key] = tag
    
    unique_tag_list = list(unique_tags.values())
    
    for i in range(count):
        # Create tags for this menu
        tags = []
        if tags_per_menu > 0 and unique_tag_list:
            start_idx = (i * tags_per_menu) % len(unique_tag_list)
            for j in range(min(tags_per_menu, len(unique_tag_list))):
                tag_idx = (start_idx + j) % len(unique_tag_list)
                tags.append(unique_tag_list[tag_idx])
        
        # Create meals for this menu
        meals = []
        if meals_per_menu > 0:
            weekdays = ["Seg", "Ter", "Qua"][:meals_per_menu]
            for j, weekday in enumerate(weekdays):
                meal = create_menu_meal_orm(
                    week=1,
                    weekday=weekday,
                    meal_type="almoço",
                    meal_name=f"Test Meal {j+1} for Menu {i+1}"
                )
                meals.append(meal)
        
        menu_kwargs = create_menu_orm_kwargs()
        menu_kwargs["tags"] = tags
        menu_kwargs["meals"] = meals
        menu = create_menu_orm(**menu_kwargs)
        menus.append(menu)
    
    return menus