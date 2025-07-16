from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from pydantic import HttpUrl, ValidationInfo, field_validator

from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired, UUIDIdOptional, UrlOptional
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.pydantic_validators import validate_tags_have_correct_author_id_and_type as validate_tags

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields as fields

class ApiMeal(BaseApiEntity[Meal, MealSaModel]):
    """
    **API Entity Adapter** for Meal domain objects in Clean Architecture implementation.
    
    This class serves as the **adapter layer** between external interfaces (REST APIs, AWS Lambda events) 
    and the internal domain layer, implementing the Adapter Pattern to isolate domain logic from external concerns.

    ## Architecture Role
    
    **Clean Architecture Flow:**
    ```
    External Request → API Layer → Domain Layer → Infrastructure Layer
                          ↓             ↓               ↓
                         JSON     Business Logic   Database/ORM
    ```

    ## Key Responsibilities
    
    1. **Type Conversion**: Convert between external API types (JSON strings) and internal domain types (UUIDs, enums, value objects)
    2. **Validation**: Enforce data integrity at the API boundary with strict Pydantic v2 validation
    3. **Serialization**: Handle JSON serialization/deserialization for HTTP responses
    4. **Security**: Sanitize inputs and prevent injection attacks through strict validation

    ## Security Features (Pydantic v2 Configuration)
    
    - **Immutable Models**: Frozen to prevent accidental mutation
    - **Strict Validation**: No automatic type conversions - explicit validation required
    - **Injection Prevention**: Extra fields forbidden, input sanitization enforced  
    - **Type Safety**: Comprehensive type checking with no implicit conversions

    ## Domain Integration Pattern (BaseApiEntity)
    
    **Purpose**: Represent persistent domain objects with identity
    **Flow**: Bidirectional conversion with lifecycle fields
    **Methods**: 
    - `to_domain()`: Convert API → Domain
    - `from_domain()`: Convert Domain → API  
    - `from_orm_model()`: Convert ORM → API
    - `to_orm_kwargs()`: Convert API → ORM kwargs

    ## AWS Lambda Integration
    
    Used in both command and query flows:
    - **Commands**: JSON → ApiMeal → Domain → Message Bus → Repository
    - **Queries**: Repository → Domain → ApiMeal → JSON Response

    ## Attributes
    
        id (str): Unique identifier of the meal.
        name (str): Name of the meal.
        author_id (str): Identifier of the meal's author.
        menu_id (str, optional): Identifier of the meal's menu.
        recipes (list[ApiRecipe], optional): Recipes in the meal.
        tags (frozenset[ApiTag], optional): Tags associated with the meal.
        description (str, optional): Detailed description.
        notes (str, optional): Additional notes.
        like (bool, optional): Whether the meal is liked.
        image_url (HttpUrl, optional): URL of an image.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts.
        weight_in_grams (int, optional): Weight in grams.
        calorie_density (float, optional): Calorie density.
        carbo_percentage (float, optional): Percentage of carbohydrates.
        protein_percentage (float, optional): Percentage of proteins.
        total_fat_percentage (float, optional): Percentage of total fat.

    ## Example Usage
    
    ```python
    # AWS Lambda Query Handler
    MealListAdapter = TypeAdapter(list[ApiMeal])
    
    async def lambda_handler(event, context):
        # Convert domain objects to API response
        return {
            "statusCode": 200,
            "body": MealListAdapter.dump_json(
                [ApiMeal.from_domain(meal) for meal in domain_meals]
            )
        }
    ```
    """

    name: fields.MealNameRequired
    author_id: UUIDIdRequired
    menu_id: UUIDIdOptional
    recipes: fields.MealRecipesOptionalList
    tags: fields.MealTagsOptionalFrozenset
    description: fields.MealDescriptionOptional
    notes: fields.MealNotesOptional
    like: fields.MealLikeOptional
    image_url: UrlOptional
    nutri_facts: fields.MealNutriFactsOptional
    weight_in_grams: fields.MealWeightInGramsOptional
    calorie_density: fields.MealCalorieDensityOptional
    carbo_percentage: fields.MealCarboPercentageOptional
    protein_percentage: fields.MealProteinPercentageOptional
    total_fat_percentage: fields.MealTotalFatPercentageOptional

    @field_validator('recipes', mode='after')
    @classmethod
    def validate_recipes_have_correct_meal_and_author_id(cls, v: Any, info: ValidationInfo) -> Any:
        """
        Validate meal_id equals to the meal id and author_id equals to the meal author_id.
        """
        # Check if required fields are available (they might not be if their validation failed)
        if not info.data or 'id' not in info.data or 'author_id' not in info.data:
            # If id or author_id validation failed, skip this validation
            # The error for those fields will be reported separately
            return v
            
        meal_id = info.data['id']
        author_id = info.data['author_id']
        for recipe in v:
            if recipe.meal_id != meal_id:
                raise ValueError(f"Validation error. Recipe {recipe.id} has incorrect meal_id: {recipe.meal_id}. Expected: {meal_id}")
            if recipe.author_id != author_id:
                raise ValueError(f"Validation error. Recipe {recipe.id} has incorrect author_id: {recipe.author_id}. Expected: {author_id}")
        return v


    @field_validator('tags', mode='before')
    @classmethod
    def validate_tags_have_correct_author_id_and_type(cls, v: Any, info: ValidationInfo) -> Any:
        """
        Validate tags field. If a dict is provided without 'type' and 'author_id',
        add them with default values and convert to ApiTag.
        """
        return validate_tags(v, 'meal', info)

    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        """
        Convert a domain object to an API schema instance.
        
        **Clean Architecture Flow**: Domain Layer → API Layer
        
        This method implements the **Domain → API** conversion pattern, transforming
        internal domain types (UUIDs, enums, domain value objects) to external API
        types (strings, JSON-serializable primitives) for HTTP responses.
        
        **Type Conversions Performed**:
        - Domain UUIDs → String representations
        - Domain sets → Frozen sets (immutable for API)
        - Nested domain objects → Nested API objects
        - Domain enums → String values
        
        Args:
            domain_obj (Meal): The domain meal object to convert
            
        Returns:
            ApiMeal: Immutable API representation suitable for JSON serialization
            
        **Usage in AWS Lambda**:
        ```python
        # Query response conversion
        api_meals = [ApiMeal.from_domain(meal) for meal in domain_meals]
        return {"body": MealListAdapter.dump_json(api_meals)}
        ```
        """
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            menu_id=domain_obj.menu_id,
            recipes=[ApiRecipe.from_domain(r) for r in domain_obj.recipes],
            tags=frozenset(ApiTag.from_domain(t) for t in domain_obj.tags),
            description=domain_obj.description,
            notes=domain_obj.notes,
            like=domain_obj.like,
            image_url=HttpUrl(domain_obj.image_url) if domain_obj.image_url else None,
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            weight_in_grams=domain_obj.weight_in_grams,
            calorie_density=domain_obj.calorie_density,
            carbo_percentage=domain_obj.carbo_percentage,
            protein_percentage=domain_obj.protein_percentage,
            total_fat_percentage=domain_obj.total_fat_percentage,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    def to_domain(self) -> Meal:
        """
        Convert the API schema instance to a domain object.
        
        **Clean Architecture Flow**: API Layer → Domain Layer
        
        This method implements the **API → Domain** conversion pattern, transforming
        external API types (strings, JSON primitives) back to internal domain types
        (UUIDs, enums, domain value objects) for business logic processing.
        
        **Type Conversions Performed**:
        - String representations → Domain UUIDs
        - Frozen sets → Domain sets (mutable for domain operations)
        - Nested API objects → Nested domain objects
        - String values → Domain enums
        
        **Security & Validation**:
        - All conversions are strictly validated (no implicit type coercion)
        - Input sanitization enforced at API boundary
        - Type safety maintained throughout conversion
        
        Returns:
            Meal: Pure domain object with business logic capabilities
            
        **Usage in AWS Lambda**:
        ```python
        # Command processing conversion
        api_command = ApiCreateMeal.model_validate_json(event['body'])
        domain_command = api_command.to_domain()
        await message_bus.handle(domain_command)
        ```
        """
        return Meal(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            menu_id=self.menu_id,
            recipes=[r.to_domain() for r in self.recipes] if self.recipes else None,
            tags=set(t.to_domain() for t in self.tags) if self.tags else None,
            description=self.description,
            notes=self.notes,
            like=self.like,
            image_url=str(self.image_url) if self.image_url else None,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
        """
        Convert an ORM model to an API schema instance.
        
        **Clean Architecture Flow**: Infrastructure Layer → API Layer
        
        This method implements the **ORM → API** conversion pattern in the query flow,
        transforming database/infrastructure types to API types for external response.
        Part of the complete query chain: Repository → Domain → API → JSON.
        
        **Type Conversions Performed**:
        - SQLAlchemy ORM attributes → API field types
        - Database relationships → Nested API objects
        - ORM embedded objects → API value objects
        - Database timestamps → API datetime fields
        
        **Integration with Clean Architecture**:
        - Enables direct ORM-to-API conversion for performance optimization
        - Maintains type safety between infrastructure and adapter layers
        - Supports the `from_attributes=True` Pydantic configuration
        
        Args:
            orm_model (MealSaModel): SQLAlchemy ORM model instance from database
            
        Returns:
            ApiMeal: API representation ready for JSON serialization
            
        **Usage Pattern**:
        ```python
        # Repository query result conversion
        orm_meals = await session.execute(select(MealSaModel))
        api_meals = [ApiMeal.from_orm_model(orm) for orm in orm_meals]
        ```
        """
        return cls(
            id=orm_model.id,
            name=orm_model.name,
            author_id=orm_model.author_id,
            menu_id=orm_model.menu_id,
            recipes=[ApiRecipe.from_orm_model(r) for r in orm_model.recipes],
            tags=frozenset(ApiTag.from_orm_model(t) for t in orm_model.tags),
            description=orm_model.description,
            notes=orm_model.notes,
            like=orm_model.like,
            image_url=HttpUrl(orm_model.image_url) if orm_model.image_url else None,
            nutri_facts=ApiNutriFacts(**asdict(orm_model.nutri_facts)) if orm_model.nutri_facts else None,
            weight_in_grams=orm_model.weight_in_grams,
            calorie_density=orm_model.calorie_density,
            carbo_percentage=orm_model.carbo_percentage,
            protein_percentage=orm_model.protein_percentage,
            total_fat_percentage=orm_model.total_fat_percentage,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
        )
    
    def to_orm_kwargs(self) -> Dict[str, Any]:
        """
        Convert the API schema instance to ORM model kwargs.
        
        **Clean Architecture Flow**: API Layer → Infrastructure Layer
        
        This method implements the **API → ORM** conversion pattern in the command flow,
        transforming validated API types to database/infrastructure types for persistence.
        Part of the complete command chain: JSON → API → Domain → Message Bus → Repository.
        
        **Type Conversions Performed**:
        - API field types → SQLAlchemy ORM attributes
        - Nested API objects → Database relationship data
        - API value objects → ORM embedded objects
        - API datetime fields → Database timestamps
        
        **Persistence Integration**:
        - Generates kwargs suitable for ORM model creation/update
        - Handles complex relationships and embedded objects
        - Maintains data integrity between adapter and infrastructure layers
        
        Returns:
            Dict[str, Any]: Keyword arguments for ORM model instantiation
            
        **Usage Pattern**:
        ```python
        # Repository persistence operation
        api_meal = ApiMeal.model_validate(request_data)
        orm_kwargs = api_meal.to_orm_kwargs()
        new_meal = MealSaModel(**orm_kwargs)
        session.add(new_meal)
        ```
        """
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "menu_id": self.menu_id,
            "recipes": [r.to_orm_kwargs() for r in self.recipes] if self.recipes else [],
            "tags": [t.to_orm_kwargs() for t in self.tags] if self.tags else [],
            "description": self.description,
            "notes": self.notes,
            "like": self.like,
            "image_url": str(self.image_url) if self.image_url else None,
            "nutri_facts": NutriFactsSaModel(**self.nutri_facts.to_orm_kwargs()) if self.nutri_facts else None,
            "weight_in_grams": self.weight_in_grams,
            "calorie_density": self.calorie_density,
            "carbo_percentage": self.carbo_percentage,
            "protein_percentage": self.protein_percentage,
            "total_fat_percentage": self.total_fat_percentage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
        }
