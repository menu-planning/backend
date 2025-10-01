from functools import lru_cache

from pydantic_settings import BaseSettings

class PaginationSettings(BaseSettings):

    """Centralized pagination limits per resource type."""
    
    # Lightweight resources
    TAGS: int = 500
    CLASSIFICATIONS: int = 300
    
    # Medium resources  
    PRODUCTS: int = 200
    CLIENTS: int = 150
    MENUS: int = 100
    
    # Heavy resources (with complex data)
    MEALS_AND_RECIPES: int = 100
    
    # Default fallback
    DEFAULT: int = 50
    MAX_ABSOLUTE: int = 1000


@lru_cache
def get_pagination_settings() -> PaginationSettings:
    """Return a cached `PaginationSettings` instance.

    Returns:
        A process-wide cached settings object.
    """
    return PaginationSettings()
