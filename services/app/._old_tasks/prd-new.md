# PRD: API Schema Documentation Enhancement for AI Agent Onboarding

## Executive Summary

### Problem Statement
AI agents (primarily Claude-4-Sonnet via Cursor) struggle with Pydantic API schema implementation due to insufficient documentation of the four-layer conversion pattern (`to_domain`, `from_domain`, `from_orm_model`, `to_orm_kwargs`) and complex type handling between domain, API, and ORM layers.

### Proposed Solution
Enhance existing documentation with a focused "API Schema Pattern" section that provides clear guidance on:
- Immutable Pydantic API class implementation
- Type conversion strategies (set ↔ frozenset ↔ list)
- Computed properties vs stored attributes handling
- SQLAlchemy composite type integration
- Testing patterns for layer synchronization

### Business Value
- Reduced AI agent onboarding time for API-related tasks
- Improved code quality through better understanding of conversion patterns
- Decreased debugging time for type mismatch issues

### Success Criteria
- AI agents can implement API schema classes without type conversion errors
- Clear decision framework prevents common type mismatch pitfalls
- Testing patterns ensure layer synchronization validation

## Goals and Non-Goals

### Goals
1. Add "API Schema Pattern" section to `pattern-library.md`
2. Enhance "Data Layer Conversions" in `technical-specifications.md`
3. Document type mismatch patterns in `common-confusion-points.md`
4. Provide decision framework for type choices across layers

### Non-Goals (Out of Scope)
1. Implementing new API schema classes
2. Refactoring existing API schemas
3. Changing domain or ORM business logic
4. Major restructuring of existing documentation

## User Stories and Acceptance Criteria

### User Story 1: API Schema Implementation Guidance
**As a** Claude-4-Sonnet AI agent
**I want to** implement new Pydantic API schema classes
**So that** I can correctly handle data conversion between layers

**Acceptance Criteria:**
- [ ] Documentation shows immutable API class pattern with frozen=True
- [ ] Clear examples of all four conversion methods
- [ ] Type conversion patterns for collections are documented
- [ ] Examples show handling of computed vs stored properties

### User Story 2: Type Mismatch Resolution
**As a** Claude-4-Sonnet AI agent
**I want to** understand when type mismatches occur
**So that** I can choose appropriate types for each layer

**Acceptance Criteria:**
- [ ] Decision framework for set vs frozenset vs list usage
- [ ] Examples of computed properties in domain vs ORM columns
- [ ] SQLAlchemy composite type handling examples
- [ ] Common pitfalls and solutions documented

### User Story 3: Testing Pattern Implementation
**As a** Claude-4-Sonnet AI agent
**I want to** validate layer synchronization
**So that** I can ensure conversions work correctly

**Acceptance Criteria:**
- [ ] Test patterns for round-trip conversions
- [ ] Validation strategies for type compatibility
- [ ] Examples of testing computed property synchronization

## Technical Specifications

### Documentation Structure Updates

#### Pattern Library Enhancement
Add new section: **"API Schema Pattern"** after existing patterns

```markdown
## API Schema Pattern

### Pattern Overview
Pydantic API schemas serve as the boundary layer between external JSON and internal domain models, providing validation and type conversion across three layers:

1. **API Layer** (Pydantic) - Immutable validation and serialization
2. **Domain Layer** - Business logic with computed properties  
3. **ORM Layer** - SQLAlchemy models with database mappings

### Immutable API Class Implementation
```python
from pydantic import BaseModel, field_validator, ConfigDict

class ApiMeal(BaseModel):
    model_config = ConfigDict(frozen=True)  # CRITICAL: Immutability
    
    id: str
    name: str
    recipes: list[ApiRecipe]  # Always list for JSON serialization
    tags: frozenset[ApiTag]   # Immutable set internally
    
    @field_validator('recipes')
    @classmethod
    def validate_unique_recipes(cls, v: list[ApiRecipe]) -> list[ApiRecipe]:
        """Ensure recipe IDs are unique."""
        ids = [r.id for r in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate recipe IDs detected")
        return v
```

### The Four Conversion Methods

#### 1. `from_domain()` - Domain to API
```python
@classmethod
def from_domain(cls, domain_obj: Meal) -> "ApiMeal":
    """Convert domain object to API schema."""
    return cls(
        id=domain_obj.id,
        name=domain_obj.name,
        # Convert domain set to API list for JSON serialization
        recipes=[ApiRecipe.from_domain(r) for r in domain_obj.recipes],
        # Convert domain set to API frozenset for immutability
        tags=frozenset(ApiTag.from_domain(t) for t in domain_obj.tags),
    )
```

#### 2. `to_domain()` - API to Domain
```python
def to_domain(self) -> Meal:
    """Convert API schema to domain object."""
    return Meal(
        id=self.id,
        name=self.name,
        # Convert API list back to domain set
        recipes=set(r.to_domain() for r in self.recipes),
        # Convert API frozenset to domain set
        tags=set(t.to_domain() for t in self.tags),
    )
```

#### 3. `from_orm_model()` - ORM to API
```python
@classmethod
def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
    """Convert ORM model to API schema."""
    return cls(
        id=orm_model.id,
        name=orm_model.name,
        # ORM stores as list, convert to API list
        recipes=[ApiRecipe.from_orm_model(r) for r in orm_model.recipes],
        # Handle SQLAlchemy composite types
        nutri_facts=ApiNutriFacts(**orm_model.nutri_facts.__dict__) if orm_model.nutri_facts else None,
    )
```

#### 4. `to_orm_kwargs()` - API to ORM Data
```python
def to_orm_kwargs(self) -> dict[str, Any]:
    """Convert API schema to ORM model kwargs."""
    return {
        "id": self.id,
        "name": self.name,
        # Convert API list to ORM list
        "recipes": [r.to_orm_kwargs() for r in self.recipes],
        # Convert frozenset to list for ORM storage
        "tags": [t.to_orm_kwargs() for t in self.tags],
    }
```

### Type Conversion Decision Framework

| Use Case | Domain Layer | API Layer | ORM Layer | Reasoning |
|----------|-------------|-----------|-----------|-----------|
| **Unique Collections** | `set[Recipe]` | `list[ApiRecipe]` | `list[RecipeSaModel]` | Domain ensures uniqueness, API/ORM use lists for serialization/storage |
| **Immutable Collections** | `frozenset[Tag]` | `frozenset[ApiTag]` | `list[TagSaModel]` | Preserve immutability in domain/API, ORM uses lists |
| **Computed Properties** | `@cached_property calories` | `calories: float` | `calories: Column(Float)` | Domain computes, API exposes, ORM stores for querying |
| **Composite Types** | `NutriFacts` object | `ApiNutriFacts` | SQLAlchemy `Composite` | Rich domain object, validated API, efficient ORM storage |

### Common Type Mismatch Patterns

#### Pattern 1: Computed vs Stored Properties
```python
# Domain: Computed property
class Meal:
    @cached_property
    def total_calories(self) -> float:
        return sum(recipe.calories for recipe in self.recipes)

# API: Explicit field for client consumption
class ApiMeal(BaseModel):
    total_calories: float  # Sent to client for display

# ORM: Stored column for efficient querying
class MealSaModel(Base):
    total_calories = Column(Float)  # Stored for WHERE clauses
```

#### Pattern 2: SQLAlchemy Composite Handling
```python
# Domain
class NutriFacts:
    calories: float
    protein: float

# ORM with composite
class MealSaModel(Base):
    nutri_facts = composite(NutriFactsComposite, 'calories', 'protein')

# API conversion from ORM composite
@classmethod
def from_orm_model(cls, orm_model: MealSaModel) -> "ApiMeal":
    return cls(
        # Handle composite by accessing __dict__
        nutri_facts=ApiNutriFacts(**orm_model.nutri_facts.__dict__) if orm_model.nutri_facts else None
    )
```

### Testing Patterns for Layer Synchronization

#### Round-trip Conversion Test
```python
def test_meal_round_trip_conversion(sample_meal_domain):
    """Test Domain → API → ORM → API → Domain preserves data."""
    # Domain to API
    api_meal = ApiMeal.from_domain(sample_meal_domain)
    
    # API to ORM kwargs and back
    orm_kwargs = api_meal.to_orm_kwargs()
    orm_model = MealSaModel(**orm_kwargs)
    api_meal_2 = ApiMeal.from_orm_model(orm_model)
    
    # Back to domain
    domain_meal_2 = api_meal_2.to_domain()
    
    # Assert equality (custom __eq__ needed)
    assert domain_meal_2.id == sample_meal_domain.id
    assert domain_meal_2.name == sample_meal_domain.name
    assert len(domain_meal_2.recipes) == len(sample_meal_domain.recipes)
```

#### Type Compatibility Test
```python
def test_collection_type_compatibility():
    """Ensure collections convert correctly between layers."""
    domain_tags = {Tag("vegan"), Tag("gluten-free")}
    
    # Domain set → API frozenset
    api_tags = frozenset(ApiTag.from_domain(t) for t in domain_tags)
    assert isinstance(api_tags, frozenset)
    
    # API frozenset → ORM list
    orm_tags = [t.to_orm_kwargs() for t in api_tags]
    assert isinstance(orm_tags, list)
    
    # Round trip preserves content
    reconstructed = set(Tag.from_orm_kwargs(kwargs) for kwargs in orm_tags)
    assert reconstructed == domain_tags
```

### Common Pitfalls and Solutions

❌ **Mutable API Classes**
```python
class ApiMeal(BaseModel):  # Missing frozen=True
    recipes: list[ApiRecipe]
    
meal = ApiMeal(...)
meal.recipes.append(new_recipe)  # Mutates object!
```

✅ **Immutable API Classes**
```python
class ApiMeal(BaseModel):
    model_config = ConfigDict(frozen=True)
    recipes: list[ApiRecipe]
    
# meal.recipes.append(new_recipe)  # Raises FrozenInstanceError
```

❌ **Inconsistent Collection Types**
```python
# Domain uses set, API uses set, ORM expects list
def to_orm_kwargs(self) -> dict:
    return {"tags": self.tags}  # TypeError: set not serializable
```

✅ **Consistent Collection Conversion**
```python
def to_orm_kwargs(self) -> dict:
    return {"tags": [t.to_orm_kwargs() for t in self.tags]}
```

❌ **Missing Computed Property Sync**
```python
# Domain computes calories, but ORM doesn't store it
# Later queries fail: WHERE total_calories > 500
```

✅ **Computed Property Storage**
```python
# Store computed values in ORM for querying
def save_meal(meal: Meal):
    orm_kwargs = api_meal.to_orm_kwargs()
    orm_kwargs["total_calories"] = meal.total_calories  # Store computed value
```
```

#### Technical Specifications Enhancement
Update existing section with:

```markdown
### Data Layer Conversions

The system uses a three-layer architecture with specific type conversion patterns:

**Type Flow Example: Recipe Collections**
```
Domain Layer: set[Recipe] (business uniqueness)
     ↓ from_domain()
API Layer: list[ApiRecipe] (JSON serialization)
     ↓ to_orm_kwargs()  
ORM Layer: list[RecipeSaModel] (database storage)
     ↓ from_orm_model()
API Layer: list[ApiRecipe] (response serialization)
     ↓ to_domain()
Domain Layer: set[Recipe] (business logic)
```

**Computed Property Handling**
- Domain: `@cached_property` for expensive calculations
- API: Regular field for client consumption  
- ORM: Stored column for efficient querying

**SQLAlchemy Composite Integration**
```python
# ORM Model
class MealSaModel(Base):
    nutri_facts = composite(NutriFactsComposite, 'calories', 'protein', 'carbs')

# API Conversion
@classmethod
def from_orm_model(cls, orm_model: MealSaModel):
    return cls(
        nutri_facts=ApiNutriFacts(**orm_model.nutri_facts.__dict__) 
        if orm_model.nutri_facts else None
    )
```
```

#### Common Confusion Points Addition
Add new section:

```markdown
### 5. API Schema Layer Conversion Confusion

**Issue Description**:
AI agents encounter type mismatches and conversion errors when implementing Pydantic API schema classes, particularly around collection types and computed properties.

**What Causes This Confusion**:
- Type differences between layers (set vs frozenset vs list)
- Computed properties in domain vs stored columns in ORM
- SQLAlchemy composite type handling
- Missing immutability requirements

**Symptoms**:
- `TypeError: Object of type set is not JSON serializable`
- Mutable API objects causing unexpected side effects
- Round-trip conversion tests failing
- Query errors when computed properties aren't stored

**Resolution Steps**:
1. **Always use `frozen=True`** in API model configuration
2. **Follow type conversion patterns**: Domain sets → API lists → ORM lists
3. **Store computed properties** in ORM for querying capabilities
4. **Handle composites** via `.__dict__` unpacking

**Prevention Strategy**:
- Use the API Schema Pattern from pattern library
- Implement round-trip conversion tests
- Follow the type decision framework for collection choices
```

## Implementation Plan

### Phase 1: Pattern Library Update (2 days)
- [ ] Add "API Schema Pattern" section after existing patterns
- [ ] Include complete examples with all four conversion methods
- [ ] Document type conversion decision framework
- [ ] Add testing patterns and common pitfalls

### Phase 2: Technical Specifications Enhancement (1 day)
- [ ] Expand "Data Layer Conversions" section
- [ ] Add SQLAlchemy composite examples
- [ ] Document computed property handling strategy

### Phase 3: Common Confusion Points Addition (1 day)
- [ ] Add API schema conversion confusion point
- [ ] Document symptoms and resolution steps
- [ ] Include prevention strategies

### Phase 4: Cross-Reference Integration (0.5 days)
- [ ] Add navigation links between related sections
- [ ] Update quick reference guide with API schema patterns
- [ ] Ensure consistency across all documents

## Success Metrics

### Immediate Indicators
- AI agents can implement immutable API classes without guidance
- Type conversion errors eliminated in new implementations
- Round-trip conversion tests pass on first attempt

### Long-term Metrics
- Reduced time for API-related tasks (target: 20% improvement)
- Fewer follow-up questions about type handling
- Improved code quality in API layer implementations

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Examples become outdated | Medium | Medium | Link to existing codebase examples |
| Pattern complexity overwhelms beginners | Low | Medium | Progressive complexity with simple examples first |
| Inconsistency with existing code | Low | High | Validate examples against current ApiMeal implementation |

## Monitoring and Success Validation

### Documentation Quality Metrics
- Examples remain executable and current
- Cross-references stay accurate
- Pattern guidance prevents common errors

### AI Agent Performance Indicators  
- Successful API schema implementations without iteration
- Correct type handling in conversion methods
- Effective testing pattern usage

## Dependencies and Prerequisites

### Content Dependencies
- Current `ApiMeal` class as primary example reference
- Existing pattern library structure
- Technical specifications format

### Review Requirements
- Technical accuracy validation against codebase
- Consistency check with existing documentation style
- AI agent testing with sample scenarios

## Timeline and Milestones

**Total Estimated Time**: 4.5 days

### Key Milestones
- Phase 1 Complete: Pattern library enhanced with API schema guidance
- Phase 2 Complete: Technical specifications updated with conversion details  
- Phase 3 Complete: Common confusion points documented
- Final Review: Documentation validated and cross-referenced

## Open Questions and Decisions

### Pending Decisions
1. **Example Complexity Level**
   - Options: [Simple conceptual, Real codebase examples, Progressive complexity]
   - Recommendation: Progressive complexity starting with real ApiMeal examples

2. **Testing Pattern Detail Level**
   - Options: [Basic round-trip only, Comprehensive test suite examples, Custom assertion helpers]
   - Recommendation: Basic round-trip with references to comprehensive patterns

### Required Approvals
- [ ] Content accuracy review against current codebase
- [ ] Documentation style consistency validation
- [ ] AI agent scenario testing approval