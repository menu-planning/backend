# API Layer Implementation Guide

## Overview

This guide provides step-by-step implementation patterns for the API layer in the menu-planning application. All patterns follow Clean Architecture principles and leverage Pydantic v2 for comprehensive validation and type safety.

## BaseApiModel Configuration

### Configuration Details

Every API schema inherits from `BaseApiModel` which enforces strict validation:

```python
from pydantic import BaseModel, ConfigDict

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

### Configuration Rationale

- **`frozen=True`**: Prevents accidental mutation after creation, ensuring data integrity
- **`strict=True`**: Disables automatic type conversions that could mask errors
- **`extra='forbid'`**: Prevents injection attacks by rejecting unexpected fields
- **`validate_assignment=True`**: Ensures consistency even when reassigning fields
- **`from_attributes=True`**: Enables ORM integration by converting object attributes to fields
- **`use_enum_values=True`**: Ensures consistent JSON serialization of enum fields

## Command Implementation Patterns

### BaseCommand Inheritance

Commands represent actions to be performed on the system. They inherit from `BaseApiCommand` and domain `Command`:

```python
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.your_context.domain.commands.your_command import YourCommand

class ApiYourCommand(BaseApiCommand[YourCommand]):
    """
    API command for performing your action.
    
    This command handles validation and conversion from API layer to domain layer.
    """
    
    # Required fields for the command
    entity_id: UUIDId
    name: str
    description: str | None = None
    
    def to_domain(self) -> YourCommand:
        """Convert API command to domain command.
        
        Required method that transforms API-level data into domain-level command.
        """
        return YourCommand(
            entity_id=self.entity_id,
            name=self.name,
            description=self.description
        )
```

### Update Command Pattern

For update operations, implement a separate attributes class and use the `from_api_<entity>` classmethod:

```python
from typing import Any

class ApiAttributesToUpdateOnUser(BaseApiCommand[UpdateUser]):
    """
    API command for user attributes that can be updated.
    
    Contains only the fields that can be updated, all optional.
    """
    
    name: str | None = None
    email: str | None = None
    
    def to_domain(self) -> dict[str, Any]:
        """Convert to dictionary of attributes to update.
        
        Returns only the fields that were set (exclude_unset=True).
        """
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnUser to domain model: {e}"
            )


class ApiUpdateUser(BaseApiCommand[UpdateUser]):
    """API command for updating user information."""
    
    user_id: UUIDId
    updates: ApiAttributesToUpdateOnUser
    
    def to_domain(self) -> UpdateUser:
        """Convert to domain update command."""
        try:
            return UpdateUser(
                user_id=self.user_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateUser to domain model: {e}")
    
    @classmethod
    def from_api_user(cls, api_user: ApiUser) -> "ApiUpdateUser":
        """Create update command from existing API user."""
        attributes_to_update = {
            key: getattr(api_user, key) for key in ApiUser.model_fields.keys()
        }
        return cls(
            user_id=api_user.id,
            updates=ApiAttributesToUpdateOnUser(**attributes_to_update),
        )
```

### Command Usage in AWS Lambda

Commands integrate with AWS Lambda event processing:

```python
# In your Lambda handler
def lambda_handler(event, context):
    try:
        # Parse and validate JSON event data
        api_command = ApiCreateUser.model_validate(event)
        
        # Convert to domain command
        domain_command = api_command.to_domain()
        
        # Process through domain layer
        result = message_bus.handle(domain_command)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"success": True, "result": result})
        }
    except ValidationError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Validation failed", "details": e.errors()})
        }
```

## Entity Implementation Patterns

### BaseEntity Inheritance

Entities represent domain objects with identity and lifecycle. They inherit from `BaseApiEntity`:

```python
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.your_context.domain.entities.your_entity import YourEntity
from src.contexts.your_context.adapters.orm.your_entity_orm import YourEntityORM

class ApiYourEntity(BaseApiEntity[YourEntity, YourEntityORM]):
    """
    API entity for your domain entity.
    
    Provides conversion between domain, API, and ORM layers.
    """
    
    # Entity-specific fields
    name: str
    description: str | None = None
    status: str = "active"
    
    @classmethod
    def from_domain(cls, entity: YourEntity) -> "ApiYourEntity":
        """Convert domain entity to API entity.
        
        Required method for domain → API conversion.
        """
        return cls(
            id=cls.convert.uuid_to_string(entity.id),
            name=entity.name,
            description=entity.description,
            status=entity.status,
            created_at=cls.convert.datetime_to_isostring(entity.created_at),
            updated_at=cls.convert.datetime_to_isostring(entity.updated_at),
            version=entity.version,
            discarded=entity.discarded
        )
    
    def to_domain(self) -> YourEntity:
        """Convert API entity to domain entity.
        
        Required method for API → domain conversion.
        """
        return YourEntity(
            id=self.convert.string_to_uuid(self.id),
            name=self.name,
            description=self.description,
            status=self.status,
            created_at=self.convert.isostring_to_datetime(self.created_at),
            updated_at=self.convert.isostring_to_datetime(self.updated_at),
            version=self.version,
            discarded=self.discarded
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: YourEntityORM) -> "ApiYourEntity":
        """Convert ORM model to API entity.
        
        Required method for ORM → API conversion.
        """
        return cls(
            id=str(orm_model.id),
            name=orm_model.name,
            description=orm_model.description,
            status=orm_model.status,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            version=orm_model.version,
            discarded=orm_model.discarded
        )
    
    def to_orm_kwargs(self) -> dict:
        """Convert API entity to ORM kwargs.
        
        Required method for API → ORM conversion.
        """
        return {
            "id": self.convert.string_to_uuid(self.id),
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_at": self.convert.isostring_to_datetime(self.created_at),
            "updated_at": self.convert.isostring_to_datetime(self.updated_at),
            "version": self.version,
            "discarded": self.discarded
        }
```

### Entity Usage Pattern

Entities flow through the system in predictable patterns:

```python
# Domain Entity → API Entity → JSON Response
domain_entity = user_service.get_user(user_id)
api_entity = ApiUser.from_domain(domain_entity)
json_response = api_entity.model_dump_json()

# JSON Request → API Entity → Domain Entity
json_data = request.json
api_entity = ApiUser.model_validate(json_data)
domain_entity = api_entity.to_domain()

# ORM Model → API Entity → JSON Response
orm_model = session.query(UserORM).filter_by(id=user_id).first()
api_entity = ApiUser.from_orm_model(orm_model)
json_response = api_entity.model_dump_json()
```

## Value Object Implementation Patterns

### BaseValueObject Inheritance

Value objects represent concepts without identity. They inherit from `BaseApiValueObject`:

```python
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.your_context.domain.value_objects.your_value_object import YourValueObject
from src.contexts.your_context.adapters.orm.your_value_object_orm import YourValueObjectORM

class ApiYourValueObject(BaseApiValueObject[YourValueObject, YourValueObjectORM]):
    """
    API value object for your domain value object.
    
    Emphasizes immutability and value equality.
    """
    
    # Value object fields
    value: str
    unit: str
    precision: int = 2
    
    @classmethod
    def from_domain(cls, value_obj: YourValueObject) -> "ApiYourValueObject":
        """Convert domain value object to API value object."""
        return cls(
            value=value_obj.value,
            unit=value_obj.unit,
            precision=value_obj.precision
        )
    
    def to_domain(self) -> YourValueObject:
        """Convert API value object to domain value object."""
        return YourValueObject(
            value=self.value,
            unit=self.unit,
            precision=self.precision
        )
    
    @classmethod
    def from_orm_model(cls, orm_model: YourValueObjectORM) -> "ApiYourValueObject":
        """Convert ORM model to API value object."""
        return cls(
            value=orm_model.value,
            unit=orm_model.unit,
            precision=orm_model.precision
        )
    
    def to_orm_kwargs(self) -> dict:
        """Convert API value object to ORM kwargs."""
        return {
            "value": self.value,
            "unit": self.unit,
            "precision": self.precision
        }
```

### Value Object Validation

Value objects should implement comprehensive validation:

```python
from pydantic import Field, field_validator

class ApiMoney(BaseApiValueObject[Money, MoneyORM]):
    """API value object for monetary amounts."""
    
    amount: float = Field(..., ge=0, description="Amount must be non-negative")
    currency: str = Field(..., min_length=3, max_length=3, description="3-letter currency code")
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code format."""
        if not v.isupper():
            raise ValueError('Currency code must be uppercase')
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """Validate amount precision."""
        if round(v, 2) != v:
            raise ValueError('Amount cannot have more than 2 decimal places')
        return v
```

## Common Patterns

### Type Conversion Utilities

All schemas have access to `convert` utility for common conversions:

```python
# Available conversion methods
cls.convert.uuid_to_string(uuid_obj)      # UUID → string
cls.convert.string_to_uuid(uuid_string)   # string → UUID
cls.convert.datetime_to_isostring(dt)     # datetime → ISO string
cls.convert.isostring_to_datetime(iso)    # ISO string → datetime
cls.convert.set_to_frozenset(s)           # set → frozenset
cls.convert.frozenset_to_set(fs)          # frozenset → set
cls.convert.enum_to_string(enum_val)      # enum → string
cls.convert.string_to_enum(string, enum_cls)  # string → enum
```

### Standard Entity Fields

All entities inherit these standard fields from `BaseApiEntity`:

```python
# Standard entity fields
id: UUIDId                                # Unique identifier
created_at: datetime | None = None        # Creation timestamp
updated_at: datetime | None = None        # Last update timestamp
version: int = 1                          # Version for optimistic locking
discarded: bool = False                   # Soft delete flag
```

### Error Handling

Implement consistent error handling:

```python
try:
    domain_obj = api_schema.to_domain()
    return domain_obj
except Exception as e:
    raise ValueError(f"Failed to convert {self.__class__.__name__} to domain: {e}") from e
```

## Next Steps

For advanced patterns, see:
- [Advanced Patterns](./advanced-patterns.md)
- [Testing Guide](./testing-guide.md)
- [Code Examples](./examples/) 