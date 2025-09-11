"""
Domain entities for test scenarios

This module contains domain entities used for integration testing of the
SaGenericRepository. These entities represent the business objects that
the repository will manage, providing a clean interface between the
domain layer and the persistence layer.

Features tested:
- Entity lifecycle management
- Attribute validation and updates
- Complex entity relationships
- Edge cases (circular references, self-referential)
"""

from src.contexts.seedwork.domain.entity import Entity


class MealTestEntity(Entity):
    """
    Test domain entity for meal

    Represents a meal in the domain layer with all business logic
    and validation rules. Used to test repository CRUD operations
    and complex queries.
    """

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(
            id=id,
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name
        self.author_id = kwargs.get("author_id")
        self.description = kwargs.get("description")
        self.total_time = kwargs.get("total_time")
        self.calorie_density = kwargs.get("calorie_density")
        self.preprocessed_name = kwargs.get("preprocessed_name")
        self.menu_id = kwargs.get("menu_id")
        self.notes = kwargs.get("notes")
        self.like = kwargs.get("like")
        self.weight_in_grams = kwargs.get("weight_in_grams")
        self.carbo_percentage = kwargs.get("carbo_percentage")
        self.protein_percentage = kwargs.get("protein_percentage")
        self.total_fat_percentage = kwargs.get("total_fat_percentage")
        self.image_url = kwargs.get("image_url")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class RecipeTestEntity(Entity):
    """
    Test domain entity for recipe

    Represents a recipe in the domain layer with relationships to meals,
    ingredients, and ratings. Used to test complex relationship handling
    and cascade operations.
    """

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(
            id=id,
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name
        self.author_id = kwargs.get("author_id")
        self.meal_id = kwargs.get("meal_id")
        self.instructions = kwargs.get("instructions")
        self.total_time = kwargs.get("total_time")
        self.preprocessed_name = kwargs.get("preprocessed_name")
        self.description = kwargs.get("description")
        self.utensils = kwargs.get("utensils")
        self.notes = kwargs.get("notes")
        self.privacy = kwargs.get("privacy")
        self.weight_in_grams = kwargs.get("weight_in_grams")
        self.calorie_density = kwargs.get("calorie_density")
        self.carbo_percentage = kwargs.get("carbo_percentage")
        self.protein_percentage = kwargs.get("protein_percentage")
        self.total_fat_percentage = kwargs.get("total_fat_percentage")
        self.image_url = kwargs.get("image_url")
        self.average_taste_rating = kwargs.get("average_taste_rating")
        self.average_convenience_rating = kwargs.get("average_convenience_rating")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class CircularTestEntityA(Entity):
    """
    Test domain entity for circular model A

    Used to test circular relationship handling where Entity A references
    Entity B, and Entity B has a list of Entity A references. This tests
    the repository's ability to handle complex relationship cycles without
    infinite loops.
    """

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(
            id=id,
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name
        self.b_ref_id = kwargs.get("b_ref_id")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class CircularTestEntityB(Entity):
    """
    Test domain entity for circular model B

    Complements TestCircularEntityA to form circular relationships.
    Used to test edge cases in relationship mapping and query building.
    """

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(
            id=id,
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class SelfReferentialTestEntity(Entity):
    """
    Test domain entity for self-referential model

    Represents entities that can reference themselves (parent-child relationships)
    and also have many-to-many relationships with other instances of the same
    type (friends). Used to test:

    - Self-referential foreign keys
    - Hierarchical data structures
    - Many-to-many self-relationships
    - Recursive query scenarios
    """

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(
            id=id,
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name
        self.level = kwargs.get("level", 0)
        self.parent_id = kwargs.get("parent_id")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class TagTestEntity(Entity):
    """
    Test domain entity for tags

    Simple entity used to test many-to-many relationships with meals and recipes.
    Includes unique constraints and basic validation.
    """

    def __init__(
        self, id: int, key: str, value: str, author_id: str, type: str, **kwargs
    ):
        super().__init__(
            id=str(id),
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.key = key
        self.value = value
        self.author_id = author_id
        self.type = type

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class RatingTestEntity(Entity):
    """
    Test domain entity for ratings

    Represents user ratings for recipes. Used to test:
    - Constraint validation (rating bounds)
    - Foreign key relationships
    - Aggregate calculations
    """

    def __init__(
        self,
        id: int,
        user_id: str,
        recipe_id: str,
        taste: int,
        convenience: int,
        **kwargs,
    ):
        super().__init__(
            id=str(id),
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.user_id = user_id
        self.recipe_id = recipe_id
        self.taste = taste
        self.convenience = convenience
        self.comment = kwargs.get("comment")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)


class IngredientTestEntity(Entity):
    """
    Test domain entity for ingredients

    Represents recipe ingredients. Used to test:
    - Ordered relationships (position-based)
    - Numeric constraints (positive quantities)
    - Optional relationships (product_id may be null)
    """

    def __init__(
        self, id: int, name: str, quantity: float, unit: str, recipe_id: str, **kwargs
    ):
        super().__init__(
            id=str(id),
            discarded=kwargs.get("discarded", False),
            version=kwargs.get("version", 1),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
        )
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.recipe_id = recipe_id
        self.position = kwargs.get("position", 0)
        self.product_id = kwargs.get("product_id")

        # Add any additional attributes dynamically
        for k, v in kwargs.items():
            if not hasattr(self, k) and k not in [
                "discarded",
                "version",
                "created_at",
                "updated_at",
            ]:
                setattr(self, k, v)

    def _update_properties(self, **kwargs):
        """Implementation of abstract method from Entity base class"""
        for k, v in kwargs.items():
            setattr(self, k, v)
