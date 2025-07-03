# API Layer Overview

## Introduction

The API layer in the menu-planning application implements the **Adapter Pattern** from Clean Architecture, serving as a bridge between external interfaces (HTTP requests, AWS Lambda events) and the internal domain layer. This layer uses **Pydantic v2** for data validation, serialization, and type safety.

## Architecture Role

The API layer serves as the outermost layer in our Clean Architecture implementation:

```
External Interface → API Layer → Domain Layer → Infrastructure Layer
     (JSON)      →  (Pydantic) →  (Domain Objects) →  (Database)
```

### Key Responsibilities

1. **Input Validation**: Strict validation of incoming data with comprehensive type checking
2. **Type Conversion**: Seamless conversion between API types and domain types
3. **Security**: Protection against injection attacks and data corruption
4. **Immutability**: Ensuring data integrity through frozen models
5. **Serialization**: Converting domain objects to JSON responses

## Core Components

### BaseApiModel Configuration

All API schemas inherit from `BaseApiModel` which provides strict Pydantic v2 configuration:

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

### Schema Hierarchy

The API layer implements three main schema types:

1. **BaseApiCommand**: For write operations (commands)
2. **BaseApiEntity**: For domain entities with identity
3. **BaseApiValueObject**: For value objects without identity

## AWS Lambda Integration Flow

The API layer integrates seamlessly with AWS Lambda:

```
AWS Lambda Event → JSON Parsing → ApiCommand → Domain Layer → MessageBus → Response
```

### Flow Steps

1. **Event Reception**: Lambda receives event with JSON payload
2. **JSON Validation**: Pydantic validates and parses JSON into API schema
3. **Domain Conversion**: API schema converts to domain command via `to_domain()`
4. **Domain Processing**: Domain layer processes the command
5. **Response Generation**: Results convert back through API layer to JSON

## Type Conversion Strategy

The API layer handles comprehensive type conversions:

- **Domain UUID ↔ API String**: UUID objects become strings for JSON serialization
- **Domain Enum ↔ API Enum**: Enum objects become values for API consistency
- **Domain Set ↔ API FrozenSet**: Mutable sets become immutable for safety
- **Domain DateTime ↔ API String**: DateTime objects become ISO strings

## Security Features

### Input Validation
- **Strict typing**: No automatic type conversions
- **Field validation**: Comprehensive field-level validation
- **Extra field rejection**: Prevents injection attacks

### Data Integrity
- **Immutable models**: Frozen configuration prevents accidental mutation
- **Validation on assignment**: Ensures consistency after creation
- **Default validation**: Validates default values for correctness

## Design Patterns

### Command Pattern
Commands represent actions to be performed:
```python
class ApiCreateUser(BaseApiCommand[CreateUser]):
    name: str
    email: str
    
    def to_domain(self) -> CreateUser:
        return CreateUser(name=self.name, email=self.email)
```

### Adapter Pattern
Entities adapt domain objects for API consumption:
```python
class ApiUser(BaseApiEntity[User, UserORM]):
    name: str
    email: str
    
    @classmethod
    def from_domain(cls, user: User) -> "ApiUser":
        return cls(
            id=cls.convert.uuid_to_string(user.id),
            name=user.name,
            email=user.email
        )
```

## Benefits

1. **Type Safety**: Comprehensive type validation prevents runtime errors
2. **Security**: Protection against injection attacks and data corruption
3. **Maintainability**: Clear separation of concerns and consistent patterns
4. **Performance**: Optimized validation and conversion utilities
5. **Developer Experience**: Clear error messages and comprehensive documentation

## Next Steps

For detailed implementation guidance, see:
- [Implementation Guide](./implementation-guide.md)
- [Testing Guide](./testing-guide.md)
- [Integration Patterns](./integration-patterns.md)
- [Code Examples](./examples/) 