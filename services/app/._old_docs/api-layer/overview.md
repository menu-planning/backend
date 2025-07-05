# API Layer Overview

## Purpose and Role in Clean Architecture

The API layer serves as the **adapter layer** in our clean architecture implementation, acting as a bridge between external interfaces (REST APIs, AWS Lambda events) and the internal domain layer. This layer implements the **Adapter Pattern** to isolate domain logic from external concerns.

### Key Responsibilities

1. **Type Conversion**: Convert between external API types (strings, JSON) and internal domain types (UUIDs, enums, value objects)
2. **Validation**: Enforce data integrity at the API boundary
3. **Serialization**: Handle JSON serialization/deserialization for HTTP responses
4. **Security**: Sanitize inputs and prevent injection attacks through strict validation

### Clean Architecture Flow

```
External Request → API Layer → Domain Layer → Infrastructure Layer
                      ↓             ↓               ↓
                     JSON     Business Logic   Database/ORM
```

## Pydantic v2 Implementation

Our API layer is built on **Pydantic v2** with strict configuration for maximum security and type safety.

### Core Configuration

All API models inherit from `BaseApiModel` with this configuration:

```python
MODEL_CONFIG = ConfigDict(
    # SECURITY & INTEGRITY SETTINGS
    frozen=True,                 # Make models immutable - prevents accidental mutation
    strict=True,                # Enable strict type validation - NO automatic conversions
    extra='forbid',             # Forbid extra fields - prevents injection attacks
    validate_assignment=True,    # Validate assignment - ensures consistency after creation
    
    # CONVERSION & COMPATIBILITY SETTINGS  
    from_attributes=True,       # Convert from attributes to fields - enables ORM integration
    populate_by_name=True,      # Allow population by field name - supports multiple naming
    use_enum_values=True,       # Use enum values instead of enum objects - API consistency
    
    # VALIDATION BEHAVIOR SETTINGS
    validate_default=True,      # Validate default values - ensures defaults are correct
    str_strip_whitespace=True,  # Strip whitespace from strings - data cleansing
    
    # SERIALIZATION SETTINGS
    alias_generator=None,       # Can be overridden in subclasses for custom naming
    
    # PERFORMANCE SETTINGS
    arbitrary_types_allowed=False,  # Disallow arbitrary types - forces explicit validation
    revalidate_instances='never'    # Performance optimization for immutable objects
)
```

### Security Features

- **Immutable Models**: All API models are frozen to prevent accidental mutation
- **Strict Validation**: No automatic type conversions - explicit validation required
- **Injection Prevention**: Extra fields forbidden, input sanitization enforced
- **Type Safety**: Comprehensive type checking with no implicit conversions

## Domain Integration Patterns

### Three-Layer Architecture

Our API layer implements three distinct base classes for different domain patterns:

#### 1. Commands (BaseApiCommand)
- **Purpose**: Represent user actions/intentions
- **Flow**: API → Domain only (write operations)
- **Methods**: `to_domain()` on all and `from_api_model()` for update commands
- **Use Cases**: Create, Update, Delete operations

#### 2. Entities (BaseApiEntity)
- **Purpose**: Represent persistent domain objects with identity
- **Flow**: Bidirectional conversion with lifecycle fields
- **Methods**: `to_domain()`, `from_domain()`, `from_orm_model()`, `to_orm_kwargs()`
- **Use Cases**: Users, Meals, Recipes, Clients, Menus

#### 3. Value Objects (BaseApiValueObject)
- **Purpose**: Represent immutable concepts without identity
- **Flow**: Bidirectional conversion with validation
- **Methods**: `to_domain()`, `from_domain()`, `from_orm_model()`, `to_orm_kwargs()`
- **Use Cases**: Addresses, Nutrition Facts, Tags, Ratings

### Type Conversion Utilities

All API models have access to `TypeConversionUtility` for standardized conversions:

```python
class BaseApiModel(BaseModel):
    convert: ClassVar[TypeConversionUtility] = CONVERT
    
    # Common conversion patterns:
    # - UUID ↔ string: convert.uuid_to_string(), convert.string_to_uuid()
    # - Set ↔ frozenset: convert.set_to_frozenset(), convert.frozenset_to_set()  
    # - Enum ↔ string: convert.enum_to_string(), convert.string_to_enum()
    # - DateTime ↔ ISO: convert.datetime_to_isostring(), convert.isostring_to_datetime()
```

## AWS Lambda Integration Flow

### Command Event Processing Flow

```
AWS Lambda Event → JSON → API Command → Domain Command → Message Bus → Repository
                             ↓                ↓                             ↓
                         Validation      Business Logic                  Persistence
```

### Querying Event Processing Flow

```
AWS Lambda Event → JSON → API Query → Repository → Mapper -> Domain -> API Entity -> JSON
                             ↓            ↓         ↓                     ↓
                         Validation      Query  ORM to Domain         Serialization
```

### Implementation Pattern

```python
asycn def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    # 1. Parse JSON event to API command
    api_command = ApiCreateMeal.model_validate_json(event['body'])
    
    # 2. Convert to domain command
    domain_command = api_command.to_domain()
    
    # 3. Execute through message bus
    await message_bus.handle(domain_command)
    
    # 4. Convert result to API response
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({
            "message": "Meal created successfully",
            "recipe_id": domain_command.meal_id
        }),
    }
```

```python

MealListAdapter = TypeAdapter(list[ApiMeal])

asycn def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    # 1. Parse query parameters
    query_params = (
        event.get("multiValueQueryStringParameters") if event.get("multiValueQueryStringParameters") else {}
    )
    # 2. Convert query parameters to filters
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}

    # 3. Convert filters to API model
    api = ApMealFilter(**filters).model_dump()

    # 4. Convert API model to filters
    for k, _ in filters.items():
        filters[k] = api.get(k)

    # 5. Execute through message bus
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        result = await uow.meals.query(filter=filters)

    # 6. Convert result to API response
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": MealListAdapter.dump_json(
            [ApiMeal.from_domain(i) for i in result] if result else []
        ),
    }
```

## Benefits of This Architecture

### 1. **Isolation**
- Domain logic remains pure and testable
- API concerns don't leak into business logic
- Easy to change external interfaces without affecting domain

### 2. **Type Safety**
- Strict validation prevents runtime errors
- Clear type conversions between layers
- No implicit type coercion

### 3. **Security**
- Input sanitization at API boundary
- Injection attack prevention
- Immutable data structures

### 4. **Performance**
- Optimized Pydantic configuration
- Efficient JSON serialization
- Minimal overhead for type conversions

### 5. **Maintainability**
- Clear separation of concerns
- Consistent patterns across all API classes
- Easy to add new endpoints following established patterns

## Next Steps

This overview provides the foundation for understanding our API layer. The following guides will cover:

- **Implementation Guide**: Step-by-step patterns for creating API classes
- **Testing Guide**: TDD approaches and testing strategies
- **Integration Patterns**: Advanced AWS Lambda and domain integration
- **Examples**: Working code examples for all patterns 