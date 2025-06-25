"""
TagFilterMixin for repository tag filtering functionality.

This mixin provides reusable tag filtering methods that can be used across different repository
implementations. It standardizes the complex logic needed for filtering entities by tags with
proper AND/OR logic handling.

The mixin is designed to work with SQLAlchemy models that have many-to-many relationships with
TagSaModel entities.
"""

from itertools import groupby
from typing import Any, TypeVar, Type, List, Tuple

from sqlalchemy import ColumnElement, and_
from sqlalchemy.orm import InstrumentedAttribute

from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import FilterNotAllowedError

# Type variable for SQLAlchemy model types
T = TypeVar('T')


class TagFilterMixin:
    """
    Mixin class providing reusable tag filtering functionality for repositories.
    
    This mixin standardizes the complex tag filtering logic that was previously duplicated
    across multiple repository implementations (MealRepository, RecipeRepository, MenuRepository).
    
    **Requirements for using this mixin:**
    
    1. The repository class must define a `tag_model` class attribute pointing to TagSaModel
    2. The SA model must have a `tags` relationship attribute that returns a list of TagSaModel
    3. The SA model must support SQLAlchemy `any()` operations on the tags relationship
    
    **Example usage:**
    
    ```python
    class MealRepository(TagFilterMixin, SaGenericRepository):
        tag_model = TagSaModel
        
        async def query(self, filter: dict, starting_stmt: Select = None):
            if "tags" in filter:
                tags = filter.pop("tags")
                self.validate_tag_format(tags)
                tag_condition = self.build_tag_filter(MealSaModel, tags, "meal")
                # Apply condition to your query...
    ```
    
    **Tag Format:**
    
    Tags must be provided as a list of 3-tuples: `[(key, value, author_id), ...]`
    
    **Filtering Logic:**
    
    - Tags with the same key are combined with OR logic (any value matches)
    - Tags with different keys are combined with AND logic (all keys must match)
    - Each tag tuple must have matching author_id and correct type
    
    **Example:**
    
    ```python
    tags = [
        ("cuisine", "italian", "user123"),
        ("cuisine", "mexican", "user123"),  # OR with above
        ("difficulty", "easy", "user123"),   # AND with cuisine group
    ]
    # Result: (cuisine=italian OR cuisine=mexican) AND difficulty=easy
    ```
    """
    
    # Class attribute that must be set by implementing classes
    tag_model: Type[TagSaModel] = TagSaModel
    
    def validate_tag_format(self, tags: Any) -> None:
        """
        Validate that the provided tags are in the correct format.
        
        Args:
            tags: The tags to validate. Must be a list of 3-tuples.
            
        Raises:
            FilterNotAllowedError: If the tag format is invalid.
            
        **Valid format:**
        - Must be a list
        - Each item must be a tuple with exactly 3 elements
        - All elements in each tuple must be strings
        - Format: [(key, value, author_id), ...]
        
        **Examples:**
        
        Valid:
        ```python
        [("cuisine", "italian", "user123")]
        [("cuisine", "italian", "user123"), ("difficulty", "easy", "user123")]
        ```
        
        Invalid:
        ```python
        "cuisine:italian"  # Not a list
        [("cuisine", "italian")]  # Missing author_id
        [("cuisine", 123, "user123")]  # Non-string value
        ```
        """
        if not isinstance(tags, list):
            raise FilterNotAllowedError(
                f"Tags must be a list, got {type(tags).__name__}. "
                f"Expected format: [(key, value, author_id), ...]"
            )
        
        for i, tag in enumerate(tags):
            if not isinstance(tag, tuple):
                raise FilterNotAllowedError(
                    f"Tag at index {i} must be a tuple, got {type(tag).__name__}. "
                    f"Expected format: (key, value, author_id)"
                )
            
            if len(tag) != 3:
                raise FilterNotAllowedError(
                    f"Tag at index {i} must have exactly 3 elements (key, value, author_id), "
                    f"got {len(tag)} elements: {tag}"
                )
            
            key, value, author_id = tag
            for j, component in enumerate([key, value, author_id]):
                if not isinstance(component, str):
                    component_names = ["key", "value", "author_id"]
                    raise FilterNotAllowedError(
                        f"Tag at index {i}: {component_names[j]} must be a string, "
                        f"got {type(component).__name__}: {component}"
                    )
    
    def build_tag_filter(
        self, 
        sa_model_class: Type[T], 
        tags: List[Tuple[str, str, str]], 
        tag_type: str
    ) -> ColumnElement[bool]:
        """
        Build a SQLAlchemy filter condition for tag matching.
        
        This method implements the complex tag filtering logic:
        - Groups tags by key 
        - Creates OR conditions for multiple values within the same key
        - Creates AND conditions between different key groups
        - Ensures proper author_id and type matching
        
        Args:
            sa_model_class: The SQLAlchemy model class (e.g., MealSaModel)
            tags: List of tag tuples in format [(key, value, author_id), ...]
            tag_type: The type of tags to filter (e.g., "meal", "recipe", "menu")
            
        Returns:
            SQLAlchemy condition that can be used in WHERE clauses
            
        Raises:
            FilterNotAllowedError: If the SA model doesn't have a tags relationship
            
        **Example usage:**
        
        ```python
        tags = [
            ("cuisine", "italian", "user123"),
            ("cuisine", "mexican", "user123"),
            ("difficulty", "easy", "user123")
        ]
        condition = self.build_tag_filter(MealSaModel, tags, "meal")
        stmt = stmt.where(condition)
        ```
        
        **Generated SQL logic:**
        ```sql
        -- For the above example:
        EXISTS (
            SELECT 1 FROM tags 
            WHERE tags.key = 'cuisine' 
            AND tags.value IN ('italian', 'mexican')
            AND tags.author_id = 'user123'
            AND tags.type = 'meal'
        ) 
        AND EXISTS (
            SELECT 1 FROM tags 
            WHERE tags.key = 'difficulty' 
            AND tags.value = 'easy'
            AND tags.author_id = 'user123' 
            AND tags.type = 'meal'
        )
        ```
        """
        # Validate that the model has a tags relationship
        if not hasattr(sa_model_class, 'tags'):
            raise FilterNotAllowedError(
                f"Model {sa_model_class.__name__} does not have a 'tags' relationship. "
                f"TagFilterMixin requires models to have a many-to-many relationship with TagSaModel."
            )
        
        # Handle empty tags list
        if not tags:
            # Return a condition that's always True (no filtering)
            return True  # type: ignore
        
        # Sort tags by key for consistent groupby behavior
        tags_sorted = sorted(tags, key=lambda t: t[0])
        conditions = []
        
        # Group tags by key and create AND logic between different keys
        for key, group in groupby(tags_sorted, key=lambda t: t[0]):
            group_list = list(group)
            # All tags in a group should have the same author_id
            author_id = group_list[0][2]
            
            # Extract all values for this key (creates OR logic within key group)
            values = [t[1] for t in group_list]
            
            # Create EXISTS condition using SQLAlchemy any()
            # This generates: EXISTS(SELECT 1 FROM tags WHERE key=X AND value IN (Y) AND author_id=Z AND type=W)
            tags_relationship: InstrumentedAttribute = getattr(sa_model_class, 'tags')
            condition = tags_relationship.any(
                and_(
                    self.tag_model.key == key,
                    self.tag_model.value.in_(values),
                    self.tag_model.author_id == author_id,
                    self.tag_model.type == tag_type,
                )
            )
            conditions.append(condition)
        
        # Combine all key-group conditions with AND logic
        # This means ALL key groups must match (each key group can have OR within it)
        return and_(*conditions)
    
    def build_negative_tag_filter(
        self, 
        sa_model_class: Type[T], 
        tags: List[Tuple[str, str, str]], 
        tag_type: str
    ) -> ColumnElement[bool]:
        """
        Build a SQLAlchemy filter condition for tag exclusion (tags_not_exists).
        
        This method creates conditions to exclude entities that have any of the specified tags.
        It's the logical negation of the positive tag filter.
        
        Args:
            sa_model_class: The SQLAlchemy model class (e.g., MealSaModel)
            tags: List of tag tuples to exclude in format [(key, value, author_id), ...]
            tag_type: The type of tags to filter (e.g., "meal", "recipe", "menu")
            
        Returns:
            SQLAlchemy condition that excludes entities with the specified tags
            
        **Example usage:**
        
        ```python
        tags_to_exclude = [
            ("cuisine", "spicy", "user123"),
            ("difficulty", "hard", "user123")
        ]
        condition = self.build_negative_tag_filter(MealSaModel, tags_to_exclude, "meal")
        stmt = stmt.where(condition)
        ```
        
        **Generated SQL logic:**
        ```sql
        -- Excludes entities that have ANY of the specified tag combinations
        NOT EXISTS (
            SELECT 1 FROM tags 
            WHERE (
                (tags.key = 'cuisine' AND tags.value = 'spicy') OR
                (tags.key = 'difficulty' AND tags.value = 'hard')
            )
            AND tags.author_id = 'user123'
            AND tags.type = 'meal'
        )
        ```
        
        **Note:** This is different from the positive filter logic. For exclusion,
        we typically want to exclude entities that have ANY of the specified tags,
        not ALL of them.
        """
        # Validate that the model has a tags relationship
        if not hasattr(sa_model_class, 'tags'):
            raise FilterNotAllowedError(
                f"Model {sa_model_class.__name__} does not have a 'tags' relationship. "
                f"TagFilterMixin requires models to have a many-to-many relationship with TagSaModel."
            )
        
        # Handle empty tags list
        if not tags:
            # Return a condition that's always True (no filtering)
            return True  # type: ignore
        
        # For negative filtering, we simply negate the positive condition
        # This creates NOT EXISTS(...) logic
        positive_condition = self.build_tag_filter(sa_model_class, tags, tag_type)
        return ~positive_condition 