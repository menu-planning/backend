# Pydantic Schema Patterns and Guidelines

## Overview

This document outlines the patterns and guidelines for implementing Pydantic schemas in the menu-planning application. These schemas serve as Data Transfer Objects (DTOs) and validators for API requests and responses.

## Base Configuration

All schemas must inherit from `BaseApiModel` which provides the following configuration:

```python
model_config = ConfigDict(
    frozen=True,              # Make models immutable
    strict=True,             # Enable strict mode for better type checking
    from_attributes=True,    # Convert from attributes to fields
    extra='forbid',          # Forbid extra fields
    validate_default=True,   # Validate default values
    use_enum_values=True,    # Use enum values instead of enum objects
    populate_by_name=True,   # Allow population by field name
    validate_assignment=True # Validate assignment
)
```

## Schema Location and Structure

1. **File Location**: All schema files must be placed under `**/adapters/api_schemas/**`
2. **File Organization**:
   - Value Objects: `value_objects/`
   - Entities: `entities/`
   - Commands: `commands/`
   - Filters: `filters/`

## Required Methods

Every schema must implement these conversion methods:

```python
@classmethod
def from_domain(cls, domain_obj: D) -> Self:
    """Convert from domain model to schema"""
    raise NotImplementedError()

def to_domain(self) -> D:
    """Convert from schema to domain model"""
    raise NotImplementedError()

@classmethod
def from_orm_model(cls, orm_model: S) -> Self:
    """Convert from ORM model to schema"""
    raise NotImplementedError()

def to_orm_kwargs(self) -> Dict[str, Any]:
    """Convert to ORM model kwargs"""
    raise NotImplementedError()
```

## Validation Rules

1. **No Business Logic**: Schemas should only handle type and shape validation
2. **Nullable Fields**: Use `Optional[...]` with `Field(default=None)` and coercion
3. **Collection Validation**: Use `TypeAdapter` for bulk validation of collections
4. **Field Documentation**: Every field must have a descriptive docstring

## Example Implementation

```python
from pydantic import Field, TypeAdapter
from .base import BaseApiModel

class ApiRecipe(BaseApiModel):
    """Schema for recipe data."""
    
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Recipe name")
    ingredients: list[ApiIngredient] = Field(default_factory=list)
    
    # Type adapter for bulk validation
    _ingredient_list_adapter = TypeAdapter(list[ApiIngredient])
    
    @field_validator("ingredients", mode="before")
    def validate_ingredients(cls, value):
        return cls._ingredient_list_adapter.validate_python(value)
    
    @classmethod
    def from_domain(cls, domain_obj: Recipe) -> "ApiRecipe":
        return cls.model_validate(domain_obj)
    
    def to_domain(self) -> Recipe:
        return Recipe(**self.model_dump())
```

## Testing Requirements

1. **Unit Tests**: Each schema must have corresponding test file
2. **Test Coverage**:
   - Successful validation of example payload
   - Successful conversion from minimal SQLAlchemy instance
   - Error cases and validation failures
   - Bulk validation scenarios
   - Serialization consistency

## Best Practices

1. **Documentation**:
   - Include docstrings for all schemas and methods
   - Document field constraints and validations
   - Provide example usage

2. **Error Handling**:
   - Use clear error messages
   - Implement custom validation errors when needed
   - Handle edge cases gracefully

3. **Performance**:
   - Use bulk validation for collections
   - Minimize validation overhead
   - Cache TypeAdapter instances

4. **Maintenance**:
   - Keep schemas focused and single-purpose
   - Follow consistent naming conventions
   - Update tests when schema changes

## Common Patterns

1. **Value Objects**:
   - Use for immutable, self-contained data
   - Implement validation rules
   - Keep business logic in domain layer

2. **Entities**:
   - Include common fields (id, created_at, etc.)
   - Handle relationships carefully
   - Implement proper conversion methods

3. **Commands**:
   - Focus on input validation
   - Include only necessary fields
   - Clear conversion to domain commands

4. **Filters**:
   - Support pagination
   - Handle sorting
   - Implement proper validation

## Migration Guidelines

When migrating existing schemas:

1. Create new schema version
2. Implement required methods
3. Add comprehensive tests
4. Validate against existing functionality
5. Update dependent code
6. Remove old schema version

## CI/CD Integration

1. Schema tests run on every push
2. Validation of schema patterns
3. Performance testing for bulk validation
4. Documentation generation 