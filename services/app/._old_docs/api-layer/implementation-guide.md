# API Layer Implementation Guide

## BaseApiModel Configuration

### Core Configuration Deep Dive

The `BaseApiModel` uses a comprehensive `ConfigDict` that enforces strict security and performance standards:

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

### Configuration Rationale

#### Security Settings
- **`frozen=True`**: Prevents accidental mutation after creation, ensuring data integrity
- **`strict=True`**: Rejects implicit type conversions (e.g., `"123"` → `123`), forcing explicit validation
- **`extra='forbid'`**: Blocks unknown fields, preventing injection attacks
- **`validate_assignment=True`**: Validates any field assignments (even though frozen prevents them)

#### Conversion Settings
- **`from_attributes=True`**: Enables ORM integration via `model_validate(orm_object)`
- **`populate_by_name=True`**: Supports field aliases for API compatibility
- **`use_enum_values=True`**: Serializes enums as values, not objects (`"active"` not `<Status.ACTIVE>`)

#### Performance Settings
- **`arbitrary_types_allowed=False`**: Forces explicit type validation
- **`revalidate_instances='never'`**: Optimizes performance for immutable objects

## Command Implementation Patterns

### BaseApiCommand Pattern

Commands represent user actions/intentions flowing from API to Domain layer only.

```python
class BaseApiCommand(BaseModel, Generic[C]):
    # Strict validation configuration
    model_config = MODEL_CONFIG
    
    # Type conversion utility
    convert: ClassVar[TypeConversionUtility] = CONVERT

    def to_domain(self) -> C:
        """Convert API command to domain command with type conversions."""
        raise NotImplementedError("Subclasses must implement to_domain()")
```

### Annotated fields Command Pattern

```python

UUIDId = Annotated[
    str,
    Field(..., description="Unique identifier for the entity"), 
    AfterValidator(validate_uuid_format),
]

UUIDIdOptional = Annotated[
    str | None,
    Field(default=None, description="Unique identifier for the entity"), 
    AfterValidator(validate_uuid_format),
]

MealName = Annotated[
    str,
    BeforeValidator(validate_optional_text),
    Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the meal",
    ),
]

MealDescription = Annotated[
    str | None,
    Field(None, description="Detailed description"),
]

MealNotes = Annotated[
    str | None,
    Field(None, description="Additional notes"),
]

MealImageUrl = Annotated[
    str | None,
    Field(None, description="URL of the meal image"),
]
MealRecipes = Annotated[
    "List[ApiRecipe]",  # Forward reference to avoid circular import
    Field(default_factory=list, description="List of recipes in the meal"),
]

MealTags = Annotated[
    'FrozenSet[ApiTag]',  # Forward reference to avoid circular import
    Field(default_factory=frozenset, description="Frozenset of tags associated with the meal"),
]

MealLike = Annotated[
    bool | None,
    Field(None, description="Whether the meal is liked"),
]

```

### Create Command Pattern

```python
class ApiCreateMeal(BaseApiCommand[CreateMeal]):
    """API command for creating a new meal."""
    
    name: MealName | None = None
    menu_id: UUIDIdOptional
    description: MealDescription
    recipes: MealRecipes
    tags: MealTags
    notes: MealNotes
    like: MealLike
    image_url: MealImageUrl

    def to_domain(self) -> CreateMeal:
        """Convert to domain command with proper type conversions."""
        return CreateMeal(
            name=self.name,
            author_id=self.author_id,  # UUIDId automatically handled by Pydantic
            menu_id=self.menu_id,
            recipes=[recipe.to_domain() for recipe in self.recipes],
            tags=set(tag.to_domain() for tag in self.tags),  # frozenset → set
            description=self.description,
            notes=self.notes,
            image_url=self.image_url,
        )
```

### Update Command Pattern

```python
class ApiAttributesToUpdateOnMeal(BaseApiCommand[UpdateMeal]):
    """API for attributes that can be updated on a meal."""

    name: MealName | None = None
    menu_id: UUIDIdOptional
    description: MealDescription
    recipes: MealRecipes
    tags: MealTags
    notes: MealNotes
    like: MealLike
    image_url: MealImageUrl

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )

class ApiUpdateMeal(BaseApiCommand[UpdateMeal]):
    """API command for updating an existing meal."""

    meal_id: UUIDId
    updates: ApiAttributesToUpdateOnMeal

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateMeal(
                meal_id=self.meal_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_meal(cls, api_meal: ApiMeal) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal."""
        attributes_to_update = {
            key: getattr(api_meal, key) for key in ApiMeal.model_fields.keys()
        }
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )

```

### Delete Command Pattern

```python
class ApiDeleteMeal(BaseApiCommand[DeleteMeal]):
    """API command for deleting a meal."""
    
    meal_id: UUIDId

    def to_domain(self) -> DeleteMeal:
        """Convert to domain command."""
        return DeleteMeal(meal_id=self.meal_id)
```

## Entity Implementation Patterns

### BaseApiEntity Pattern

Entities represent persistent domain objects with identity and lifecycle fields.

```python
class BaseApiEntity(BaseApiModel[E, S]):
    """Base class for entity schemas with common entity fields."""
    
    # Standard entity fields
    id: UUIDId
    created_at: Annotated[datetime, Field(..., description="ISO timestamp when entity was created")]
    updated_at: Annotated[datetime, Field(..., description="ISO timestamp when entity was last updated")]
    version: Annotated[int, Field(default=1, ge=1, description="Version number for optimistic locking")]
    discarded: Annotated[bool, Field(default=False, description="Soft delete flag indicating if entity is discarded")]
```

### Entity Implementation Example

```python
class ApiMeal(BaseApiEntity[Meal, MealSaModel]):
    """API schema for Meal entity."""
    
    # Business fields
    name: MealName
    author_id: UUIDId
    menu_id: UUIDIdOptional
    recipes: MealRecipes
    tags: MealTags
    description: MealDescription
    notes: MealNotes
    like: MealLike
    image_url: MealImageUrl
    
    # Computed fields (materialized from domain)
    nutri_facts: MealNutriFacts
    weight_in_grams: MealWeightInGrams
    calorie_density: MealCalorieDensity
    carbo_percentage: MealCarboPercentage
    protein_percentage: MealProteinPercentage
    total_fat_percentage: MealTotalFatPercentage

    @classmethod
    def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
        """Convert domain entity to API schema."""
        return cls(
            id=domain_obj.id,
            name=domain_obj.name,
            author_id=domain_obj.author_id,
            menu_id=domain_obj.menu_id,
            recipes=[ApiRecipe.from_domain(r) for r in domain_obj.recipes],
            tags=frozenset(ApiTag.from_domain(t) for t in domain_obj.tags),
            description=domain_obj.description,
            notes=domain_obj.notes,
            image_url=domain_obj.image_url,
            # Materialize computed properties
            nutri_facts=ApiNutriFacts.from_domain(domain_obj.nutri_facts) if domain_obj.nutri_facts else None,
            weight_in_grams=domain_obj.weight_in_grams,
            calorie_density=domain_obj.calorie_density,
            carbo_percentage=domain_obj.carbo_percentage,
            protein_percentage=domain_obj.protein_percentage,
            total_fat_percentage=domain_obj.total_fat_percentage,
            # Lifecycle fields
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            version=domain_obj.version,
            discarded=domain_obj.discarded,
        )

    def to_domain(self) -> Meal:
        """Convert API schema to domain entity."""
        return Meal(
            id=self.id,
            name=self.name,
            author_id=self.author_id,
            menu_id=self.menu_id,
            recipes=[r.to_domain() for r in self.recipes],
            tags=set(t.to_domain() for t in self.tags),
            description=self.description,
            notes=self.notes,
            like=self.like,
            image_url=self.image_url,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
        """Convert ORM model to API schema."""
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
            image_url=orm_model.image_url,
            # nutri_facts is a Mapped[NutriFactsSaModel] composite in the ORM model
            # NutriFactsSaModel is a dataclass
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

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs."""
        return {
            "id": self.id,
            "name": self.name,
            "author_id": self.author_id,
            "menu_id": self.menu_id,
            "recipes": [r.to_orm_kwargs() for r in self.recipes],
            "tags": [t.to_orm_kwargs() for t in self.tags],
            "description": self.description,
            "notes": self.notes,
            "like": self.like,
            "image_url": self.image_url,
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

### Entity Usage Patterns

#### Domain Entity → ApiEntity → JSON Response Flow

The typical flow for entity conversion from domain to API response follows this pattern:

```python
# Step 1: Domain Entity → API Entity
domain_meal = get_meal_from_repository(meal_id)
api_meal = ApiMeal.from_domain(domain_meal)

# Step 2: API Entity → JSON Response
json_response = api_meal.custom_dump_json()

# Step 3: Return to client
return JSONResponse(content=json_response)
```

#### Detailed Flow Example

```python
def get_meal_endpoint(meal_id: str) -> JSONResponse:
    """
    Example endpoint showing complete entity conversion flow.
    
    Flow: Repository → Domain Entity → API Entity → JSON → Client
    """
    try:
        # 1. Get domain entity from repository
        domain_meal: Meal = meal_repository.get_by_id(meal_id)
        
        # 2. Convert domain entity to API schema
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # 3. Serialize to JSON with custom formatting
        json_response = api_meal.custom_dump_json()
        
        # 4. Return HTTP response
        return JSONResponse(
            content=json_response,
            status_code=200,
            headers={"Content-Type": "application/json"}
        )
    
    except EntityNotFoundError:
        return JSONResponse(
            content={"error": "Meal not found"},
            status_code=404
        )
    except ValidationError as e:
        return JSONResponse(
            content={"error": f"Validation failed: {e}"},
            status_code=400
        )
```

#### Batch Processing Pattern

```python
def get_meals_endpoint(author_id: str) -> JSONResponse:
    """
    Example endpoint showing batch entity conversion.
    
    Demonstrates performance considerations for multiple entities.
    """
    try:
        # 1. Get multiple domain entities
        domain_meals: List[Meal] = meal_repository.get_by_author(author_id)
        
        # 2. Convert all entities to API schemas
        api_meals = [ApiMeal.from_domain(meal) for meal in domain_meals]
        
        # 3. Serialize to JSON array
        json_response = [meal.custom_dump_json() for meal in api_meals]
        
        # 4. Return paginated response
        return JSONResponse(
            content={
                "meals": json_response,
                "count": len(api_meals),
                "page": 1,
                "total_pages": 1
            },
            status_code=200
        )
    
    except Exception as e:
        return JSONResponse(
            content={"error": f"Failed to retrieve meals: {e}"},
            status_code=500
        )
```

#### Testing Methods: Required Entity Methods

All API entities must implement these four core methods for proper testing and integration:

##### 1. `to_domain()` Method Testing

```python
def test_api_meal_to_domain_conversion():
    """Test API entity to domain entity conversion."""
    # Create API entity
    api_meal = ApiMeal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        menu_id="123e4567-e89b-12d3-a456-426614174002",
        recipes=[],
        tags=frozenset(),
        description="Test description",
        notes="Test notes",
        like=True,
        image_url="https://example.com/image.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
    )
    
    # Convert to domain
    domain_meal = api_meal.to_domain()
    
    # Verify conversion
    assert domain_meal.id == api_meal.id
    assert domain_meal.name == api_meal.name
    assert domain_meal.author_id == api_meal.author_id
    assert isinstance(domain_meal.tags, set)  # frozenset → set
    assert domain_meal.version == api_meal.version
```

##### 2. `to_orm_kwargs()` Method Testing

```python
def test_api_meal_to_orm_kwargs():
    """Test API entity to ORM kwargs conversion."""
    api_meal = ApiMeal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        # ... other fields
    )
    
    # Convert to ORM kwargs
    orm_kwargs = api_meal.to_orm_kwargs()
    
    # Verify structure
    assert "id" in orm_kwargs
    assert "name" in orm_kwargs
    assert "author_id" in orm_kwargs
    assert "created_at" in orm_kwargs
    assert "updated_at" in orm_kwargs
    assert "version" in orm_kwargs
    assert "discarded" in orm_kwargs
    
    # Verify types are ORM-compatible
    assert isinstance(orm_kwargs["tags"], list)  # frozenset → list
    assert isinstance(orm_kwargs["recipes"], list)
```

##### 3. `from_orm_model()` Method Testing

```python
def test_api_meal_from_orm_model():
    """Test ORM model to API entity conversion."""
    # Create mock ORM model
    orm_meal = MealSaModel(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        menu_id="123e4567-e89b-12d3-a456-426614174002",
        recipes=[],
        tags=[],
        description="Test description",
        notes="Test notes",
        like=True,
        image_url="https://example.com/image.jpg",
        nutri_facts=None,
        weight_in_grams=500.0,
        calorie_density=2.1,
        carbo_percentage=45.0,
        protein_percentage=25.0,
        total_fat_percentage=30.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
    )
    
    # Convert from ORM
    api_meal = ApiMeal.from_orm_model(orm_meal)
    
    # Verify conversion
    assert api_meal.id == orm_meal.id
    assert api_meal.name == orm_meal.name
    assert api_meal.author_id == orm_meal.author_id
    assert isinstance(api_meal.tags, frozenset)  # list → frozenset
    assert api_meal.version == orm_meal.version
```

##### 4. `from_domain()` Method Testing

```python
def test_api_meal_from_domain():
    """Test domain entity to API entity conversion."""
    # Create domain entity
    domain_meal = Meal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        menu_id="123e4567-e89b-12d3-a456-426614174002",
        recipes=[],
        tags=set(),  # set in domain
        description="Test description",
        notes="Test notes",
        like=True,
        image_url="https://example.com/image.jpg",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
    )
    
    # Convert from domain
    api_meal = ApiMeal.from_domain(domain_meal)
    
    # Verify conversion
    assert api_meal.id == domain_meal.id
    assert api_meal.name == domain_meal.name
    assert api_meal.author_id == domain_meal.author_id
    assert isinstance(api_meal.tags, frozenset)  # set → frozenset
    assert api_meal.version == domain_meal.version
```

#### Round-Trip Testing Pattern

```python
def test_api_meal_round_trip_conversion():
    """Test full round-trip conversion: Domain → API → Domain."""
    # Create original domain entity
    original_domain = Meal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Original Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        menu_id=None,
        recipes=[],
        tags=set([
            Tag(key="cuisine", value="italian", author_id="123e4567-e89b-12d3-a456-426614174001", type="cuisine")
        ]),
        description="Original description",
        notes="Original notes",
        like=False,
        image_url=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
        discarded=False,
    )
    
    # Convert to API and back
    api_meal = ApiMeal.from_domain(original_domain)
    converted_domain = api_meal.to_domain()
    
    # Verify round-trip integrity
    assert converted_domain.id == original_domain.id
    assert converted_domain.name == original_domain.name
    assert converted_domain.author_id == original_domain.author_id
    assert converted_domain.tags == original_domain.tags  # set equality
    assert converted_domain.version == original_domain.version
    assert converted_domain.discarded == original_domain.discarded
```

#### Performance Testing Pattern

```python
def test_api_meal_performance():
    """Test performance of entity conversions."""
    import time
    
    # Create large domain entity
    large_domain_meal = create_meal_with_many_recipes(recipe_count=100)
    
    # Measure conversion performance
    start_time = time.time()
    api_meal = ApiMeal.from_domain(large_domain_meal)
    conversion_time = time.time() - start_time
    
    start_time = time.time()
    json_output = api_meal.custom_dump_json()
    serialization_time = time.time() - start_time
    
    # Assert performance thresholds
    assert conversion_time < 0.1  # 100ms max for conversion
    assert serialization_time < 0.2  # 200ms max for JSON serialization
    assert len(json_output) > 0  # Ensure valid output
```

#### Integration Testing Pattern

```python
def test_api_meal_integration_with_orm():
    """Test integration between API entities and ORM models."""
    # Create API entity
    api_meal = ApiMeal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Integration Test Meal",
        author_id="123e4567-e89b-12d3-a456-426614174001",
        # ... other fields
    )
    
    # Convert to ORM kwargs
    orm_kwargs = api_meal.to_orm_kwargs()
    
    # Create ORM model
    orm_meal = MealSaModel(**orm_kwargs)
    
    # Convert back to API
    api_meal_from_orm = ApiMeal.from_orm_model(orm_meal)
    
    # Verify integrity
    assert api_meal.id == api_meal_from_orm.id
    assert api_meal.name == api_meal_from_orm.name
    assert api_meal.author_id == api_meal_from_orm.author_id
```

#### Error Handling Testing

```python
def test_api_meal_error_handling():
    """Test error handling in entity conversions."""
    # Test invalid data
    with pytest.raises(ValidationError):
        ApiMeal(
            id="invalid-uuid",  # Invalid UUID format
            name="",  # Empty name
            author_id="123e4567-e89b-12d3-a456-426614174001",
            # ... other fields
        )
    
    # Test conversion errors
    invalid_api_meal = ApiMeal(
        id="123e4567-e89b-12d3-a456-426614174000",
        name="Test Meal",
        author_id="invalid-uuid",  # This should cause to_domain() to fail
        # ... other fields
    )
    
    with pytest.raises(ValueError, match="Failed to convert"):
        invalid_api_meal.to_domain()
```

## Value Object Implementation Patterns

### BaseApiValueObject Inheritance Pattern

Value objects represent immutable concepts without identity, defined by their attributes rather than having a unique ID. They inherit from `BaseApiValueObject` which provides the four-layer conversion pattern.

```python
class BaseApiValueObject(BaseApiModel[V, S]):
    """Enhanced base class for value object schemas.
    
    Value objects represent concepts that are defined by their attributes rather than
    their identity. They are immutable and should implement equality based on their values.
    
    Characteristics:
    - No identity field (no ID)
    - Immutable by nature (frozen=True enforced)
    - Equality based on all field values
    - Used for concepts like addresses, money amounts, measurements, etc.
    
    Required Methods (must be implemented by subclasses):
    - from_domain() -> Self: Convert domain value object to API schema
    - to_domain() -> V: Convert API schema to domain value object
    - from_orm_model() -> Self: Convert ORM model/composite to API schema
    - to_orm_kwargs() -> dict: Convert API schema to ORM kwargs
    """
    pass
```

### Key Value Object Characteristics

**Immutability**: Value objects are frozen and cannot be modified after creation
```python
# ✅ Correct - BaseApiValueObject enforces immutability
class ApiAddress(BaseApiValueObject[Address, AddressSaModel]):
    street: str | None = None
    city: str | None = None
    # Fields are automatically immutable due to frozen=True
```

**No Identity**: Value objects don't have ID fields or lifecycle timestamps
```python
# ❌ Incorrect - Value objects should not have identity fields
class ApiAddress(BaseApiValueObject):
    id: str  # Wrong! Value objects don't have identity
    created_at: datetime  # Wrong! No lifecycle fields
    
# ✅ Correct - Only business attributes
class ApiAddress(BaseApiValueObject):
    street: str | None = None
    city: str | None = None
```

**Equality by Values**: Two value objects are equal if all their fields are equal
```python
addr1 = ApiAddress(street="123 Main St", city="Boston")
addr2 = ApiAddress(street="123 Main St", city="Boston")
assert addr1.model_dump() == addr2.model_dump()  # Equal by values
```

### Simple Value Object Implementation

```python
class ApiNutriValue(BaseApiValueObject[NutriValue, SaBase]):
    """Simple value object for nutritional values."""
    
    unit: MeasureUnit
    value: NonNegativeFloat

    @classmethod
    def from_domain(cls, domain_obj: NutriValue) -> "ApiNutriValue":
        """Convert domain value object to API schema."""
        return cls(
            unit=domain_obj.unit,
            value=domain_obj.value,
        )

    def to_domain(self) -> NutriValue:
        """Convert API schema to domain value object."""
        return NutriValue(
            unit=MeasureUnit(self.unit),
            value=self.value,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any):
        """ORM conversion not applicable for this value object."""
        raise NotImplementedError("ORM model stores only value, not unit")

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM kwargs, excluding unit."""
        return self.model_dump(exclude={'unit'})
```

### Complex Value Object with Text Validation

```python
class ApiAddress(BaseApiValueObject[Address, AddressSaModel]):
    """Enhanced address schema with comprehensive field validation."""
    
    # Text fields with validation using Annotated types
    street: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Street name with proper trimming and validation"
    )]
    number: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Street number or identifier"
    )]
    zip_code: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Postal/ZIP code"
    )]
    city: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="City name with proper validation"
    )]
    
    # Enum field with automatic conversion
    state: Annotated[State | None, Field(
        default=None, description="State enum (Pydantic handles string conversion)"
    )]
    
    complement: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Additional address information"
    )]

    @classmethod
    def from_domain(cls, domain_obj: Address) -> "ApiAddress":
        """Convert domain Address to API schema."""
        return cls(
            street=domain_obj.street,
            number=domain_obj.number,
            zip_code=domain_obj.zip_code,
            city=domain_obj.city,
            state=domain_obj.state,  # Pydantic handles enum conversion
            complement=domain_obj.complement,
        )

    def to_domain(self) -> Address:
        """Convert API schema to domain Address."""
        return Address(
            street=self.street,
            number=self.number,
            zip_code=self.zip_code,
            city=self.city,
            state=State(self.state) if self.state else None,
            complement=self.complement,
        )

    @classmethod
    def from_orm_model(cls, orm_model: AddressSaModel) -> "ApiAddress":
        """Convert ORM composite to API schema."""
        return cls(
            street=orm_model.street,
            number=orm_model.number,
            zip_code=orm_model.zip_code,
            city=orm_model.city,
            state=State(orm_model.state) if orm_model.state else None,
            complement=orm_model.complement,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM kwargs."""
        return {
            'street': self.street,
            'number': self.number,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,  # Already string due to use_enum_values=True
            'complement': self.complement,
        }
```

### Advanced Value Object with Collections

```python
class ApiContactInfo(BaseApiValueObject[ContactInfo, ContactInfoSaModel]):
    """Complex value object demonstrating collection handling and validation."""
    
    # Simple fields with custom field types
    main_phone: PhoneFieldOptional = None
    main_email: EmailFieldOptional = None
    
    # Collections using frozenset for immutability
    all_phones: frozenset[str] = Field(default_factory=frozenset)
    all_emails: frozenset[str] = Field(default_factory=frozenset)

    @field_validator('all_phones')
    @classmethod
    def validate_all_phones(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate each phone number in the collection."""
        if not v:
            return v
        
        validated_phones = frozenset()
        for phone in v:
            if phone:  # Skip empty strings
                validated_phone = validate_phone_format(phone)
                if validated_phone:
                    validated_phones = validated_phones | {validated_phone}
        
        return validated_phones

    @field_validator('all_emails')
    @classmethod
    def validate_all_emails(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate each email in the collection."""
        if not v:
            return v
        
        validated_emails = frozenset()
        for email in v:
            if email:  # Skip empty strings
                validated_email = validate_email_format(email)
                if validated_email:
                    validated_emails = validated_emails | {validated_email}
        
        return validated_emails

    @classmethod
    def from_domain(cls, domain_obj: ContactInfo) -> "ApiContactInfo":
        """Convert domain with set → frozenset conversion."""
        return cls(
            main_phone=domain_obj.main_phone,
            main_email=domain_obj.main_email,
            all_phones=frozenset(domain_obj.all_phones),  # set → frozenset
            all_emails=frozenset(domain_obj.all_emails),  # set → frozenset
        )

    def to_domain(self) -> ContactInfo:
        """Convert API with frozenset → set conversion."""
        return ContactInfo(
            main_phone=self.main_phone,
            main_email=self.main_email,
            all_phones=set(self.all_phones),  # frozenset → set
            all_emails=set(self.all_emails),  # frozenset → set
        )

    @classmethod
    def from_orm_model(cls, orm_model: ContactInfoSaModel) -> "ApiContactInfo":
        """Convert ORM with list → frozenset conversion."""
        return cls(
            main_phone=orm_model.main_phone,
            main_email=orm_model.main_email,
            all_phones=frozenset(orm_model.all_phones or []),  # list → frozenset
            all_emails=frozenset(orm_model.all_emails or []),  # list → frozenset
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API with frozenset → list conversion."""
        return {
            "main_phone": self.main_phone,
            "main_email": self.main_email,
            "all_phones": list(self.all_phones),  # frozenset → list
            "all_emails": list(self.all_emails),  # frozenset → list
        }
```

### Value Object Validation Patterns

#### 1. Field-Level Validation with BeforeValidator

```python
# Text field validation
street: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
    default=None, description="Street name with trimming and validation"
)]

# Email field validation
email: Annotated[str | None, BeforeValidator(validate_email_format), Field(
    default=None, description="Email with format validation"
)]

# Phone field validation
phone: Annotated[str | None, BeforeValidator(validate_phone_format), Field(
    default=None, description="Phone with international format support"
)]
```

#### 2. Collection Validation with field_validator

```python
@field_validator('all_phones')
@classmethod
def validate_all_phones(cls, v: frozenset[str]) -> frozenset[str]:
    """Validate each item in a collection."""
    if not v:
        return v
    
    validated_items = frozenset()
    for item in v:
        if item:  # Skip empty strings
            validated_item = validate_phone_format(item)
            if validated_item:
                validated_items = validated_items | {validated_item}
    
    return validated_items
```

#### 3. Cross-Field Validation with model_validator

```python
@model_validator(mode='after')
def validate_address_completeness(self) -> 'ApiAddress':
    """Validate that essential address components are present."""
    if self.street and not self.city:
        raise ValueError("City is required when street is provided")
    
    if self.zip_code and not self.state:
        raise ValueError("State is required when zip code is provided")
    
    return self
```

#### 4. Enum Validation with Automatic Conversion

```python
# Enum field - Pydantic handles string ↔ enum conversion
state: State | None = None

# In to_domain() method
state=State(self.state) if self.state else None

# In from_orm_model() method  
state=State(orm_model.state) if orm_model.state else None
```