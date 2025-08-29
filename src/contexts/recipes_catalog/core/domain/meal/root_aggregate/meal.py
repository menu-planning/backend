from __future__ import annotations

import uuid
from functools import cached_property
from typing import TYPE_CHECKING, Any

from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.events.meal_deleted import (
    MealDeleted,
)
from src.contexts.recipes_catalog.core.domain.meal.events.updated_attr_that_reflect_on_menu import (
    UpdatedAttrOnMealThatReflectOnMenu,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.macro_division import (
    MacroDivision,
)
from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    RecipeMustHaveCorrectMealIdAndAuthorId,
)
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.logging.logger import logger

if TYPE_CHECKING:
    from datetime import datetime

    from src.contexts.seedwork.shared.domain.event import Event


def event_to_updated_menu_on_meal_creation(
    menu_id: str | None,
    meal_id: str,
    message: str,
) -> list[Event]:
    if not menu_id:
        return []
    return [
        UpdatedAttrOnMealThatReflectOnMenu(
            menu_id=menu_id, meal_id=meal_id, message=message
        )
    ]


class Meal(Entity):
    def __init__(
        self,
        *,
        entity_id: str,
        name: str,
        author_id: str,
        menu_id: str | None = None,
        recipes: list[_Recipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        like: bool | None = None,
        image_url: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Meal."""
        super().__init__(
            entity_id=entity_id,
            discarded=discarded,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._author_id = author_id
        self._name = name
        self._menu_id = menu_id
        self._recipes = recipes if recipes else []
        self._tags = tags if tags else set()
        self._description = description
        self._notes = notes
        self._like = like
        self._image_url = image_url
        self.events: list[Event] = []

    @classmethod
    def create_meal(
        cls,
        *,
        name: str,
        author_id: str,
        meal_id: str,
        menu_id: str,
        recipes: list[_Recipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        image_url: str | None = None,
    ) -> Meal:
        new_recipes = []
        if recipes:
            for recipe in recipes:
                copy = _Recipe.copy_recipe(
                    recipe=recipe, user_id=author_id, meal_id=meal_id
                )
                new_recipes.append(copy)
        else:
            recipes = []
        meal = cls(
            entity_id=meal_id,
            name=name,
            author_id=author_id,
            menu_id=menu_id,
            recipes=new_recipes,
            tags=tags,
            description=description,
            notes=notes,
            image_url=image_url,
        )
        meal.events = event_to_updated_menu_on_meal_creation(
            menu_id, meal_id, "Created new meal"
        )
        return meal

    @classmethod
    def copy_meal(
        cls,
        meal: Meal,
        id_of_user_coping_meal: str,
        id_of_target_menu: str | None = None,
    ) -> Meal:
        name = meal.name
        description = meal.description
        notes = meal.notes
        image_url = meal.image_url
        meal_id = uuid.uuid4().hex
        author_id = id_of_user_coping_meal
        new_recipes = []
        new_tags = []
        for r in meal.recipes:
            copy = _Recipe.copy_recipe(
                recipe=r, user_id=id_of_user_coping_meal, meal_id=meal_id
            )
            new_recipes.append(copy)
        for t in meal.tags:
            copy = Tag(
                key=t.key, value=t.value, author_id=id_of_user_coping_meal, type=t.type
            )
            new_tags.append(copy)
        meal = cls(
            entity_id=meal_id,
            author_id=author_id,
            name=name,
            menu_id=id_of_target_menu,
            recipes=new_recipes,
            description=description,
            tags=set(new_tags),
            notes=notes,
            image_url=image_url,
        )
        meal.events = event_to_updated_menu_on_meal_creation(
            id_of_target_menu, meal_id, "Copied meal"
        )
        return meal

    def add_event_to_updated_menu(self, message: str = "") -> None:
        """Add or update an event indicating this meal affects its menu.

        This method ensures only one UpdatedAttrOnMealThatReflectOnMenu event exists
        per meal, concatenating messages to avoid event proliferation while preserving
        the audit trail of changes.

        Args:
            message: Description of the change that affects the menu
        """
        if not self.menu_id:
            return

        # Find any existing UpdatedAttrOnMealThatReflectOnMenu event
        existing_event = None
        for event in self.events:
            if isinstance(event, UpdatedAttrOnMealThatReflectOnMenu):
                existing_event = event
                break

        # Build new message, avoiding duplication
        new_message = message.strip() if message else ""

        if existing_event and existing_event.message:
            existing_messages = [
                msg.strip() for msg in existing_event.message.split(";") if msg.strip()
            ]
            # Only add new message if it's not already present
            if new_message and new_message not in existing_messages:
                existing_messages.append(new_message)
                new_message = "; ".join(existing_messages)
            else:
                new_message = existing_event.message

        # Create new event
        event = UpdatedAttrOnMealThatReflectOnMenu(
            menu_id=self.menu_id, meal_id=self.id, message=new_message
        )

        # Replace existing event or add new one
        if existing_event:
            self.events[self.events.index(existing_event)] = event
        else:
            self.events.append(event)

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    def _set_name(self, value: str) -> None:
        """Protected setter for name. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self.add_event_to_updated_menu(f"Updated meal name to: {value}")
            self._increment_version()

    @property
    def menu_id(self) -> str | None:
        self._check_not_discarded()
        return self._menu_id

    def _set_menu_id(self, value: str | None) -> None:
        """Protected setter for menu_id. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._menu_id != value:
            self._menu_id = value
            self._increment_version()

    @property
    def products_ids(self) -> set[str]:
        self._check_not_discarded()
        products_ids = set()
        for recipe in self.recipes:
            for ingredient in recipe.ingredients:
                if ingredient.product_id:
                    products_ids.add(ingredient.product_id)
        return products_ids

    @property
    def total_time(self) -> int | None:
        self._check_not_discarded()
        times = [recipe.total_time for recipe in self.recipes] if self.recipes else []
        times = [time for time in times if time]
        return max(times) if times else None

    @property
    def recipes(self) -> list[_Recipe]:
        self._check_not_discarded()
        return [recipe for recipe in self._recipes if not recipe.discarded]

    def _set_recipes(self, value: list[_Recipe]) -> None:
        """Protected setter for recipes. Can only be called through update_properties."""
        self._check_not_discarded()
        if value is None:
            value = []

        # Validate that all recipes satisfy business rules before proceeding
        for recipe in value:
            self.check_rule(
                RecipeMustHaveCorrectMealIdAndAuthorId(recipe=recipe, meal=self),
            )

        # Mark old recipes not in the new list as discarded
        for recipe in self._recipes:
            if recipe not in value:
                logger.debug(f"Recipe {recipe.id} not in value and will be discarded.")
                recipe.delete()

        # Set the new recipes and validate business rules
        self._recipes = value

        # Validate business rules on all non-discarded recipes
        for recipe in [r for r in self._recipes if not r.discarded]:
            self.check_rule(
                RecipeMustHaveCorrectMealIdAndAuthorId(recipe=recipe, meal=self),
            )

        self._increment_version()
        # Invalidate nutrition-related caches when recipes change
        self._invalidate_caches("nutri_facts")

    def get_recipe_by_id(self, recipe_id: str) -> _Recipe | None:
        self._check_not_discarded()
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe

    def copy_recipes(self, recipes: list[_Recipe]) -> None:
        self._check_not_discarded()
        for recipe in recipes:
            copied = _Recipe.copy_recipe(
                recipe=recipe, user_id=self.author_id, meal_id=self.id
            )
            self._recipes.append(copied)
        self.add_event_to_updated_menu("Copied recipes to meal")
        self._increment_version()

    @property
    def recipes_tags(self) -> set[Tag]:
        self._check_not_discarded()
        tags = set()
        for recipe in self.recipes:
            for tag in recipe.tags:
                tags.add(tag)
        return tags

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    def _set_tags(self, value: set[Tag]) -> None:
        """Protected setter for tags. Can only be called through update_properties."""
        self._check_not_discarded()
        if value is None:
            value = set()
        for tag in value:
            Meal.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Calculate the aggregated nutritional facts for all recipes in this meal.

        This property sums the nutritional facts from all recipes in the meal,
        using instance-level caching to avoid repeated computation. The cache is
        automatically invalidated when the recipes collection is modified.

        Returns:
            NutriFacts | None: Aggregated nutritional facts from all recipes,
            or None if no recipes have nutritional data

        Cache invalidation triggers:
            - recipes setter: When the recipes collection is replaced
            - create_recipe(): When a new recipe is added to the meal
            - delete_recipe(): When a recipe is removed from the meal
            - copy_recipe(): When a recipe is copied to the meal
            - update_recipes(): When recipe properties are updated

        Performance: O(n) computation where n = number of recipes with nutri_facts,
        O(1) on subsequent accesses until cache invalidation.

        Notes:
            - Only recipes with non-None nutri_facts contribute to the sum
            - Returns None if no recipes have nutritional data
        """
        self._check_not_discarded()
        nutri_facts = NutriFacts()
        has_any_nutri_facts = False
        for recipe in self.recipes:
            if recipe.nutri_facts is not None:
                nutri_facts += recipe.nutri_facts
                has_any_nutri_facts = True
        return nutri_facts if has_any_nutri_facts else None

    @property
    def calorie_density(self) -> float | None:
        self._check_not_discarded()
        if (
            self.nutri_facts
            and self.nutri_facts.calories.value is not None
            and self.weight_in_grams
        ):
            return (self.nutri_facts.calories.value / self.weight_in_grams) * 100
        return None

    @property
    def macro_division(self) -> MacroDivision | None:
        """Calculate the macronutrient distribution for the entire meal.

        This property computes the percentage breakdown of carbohydrates, proteins,
        and fats based on the meal's aggregated nutritional facts. Always computed
        fresh to avoid cache dependency complexity.

        Returns:
            MacroDivision | None: Object containing carbohydrate, protein, and fat
            percentages (totaling 100%), or None if insufficient nutritional data

        Performance: Lightweight computation based on cached nutri_facts.
        Fast enough to not require its own caching layer.

        Notes:
            - Returns None if nutri_facts is None (no nutritional data)
            - Returns None if any macro values (carbs, protein, fat) are None
            - Returns None if total macros sum to zero (division by zero protection)
            - Not cached to keep dependency chain simple - depends on cached nutri_facts
        """
        self._check_not_discarded()
        if not self.nutri_facts:
            return None

        carb = self.nutri_facts.carbohydrate.value
        protein = self.nutri_facts.protein.value
        fat = self.nutri_facts.total_fat.value

        if carb is None or protein is None or fat is None:
            return None

        denominator = carb + protein + fat
        if denominator == 0:
            return None

        return MacroDivision(
            carbohydrate=(carb / denominator) * 100,
            protein=(protein / denominator) * 100,
            fat=(fat / denominator) * 100,
        )

    @property
    def carbo_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.carbohydrate
        return None

    @property
    def protein_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.protein
        return None

    @property
    def total_fat_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.fat
        return None

    @property
    def weight_in_grams(self) -> int:
        self._check_not_discarded()
        return sum(
            [
                recipe.weight_in_grams
                for recipe in self.recipes
                if recipe.weight_in_grams
            ]
        )

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    def _set_description(self, value: str | None) -> None:
        """Protected setter for description. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def notes(self) -> str | None:
        self._check_not_discarded()
        return self._notes

    def _set_notes(self, value: str | None) -> None:
        """Protected setter for notes. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def like(self) -> bool | None:
        self._check_not_discarded()
        return self._like

    def _set_like(self, value: bool | None) -> None:
        """Protected setter for like. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._like != value:
            self._like = value
            self._increment_version()

    @property
    def image_url(self) -> str | None:
        self._check_not_discarded()
        return self._image_url

    def _set_image_url(self, value: str | None) -> None:
        """Protected setter for image_url. Can only be called through update_properties."""
        self._check_not_discarded()
        if self._image_url != value:
            self._image_url = value
            self._increment_version()

    def delete(self) -> None:
        self._check_not_discarded()
        for recipe in self._recipes:
            recipe.delete()
        if self.menu_id:
            self.events.append(
                MealDeleted(
                    meal_id=self.id,
                    menu_id=self.menu_id,
                )
            )
        self._discard()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        """
        Identity-based equality for domain entities.
        Two Meal entities are equal if they have the same ID.
        """
        if not isinstance(other, Meal):
            return NotImplemented
        return self._id == other._id

    def has_same_content(self, other: Meal) -> bool:
        """
        Compare two Meal instances for content equality (all attributes).

        This method uses reflection to dynamically discover and compare:
        1. All instance attributes from __dict__
        2. All properties and descriptors
        3. All public attributes from dir() that aren't methods

        It's designed to work regardless of changes to the Meal implementation,
        as it doesn't hardcode specific attribute names.

        Args:
            other: Meal instance to compare against

        Returns:
            bool: True if all content is identical, False otherwise
        """
        if not isinstance(other, Meal):
            raise TypeError(f"Cannot compare Meal with {type(other)}")

        # Quick identity check
        if self is other:
            return True

        # Get all attributes to compare using reflection
        attributes_to_compare = self._discover_comparable_attributes()

        logger.debug(
            f"Comparing Meal content: {self.id} vs {other.id}, attributes: {sorted(attributes_to_compare)}"
        )

        # Compare each discovered attribute
        differences_found = []
        for attr_name in attributes_to_compare:
            try:
                self_value = self._get_attribute_value(attr_name)
                other_value = other._get_attribute_value(attr_name)

                if not self._compare_values(self_value, other_value):
                    differences_found.append(
                        f"{attr_name}: {self_value!r} != {other_value!r}"
                    )
            except (AttributeError, Exception) as e:
                # Skip attributes that can't be accessed on either object
                logger.debug(f"Skipping attribute {attr_name} due to access error: {e}")
                continue

        if differences_found:
            logger.debug(
                f"Meal content comparison failed for {self.id} vs {other.id}. Differences found: {differences_found}"
            )
            return False

        logger.debug(f"Meal content comparison passed for {self.id} vs {other.id}")
        return True

    def _discover_comparable_attributes(self) -> set[str]:
        """
        Discover all attributes that should be compared for equality.

        Uses a whitelist approach: only compare actual state attributes.

        Returns:
            set[str]: Set of attribute names to compare
        """
        # Only compare private instance attributes (actual state)
        # These are the attributes that start with _ and are in __dict__
        state_attributes = {
            attr_name
            for attr_name in self.__dict__.keys()
            if attr_name.startswith("_") and not attr_name.startswith("__")
        }

        # Filter out non-comparable attributes
        return self._filter_non_comparable_attributes(state_attributes)

    def _filter_non_comparable_attributes(self, attributes: set[str]) -> set[str]:
        """
        Filter out attributes that shouldn't be compared for equality.

        Uses intelligent reflection instead of hardcoded patterns.

        Args:
            attributes: Set of attribute names to filter

        Returns:
            set[str]: Filtered set of attribute names
        """
        # Get cached properties from the class
        cached_properties = getattr(self.__class__, "_class_cached_properties", set())

        filtered = set()
        for attr_name in attributes:
            # Skip if it's a cached property (derived, not state)
            if attr_name in cached_properties:
                continue

            # Skip cache tracking attributes (Entity infrastructure)
            if (
                attr_name.endswith("__computed_caches")
                or attr_name == "_computed_caches"
            ):
                continue

            # Skip special Python attributes
            if attr_name.startswith("__") and attr_name.endswith("__"):
                continue

            # Skip transient attributes (domain events, etc.)
            if self._is_transient_attribute(attr_name):
                continue

            # Include this attribute for comparison
            filtered.add(attr_name)

        return filtered

    def _is_transient_attribute(self, attr_name: str) -> bool:
        """
        Check if an attribute is transient (shouldn't be compared).

        Args:
            attr_name: Name of the attribute to check

        Returns:
            bool: True if the attribute is transient
        """
        # Domain events are transient
        return attr_name == "events"

    def _get_attribute_value(self, attr_name: str) -> Any:
        """
        Get the value of an attribute using reflection.

        Args:
            attr_name: Name of the attribute to get

        Returns:
            Any: The attribute value
        """
        return getattr(self, attr_name)

    def _compare_values(self, val1: Any, val2: Any) -> bool:
        """
        Compare two values with appropriate handling for different types.

        This method handles various data types including:
        - None values
        - Basic types (str, int, float, bool)
        - Collections (list, tuple, set, dict) with order-independent comparison for lists
        - Dataclasses and attrs objects
        - Custom objects with __eq__ methods

        Args:
            val1: First value to compare
            val2: Second value to compare

        Returns:
            bool: True if values are equal, False otherwise
        """
        # Handle None values
        if val1 is None and val2 is None:
            return True
        if val1 is None or val2 is None:
            return False

        # Handle different types
        if type(val1) is not type(val2):
            return False

        # Handle collections
        if isinstance(val1, list | tuple):
            if len(val1) != len(val2):
                return False
            return self._compare_lists_order_independent(val1, val2)

        if isinstance(val1, set):
            if len(val1) != len(val2):
                return False
            # Convert to sorted lists for comparison since sets are unordered
            try:
                sorted_val1 = sorted(val1, key=lambda x: (type(x).__name__, str(x)))
                sorted_val2 = sorted(val2, key=lambda x: (type(x).__name__, str(x)))
                return all(
                    self._compare_values(item1, item2)
                    for item1, item2 in zip(sorted_val1, sorted_val2, strict=False)
                )
            except (TypeError, AttributeError):
                # If sorting fails, compare as sets directly
                return val1 == val2

        elif isinstance(val1, dict):
            if set(val1.keys()) != set(val2.keys()):
                return False
            return all(self._compare_values(val1[key], val2[key]) for key in val1)

        # Handle dataclasses and attrs objects (they usually have good __eq__ implementations)
        elif hasattr(val1, "__attrs_attrs__") or hasattr(val1, "__dataclass_fields__"):
            return val1 == val2

        # Handle custom objects that might have their own __eq__
        elif hasattr(val1, "__eq__") and hasattr(type(val1), "__eq__"):
            # Check if __eq__ is overridden (not the default object.__eq__)
            if type(val1).__eq__ is not object.__eq__:
                return val1 == val2
            # Fall back to identity comparison for objects without custom __eq__
            return val1 is val2

        # Handle basic types and other objects
        else:
            return val1 == val2

    def _compare_lists_order_independent(
        self, list1: list[Any] | tuple[Any, ...], list2: list[Any] | tuple[Any, ...]
    ) -> bool:
        """
        Compare two lists or tuples ignoring the order of elements.

        This method tries multiple strategies to handle different types of list elements:
        1. Sort both lists if possible and compare element by element
        2. If sorting fails, use a more expensive element-by-element matching approach

        Args:
            list1: First list or tuple to compare
            list2: Second list or tuple to compare

        Returns:
            bool: True if lists contain the same elements regardless of order
        """
        # Try to sort both lists and compare element by element
        try:
            # Create a generic sort key that works for most objects
            def sort_key(item):
                # Try to create a sortable key based on type and string representation
                return (type(item).__name__, str(item), id(type(item)))

            sorted_list1 = sorted(list1, key=sort_key)
            sorted_list2 = sorted(list2, key=sort_key)

            return all(
                self._compare_values(item1, item2)
                for item1, item2 in zip(sorted_list1, sorted_list2, strict=False)
            )

        except (TypeError, AttributeError):
            # If sorting fails, fall back to element-by-element matching
            # This is more expensive but handles cases where elements aren't sortable
            return self._compare_lists_element_matching(list1, list2)

    def _compare_lists_element_matching(
        self, list1: list[Any] | tuple[Any, ...], list2: list[Any] | tuple[Any, ...]
    ) -> bool:
        """
        Compare two lists or tuples by matching each element in list1 with an element in list2.

        This is a fallback method when sorting fails. It's more expensive (O(n²)) but
        handles cases where list elements aren't comparable/sortable.

        Args:
            list1: First list or tuple to compare
            list2: Second list or tuple to compare

        Returns:
            bool: True if each element in list1 has a matching element in list2
        """
        if len(list1) != len(list2):
            return False

        # Keep track of which elements in list2 have been matched
        list2_matched = [False] * len(list2)

        # For each element in list1, find a matching element in list2
        for item1 in list1:
            found_match = False
            for i, item2 in enumerate(list2):
                if not list2_matched[i] and self._compare_values(item1, item2):
                    list2_matched[i] = True
                    found_match = True
                    break

            if not found_match:
                return False

        # All elements in list1 should have found matches in list2
        return all(list2_matched)

    def _update_properties(self, **kwargs) -> None:
        """Override to route property updates to protected setter methods."""
        self._check_not_discarded()
        if not kwargs:
            return

        # Store original version for single increment (like base Entity class)
        original_version = self.version

        # Validate all properties first (similar to Entity base class)
        for key, value in kwargs.items():
            if key[0] == "_":
                raise AttributeError(f"{key} is private.")

            # Check if there's a corresponding protected setter method
            setter_method_name = f"_set_{key}"
            if not hasattr(self, setter_method_name):
                raise AttributeError(
                    f"Meal has no property '{key}' or it cannot be updated."
                )

        # Apply all property updates using reflection
        for key, value in kwargs.items():
            setter_method = getattr(self, f"_set_{key}")
            setter_method(value)

        # Set version manually to avoid multiple increments (like base Entity class)
        self._version = original_version + 1
        # Invalidate all caches after successful property updates
        self._invalidate_caches()

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties atomically through protected setters."""
        self._check_not_discarded()
        initial_nutri_facts = self.nutri_facts

        # Handle recipes separately if present (special processing)
        if "recipes" in kwargs:
            recipes_value = kwargs.pop("recipes")
            self._set_recipes(recipes_value)

        # Generate menu event if needed
        if self.menu_id:
            name_changed = "name" in kwargs and self.name != kwargs.get(
                "name", self.name
            )
            nutri_changed = initial_nutri_facts != self.nutri_facts

            if name_changed or nutri_changed:
                self.add_event_to_updated_menu("Updated meal properties affecting menu")

        # Process remaining properties through _update_properties
        if kwargs:
            self._update_properties(**kwargs)

    ### This is the part of the code that deals with the children recipes. ###
    def copy_recipe(
        self,
        recipe: _Recipe,
    ) -> None:
        """
        Create a new Recipe and add it to the Meal.
        """
        self._check_not_discarded()
        copied = _Recipe.copy_recipe(
            recipe=recipe, user_id=self.author_id, meal_id=self.id
        )
        self._recipes.append(copied)
        self.add_event_to_updated_menu("Added copied recipe to meal")
        self._increment_version()
        # Invalidate nutrition-related caches when recipe added
        self._invalidate_caches("nutri_facts")

    def create_recipe(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Create a new Recipe and add it to the Meal.
        """
        self._check_not_discarded()
        recipe = _Recipe.create_recipe(**kwargs)
        self._recipes.append(recipe)
        self.add_event_to_updated_menu("Created new recipe in meal")
        self._increment_version()
        # Invalidate nutrition-related caches when recipe added
        self._invalidate_caches("nutri_facts")

    def delete_recipe(self, recipe_id: str):
        self._check_not_discarded()
        for recipe in self._recipes:
            if not recipe.discarded and recipe.id == recipe_id:
                recipe.delete()
                break
        self.add_event_to_updated_menu(f"Deleted recipe {recipe_id} from meal")
        self._increment_version()
        # Invalidate nutrition-related caches when recipe deleted
        self._invalidate_caches("nutri_facts")

    def update_recipes(self, updates: dict[str, dict[str, Any]]):
        self._check_not_discarded()
        for recipe_id, kwargs in updates.items():
            recipe = self.get_recipe_by_id(recipe_id)
            if recipe:
                recipe.update_properties(**kwargs)
        self.add_event_to_updated_menu("Updated recipes in meal")
        self._increment_version()
        # Invalidate nutrition-related caches when recipes updated
        self._invalidate_caches("nutri_facts")

    def rate_recipe(
        self,
        recipe_id: str,
        user_id: str,
        taste: int,
        convenience: int,
        comment: str | None = None,
    ):
        self._check_not_discarded()
        for recipe in self._recipes:
            if not recipe.discarded and recipe.id == recipe_id:
                recipe.rate(
                    user_id=user_id,
                    taste=taste,
                    convenience=convenience,
                    comment=comment,
                )
                break
        self._increment_version()

    def delete_rate(self, recipe_id: str, user_id: str):
        self._check_not_discarded()
        for recipe in self._recipes:
            if not recipe.discarded and recipe.id == recipe_id:
                recipe.delete_rate(user_id=user_id)
                break
        self._increment_version()
