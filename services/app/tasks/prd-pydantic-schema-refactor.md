# Product Requirements Document: Pydantic Schema Refactoring

## Overview
This document outlines the requirements and implementation plan for refactoring the Pydantic schemas in the menu-planning application to leverage Pydantic v2 features and establish better data validation patterns.

## Current State
- Using Pydantic v2 with existing schemas under `**/adapters/api_schemas/**`
- Current schema structure follows a pattern of mapping between Domain ↔ API Schema ↔ ORM models
- Using pytest for testing infrastructure
- Using domain models under `**/domain/**`
- Using SQLAlchemy for ORM with models under `**/adapters/ORM/sa_models/**`
- Using attrs for value objects
- No existing CI pipeline

## Goals
1. Improve data validation and conversion efficiency
2. Establish consistent schema patterns across the codebase
3. Leverage Pydantic v2's advanced features
4. Maintain type safety and improve error handling
5. Enable bulk validation for collections
6. Reduce code duplication

## Non-Goals
1. Changing the domain model structure
2. Modifying business logic
3. Changing the database schema
4. Maintaining backward compatibility with old schema versions

## Functional Requirements

### 1. Schema Location and Structure
- **Location:** All Pydantic schema files must remain under `**/adapters/api_schemas/**`
- **Purpose:** Schemas act purely as DTOs/validators
- **Base Model:** All schemas must inherit from `BaseApiModel` which implements the shared configuration

### 2. Base Model Configuration
```python
class BaseApiModel(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        slots=True,
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
        extra="ignore",
        validate_assignment=False,
        use_enum_values=True
    )
```

### 3. Validation Rules
- No business logic or domain invariants in schemas
- Type and shape validation only
- Use `Optional[...]` with "before" validators to coerce empty strings/lists to `None`
- Domain invariants belong in Domain layer

### 4. Collection Validation
- For fields containing collections of nested schemas (e.g., `list[ApiRecipe]`):
  - Create module-level `TypeAdapter`
  - Implement validation using `@field_validator(..., mode="before")`
- Example implementation:
```python
recipe_list_adapter = TypeAdapter(list[ApiRecipe])

@field_validator("recipes", mode="before")
def validate_recipes(cls, value):
    return recipe_list_adapter.validate_python(value)
```

### 5. Serialization
- Use `model_dump(by_alias=True, exclude_none=True)` for JSON output
- Expose raw JSON string via `model_dump_json(...)` when required
- Consistent serialization patterns across all schemas

### 6. Conversion Helpers
Each schema must implement:
```python
@classmethod
def from_domain(cls, domain_obj):
    # Convert from domain model
    pass

def to_domain(self):
    # Convert to domain model
    pass

@classmethod
def from_orm_model(cls, sa_obj):
    # Convert from SQLAlchemy model
    pass

def to_orm_kwargs(self):
    # Convert to SQLAlchemy model kwargs
    pass
```

### 7. Schema Examples
- Each schema must include `schema_extra["example"]` showing minimal valid JSON payload
- Examples should be realistic and cover common use cases

### 8. Testing Requirements
- Unit tests for each schema must include:
  - Successful validation of example payload
  - Successful conversion from minimal SQLAlchemy instance
  - Error cases and validation failures
  - Bulk validation scenarios
  - Serialization consistency

### 9. CI Integration
- Dedicated GitHub Action for schema testing
- Runs on every push and pull request
- Focuses on schema validation and conversion tests

## Technical Requirements

### 1. Base Schema Classes
- Create base classes for common patterns
- Implement shared validation logic
- Define standard conversion methods

### 2. Testing Requirements
- Unit tests for each schema
- Test both successful and error cases
- Validate bidirectional conversions
- Test bulk validation performance
- Test serialization consistency

### 3. Error Handling
- Clear error messages
- Proper error propagation
- Custom validation errors when needed

## Migration Strategy

### Phase 1: Foundation (Week 1)
1. Create base schema classes
2. Set up testing infrastructure
3. Document patterns and guidelines

### Phase 2: Gradual Migration (Weeks 2-4)
1. Start with `Meal` schema as pilot
2. Create new schema version
3. Write comprehensive tests
4. Validate against existing functionality
5. Move to next schema after successful testing

### Phase 3: Bulk Validation (Week 5)
1. Implement TypeAdapter patterns
2. Performance testing
3. Documentation updates

### Phase 4: Cleanup (Week 6)
1. Remove deprecated schemas
2. Update documentation
3. Final testing

## Success Metrics
1. All schemas follow new pattern
2. 100% test coverage for schemas
3. No business logic in schemas
4. Successful bulk validation implementation
5. Clear error messages
6. Improved performance metrics

## Example Implementation (Meal Schema)

```python
from pydantic import Field, TypeAdapter
from .base import BaseApiModel

class ApiMeal(BaseApiModel):
    id: str
    name: str
    author_id: str
    menu_id: Optional[str] = Field(default=None)
    recipes: list[ApiRecipe] = Field(default_factory=list)
    tags: set[ApiTag] = Field(default_factory=set)

    # Type adapter for bulk validation
    _recipe_list_adapter = TypeAdapter(list[ApiRecipe])
    
    @field_validator("recipes", mode="before")
    def validate_recipes(cls, value):
        return cls._recipe_list_adapter.validate_python(value)

    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        return cls.model_validate(domain_obj)

    def to_domain(self) -> Meal:
        return Meal(**self.model_dump())

    @classmethod
    def from_orm_model(cls, sa_obj: SAMeal) -> "ApiMeal":
        return cls.model_validate(sa_obj)

    def to_orm_kwargs(self) -> dict:
        return self.model_dump(exclude={"id"})

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "meal_123",
                "name": "Sunday Brunch",
                "author_id": "user_456",
                "menu_id": "menu_789",
                "recipes": [],
                "tags": []
            }
        }
    }
```

## Open Questions
1. Should we migrate from attrs to dataclasses for value objects?
2. Do we need to support partial updates in schemas?
3. Should we implement custom JSON encoders for specific types?

## Next Steps
1. Review and approve PRD
2. Set up testing infrastructure
3. Create base schema classes
4. Begin migration with Meal schema
5. Regular progress reviews 

# Tasks for Pydantic Schema Refactoring

## Relevant Files

### Base Schema
- `adapters/api_schemas/base.py` - Base schema classes and shared configuration

### Shared Kernel Context
- `contexts/shared_kernel/adapters/api_schemas/value_objects/amount.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/address.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/tag/tag_filter.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/contact_info.py`
- `contexts/shared_kernel/adapters/api_schemas/value_objects/profile.py`

### IAM Context
- `contexts/iam/core/adapters/api_schemas/value_objects/role.py`
- `contexts/iam/core/adapters/api_schemas/entities/user.py`
- `contexts/iam/core/adapters/api_schemas/commands/create_user.py`
- `contexts/iam/core/adapters/api_schemas/commands/remove_role_from_user.py`
- `contexts/iam/core/adapters/api_schemas/commands/assign_role_to_user.py`

### Recipes Catalog Context
- `contexts/recipes_catalog/core/adapters/api_schemas/value_objects/rating.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/value_objects/ingredient.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/menu.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/meal.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/recipe.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/client/client.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/entities/client/filter.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/menu/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/meal/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/recipe/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/client/*.py`
- `contexts/recipes_catalog/core/adapters/api_schemas/commands/tag/*.py`

### Products Catalog Context
- `contexts/products_catalog/core/adapters/api_schemas/value_objects/score.py`
- `contexts/products_catalog/core/adapters/api_schemas/value_objects/if_food_votes.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/product.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/product_filter.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/classifications/base_class.py`
- `contexts/products_catalog/core/adapters/api_schemas/entities/classifications/filter.py`
- `contexts/products_catalog/core/adapters/api_schemas/commands/products/*.py`
- `contexts/products_catalog/core/adapters/api_schemas/commands/classification/*.py`

### CI Configuration
- `.github/workflows/schema-tests.yml` - CI pipeline for schema testing

### Notes

- All schema files should be placed under their respective context directories
- Test files should be placed alongside their corresponding schema files
- Use `pytest` for running tests
- Follow the example implementation pattern from the PRD
- Each schema should implement the required conversion methods (from_domain, to_domain, from_orm_model, to_orm_kwargs)
- All schemas must inherit from BaseApiModel with the specified configuration

## Tasks

- [ ] 1.0 Foundation Setup
  - [ ] 1.1 Create base schema classes and configuration
  - [ ] 1.2 Set up testing infrastructure
  - [ ] 1.3 Document schema patterns and guidelines
  - [ ] 1.4 Create GitHub Actions workflow for schema testing

- [ ] 2.0 Shared Kernel Context Migration
  - [ ] 2.1 Migrate value objects (amount, address, contact_info, profile)
  - [ ] 2.2 Migrate tag filter schema
  - [ ] 2.3 Write tests for all shared kernel schemas

- [ ] 3.0 IAM Context Migration
  - [ ] 3.1 Migrate role and user value objects
  - [ ] 3.2 Migrate user entity schema
  - [ ] 3.3 Migrate command schemas (create_user, role management)
  - [ ] 3.4 Write tests for all IAM schemas

- [ ] 4.0 Recipes Catalog Context Migration
  - [ ] 4.1 Migrate value objects (rating, ingredient)
  - [ ] 4.2 Migrate entity schemas (menu, meal, recipe, client)
  - [ ] 4.3 Migrate filter schemas
  - [ ] 4.4 Migrate command schemas
  - [ ] 4.5 Write tests for all recipes catalog schemas

- [ ] 5.0 Products Catalog Context Migration
  - [ ] 5.1 Migrate value objects (score, if_food_votes)
  - [ ] 5.2 Migrate entity schemas (product, classification)
  - [ ] 5.3 Migrate filter schemas
  - [ ] 5.4 Migrate command schemas
  - [ ] 5.5 Write tests for all products catalog schemas

- [ ] 6.0 Bulk Validation Implementation
  - [ ] 6.1 Implement TypeAdapter patterns for all collection fields
  - [ ] 6.2 Add performance testing
  - [ ] 6.3 Update documentation

- [ ] 7.0 Cleanup and Finalization
  - [ ] 7.1 Remove deprecated schemas
  - [ ] 7.2 Update documentation
  - [ ] 7.3 Final testing and validation
  - [ ] 7.4 Verify all schemas follow the new pattern 