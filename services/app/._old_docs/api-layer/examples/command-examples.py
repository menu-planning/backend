"""
API Command Pattern Examples

This module demonstrates practical command patterns using BaseApiCommand.
Commands represent user actions/intentions flowing from API to Domain layer.

Key Patterns Demonstrated:
1. Simple commands (Create, Delete)
2. Complex commands with nested updates (Update)
3. Field validation and conversion patterns
4. Real-world command structure without entity duplication

Commands reference complex types (like recipes, tags) but don't define them.
See entity-examples.py and value-object-examples.py for those patterns.
"""

from __future__ import annotations
from typing import Any, Dict, List, FrozenSet
from uuid import uuid4
from pydantic import Field, ValidationError
from enum import Enum
from attrs import frozen

# Base imports - these represent your actual base classes
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId, UUIDIdOptional
from src.contexts.seedwork.shared.domain.commands.command import Command

# =============================================================================
# SIMULATED DOMAIN COMMANDS (keeping them simple like your real ones)
# =============================================================================

@frozen(kw_only=True)
class CreateMealCommand(Command):
    """Simple domain command for creating a meal."""
    name: str
    author_id: str
    menu_id: str
    description: str | None = None
    notes: str | None = None

@frozen(kw_only=True)
class UpdateMealCommand(Command):
    """Simple domain command for updating a meal - just like your real one."""
    meal_id: str
    updates: dict[str, Any]

@frozen(kw_only=True)
class DeleteMealCommand(Command):
    """Simple domain command for deleting a meal."""
    meal_id: str

@frozen(kw_only=True)
class CreateRecipeCommand(Command):
    """Simple domain command for creating a recipe."""
    name: str
    author_id: str
    meal_id: str
    instructions: str
    privacy: str = "private"

# =============================================================================
# FIELD TYPE DEFINITIONS (simulating your real field types)
# =============================================================================

# These simulate your actual field types from api_meal_fields.py
from typing import Annotated

MealName = Annotated[str, Field(..., min_length=1, max_length=255, description="Name of the meal")]
MealDescription = Annotated[str | None, Field(None, description="Detailed description")]
MealNotes = Annotated[str | None, Field(None, description="Additional notes")]
MealImageUrl = Annotated[str | None, Field(None, description="URL of the meal image")]
MealLike = Annotated[bool, Field(False, description="Whether the meal is liked")]

# These represent collections that would be defined elsewhere
MealRecipes = Annotated[List[str], Field(default_factory=list, description="List of recipe IDs")]
MealTags = Annotated[FrozenSet[str], Field(default_factory=frozenset, description="Set of tag IDs")]

RecipeName = Annotated[str, Field(..., min_length=1, max_length=255, description="Name of the recipe")]
RecipeInstructions = Annotated[str, Field(..., min_length=10, description="Recipe instructions")]

class RecipePrivacy(Enum):
    PUBLIC = "public"
    PRIVATE = "private"

# =============================================================================
# COMMAND PATTERN EXAMPLES
# =============================================================================

class ApiCreateMeal(BaseApiCommand[CreateMealCommand]):
    """
    API command for creating a meal.
    
    Demonstrates:
    - Simple create command pattern
    - Required and optional fields
    - Basic validation
    - Straightforward to_domain() conversion
    """
    
    name: MealName
    author_id: UUIDId
    menu_id: UUIDId
    description: MealDescription
    notes: MealNotes

    def to_domain(self) -> CreateMealCommand:
        """Convert API command to domain command."""
        return CreateMealCommand(
            name=self.name,
            author_id=self.author_id,
            menu_id=self.menu_id,
            description=self.description,
            notes=self.notes,
        )


class ApiAttributesToUpdateOnMeal(BaseApiCommand[UpdateMealCommand]):
    """
    API command for meal update attributes.
    
    Demonstrates:
    - Partial update pattern (all fields optional)
    - Collection handling (recipes, tags)
    - exclude_unset for partial updates
    - Complex field types from other modules
    
    Note: This mirrors your actual ApiAttributesToUpdateOnMeal structure
    """
    
    name: MealName | None = None
    menu_id: UUIDIdOptional = None
    description: MealDescription = None
    recipes: MealRecipes = Field(default_factory=list)  # References recipe IDs
    tags: MealTags = Field(default_factory=frozenset)  # References tag IDs
    notes: MealNotes = None
    like: MealLike = False
    image_url: MealImageUrl = None

    def to_domain(self) -> Dict[str, Any]:
        """
        Convert to dictionary of update attributes.
        
        Uses exclude_unset=True to only include explicitly set fields.
        """
        return self.model_dump(exclude_unset=True)


class ApiUpdateMeal(BaseApiCommand[UpdateMealCommand]):
    """
    API command for updating an existing meal.
    
    Demonstrates:
    - Nested command pattern (updates within command)
    - Complex validation through nested objects
    - from_api_entity class method pattern
    - Realistic command structure like your codebase
    """
    
    meal_id: UUIDId
    updates: ApiAttributesToUpdateOnMeal

    def to_domain(self) -> UpdateMealCommand:
        """Convert API command to domain command."""
        return UpdateMealCommand(
            meal_id=self.meal_id,
            updates=self.updates.to_domain(),
        )

    @classmethod
    def from_api_meal(cls, api_meal: Any) -> "ApiUpdateMeal":
        """
        Create update command from existing meal entity.
        
        This demonstrates how commands can be created from entities
        without tight coupling - just extracts the needed fields.
        """
        # Extract updatable fields from the meal entity
        attributes_to_update = {
            "name": getattr(api_meal, "name", None),
            "menu_id": getattr(api_meal, "menu_id", None),
            "description": getattr(api_meal, "description", None),
            "notes": getattr(api_meal, "notes", None),
            "like": getattr(api_meal, "like", False),
            "image_url": getattr(api_meal, "image_url", None),
        }
        
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )


class ApiDeleteMeal(BaseApiCommand[DeleteMealCommand]):
    """
    API command for deleting a meal.
    
    Demonstrates:
    - Simple delete command pattern
    - Minimal required fields
    - Optional reason/metadata fields
    """
    
    meal_id: UUIDId
    reason: str | None = Field(None, max_length=200, description="Optional deletion reason")

    def to_domain(self) -> DeleteMealCommand:
        """Convert API command to domain command."""
        return DeleteMealCommand(meal_id=self.meal_id)


class ApiCreateRecipe(BaseApiCommand[CreateRecipeCommand]):
    """
    API command for creating a recipe.
    
    Demonstrates:
    - Enum field handling
    - Multiple field types
    - Business logic validation
    """
    
    name: RecipeName
    author_id: UUIDId
    meal_id: UUIDId
    instructions: RecipeInstructions
    privacy: RecipePrivacy = RecipePrivacy.PRIVATE

    def to_domain(self) -> CreateRecipeCommand:
        """Convert API command to domain command."""
        return CreateRecipeCommand(
            name=self.name,
            author_id=self.author_id,
            meal_id=self.meal_id,
            instructions=self.instructions,
            privacy=self.privacy.value,  # Enum to string conversion
        )


# =============================================================================
# USAGE EXAMPLES AND PATTERNS
# =============================================================================

def example_create_command():
    """
    Example: Creating a meal with validation.
    
    Shows the typical flow from API input to domain command.
    """
    print("=== Create Command Example ===")
    
    # Create API command
    api_command = ApiCreateMeal(
        name="Italian Dinner",
        author_id=str(uuid4()),
        menu_id=str(uuid4()),
        description="A delicious Italian meal",
        notes="Perfect for date night"
    )
    
    # Convert to domain command
    domain_command = api_command.to_domain()
    
    print(f"Created meal: {domain_command.name}")
    print(f"Author: {domain_command.author_id}")
    print(f"Description: {domain_command.description}")
    
    return domain_command


def example_update_command():
    """
    Example: Updating a meal with partial data.
    
    Shows exclude_unset functionality and nested command patterns.
    """
    print("\n=== Update Command Example ===")
    
    # Create update command with only some fields
    api_update = ApiUpdateMeal(
        meal_id=str(uuid4()),
        updates=ApiAttributesToUpdateOnMeal(
            name="Updated Italian Dinner",
            description="An even more delicious Italian meal",
            like=True,
            # recipes and tags not provided - will be excluded
        )
    )
    
    # Convert to domain command
    domain_update = api_update.to_domain()
    
    print(f"Update meal: {domain_update.meal_id}")
    print(f"Updates: {domain_update.updates}")
    print(f"Only updated fields included: {len(domain_update.updates)} fields")
    
    return domain_update


def example_delete_command():
    """
    Example: Deleting a meal with optional reason.
    
    Shows simple command pattern.
    """
    print("\n=== Delete Command Example ===")
    
    # Create delete command
    api_delete = ApiDeleteMeal(
        meal_id=str(uuid4()),
        reason="User requested deletion"
    )
    
    # Convert to domain command
    domain_delete = api_delete.to_domain()
    
    print(f"Delete meal: {domain_delete.meal_id}")
    print(f"Command type: {type(domain_delete).__name__}")
    
    return domain_delete


def example_json_workflow():
    """
    Example: JSON workflow as would happen in AWS Lambda.
    
    Shows model_validate_json and error handling.
    """
    print("\n=== JSON Workflow Example ===")
    
    # Sample JSON input (as would come from API request)
    json_input = '''
    {
        "name": "Mediterranean Bowl",
        "author_id": "550e8400-e29b-41d4-a716-446655440000",
        "menu_id": "550e8400-e29b-41d4-a716-446655440001",
        "description": "Healthy Mediterranean meal",
        "notes": "Great for lunch"
    }
    '''
    
    try:
        # Parse JSON to API command
        api_command = ApiCreateMeal.model_validate_json(json_input)
        
        # Convert to domain command
        domain_command = api_command.to_domain()
        
        # Success response
        response = {
            "status": "success",
            "meal_id": str(uuid4()),
            "message": f"Created meal: {domain_command.name}"
        }
        
        print(f"Successfully processed JSON: {response}")
        return response
        
    except ValidationError as e:
        error_response = {
            "status": "error",
            "message": f"Validation failed: {e}"
        }
        print(f"Validation error: {error_response}")
        return error_response


def example_command_composition():
    """
    Example: How commands work with complex nested structures.
    
    Shows how commands reference complex types without defining them.
    """
    print("\n=== Command Composition Example ===")
    
    # Create a complex update command
    api_update = ApiUpdateMeal(
        meal_id=str(uuid4()),
        updates=ApiAttributesToUpdateOnMeal(
            name="Complex Meal",
            recipes=["recipe-1", "recipe-2", "recipe-3"],  # Recipe IDs
            tags=frozenset(["italian", "dinner", "family"]),  # Tag IDs
            description="A meal with multiple recipes and tags",
            like=True
        )
    )
    
    # Convert to domain
    domain_update = api_update.to_domain()
    
    print(f"Update meal: {domain_update.meal_id}")
    print(f"Recipe count: {len(domain_update.updates.get('recipes', []))}")
    print(f"Tag count: {len(domain_update.updates.get('tags', set()))}")
    print(f"Updates: {list(domain_update.updates.keys())}")
    
    return domain_update


if __name__ == "__main__":
    """
    Run all examples to demonstrate command patterns.
    """
    print("=== API Command Pattern Examples ===")
    
    example_create_command()
    example_update_command()
    example_delete_command()
    example_json_workflow()
    example_command_composition()
    
    print("\n=== All examples completed! ===")
    print("\nKey Takeaways:")
    print("1. Commands are simple - they focus on actions, not data modeling")
    print("2. Commands reference complex types but don't define them")
    print("3. Domain commands are minimal - API commands handle validation")
    print("4. Use exclude_unset=True for partial updates")
    print("5. Commands flow one way: API → Domain") 