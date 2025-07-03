# API Schema Migration Guide

## Overview

This guide provides a systematic approach for migrating existing API schemas to comply with the established patterns documented in this project. Based on comprehensive analysis of 90+ schema files, this guide addresses the most common issues and provides step-by-step migration procedures.

## 🎯 Migration Objectives

### Primary Goals
1. **Pattern Compliance**: Ensure all schemas follow documented four-layer conversion patterns
2. **Validation Completeness**: Add appropriate field validation where missing
3. **Performance Optimization**: Implement TypeAdapter best practices
4. **Type Safety**: Correct type conversion patterns throughout all layers
5. **Documentation Alignment**: Ensure implementations match documented best practices

### Success Metrics
- **100% Pattern Compliance**: All schemas implement required conversion methods
- **Complete Validation Coverage**: All fields have appropriate validation patterns
- **Performance Standards**: All TypeAdapters meet established benchmarks
- **Zero Breaking Changes**: All migrations maintain backward compatibility

## 🔍 Assessment Phase

### Pre-Migration Assessment Checklist

Before beginning migration, evaluate each schema against these criteria:

#### 1. Four-Layer Conversion Compliance
```bash
# Check if schema implements all required methods
grep -r "to_domain\|from_domain\|from_orm_model\|to_orm_kwargs" src/contexts/*/api_schemas/
```

**Required Methods by Schema Type:**
- **Entity Schemas**: `to_domain()`, `from_domain()`, `from_orm_model()`, `to_orm_kwargs()`
- **Value Object Schemas**: `to_domain()`, `from_domain()`, `from_orm_model()`, `to_orm_kwargs()`
- **Command Schemas**: `to_domain()`, `from_domain()`
- **Query/Filter Schemas**: Typically only `to_domain()`

#### 2. Field Validation Assessment
```bash
# Check for validation patterns
grep -r "field_validator\|BeforeValidator\|AfterValidator" src/contexts/*/api_schemas/
```

**Validation Requirements by Field Type:**
- **Text fields**: Should use `BeforeValidator(validate_optional_text)` for trimming
- **ID fields**: Should use `field_validator` for format validation
- **Collection fields**: Should use TypeAdapters for nested validation
- **Computed fields**: Should use `@computed_field` or materialization patterns

#### 3. TypeAdapter Usage Assessment
```bash
# Check TypeAdapter implementations
find src/ -name "*.py" -exec grep -l "TypeAdapter" {} \;
```

**TypeAdapter Requirements:**
- **Naming**: Must end with "Adapter" (e.g., `RecipeListAdapter`)
- **Declaration**: Module-level singleton pattern preferred
- **Usage**: Integration with four-layer conversion methods

#### 4. Performance Baseline Assessment
```bash
# Run performance tests to establish baseline
poetry run python -m pytest tests/documentation/api_patterns/test_performance_baselines.py -v
```

**Performance Targets:**
- **TypeAdapter validation**: < 3ms for 10 items
- **Four-layer conversion**: < 50ms for complex objects
- **Field validation**: < 1ms for typical field sets

## 📋 Migration Phases

### Phase A: Foundation Setup

#### A.1 Test Infrastructure Setup
```bash
# Ensure test infrastructure is available
poetry run python -m pytest tests/documentation/api_patterns/conftest.py::test_fixtures_available -v
```

**Required Steps:**
1. **Create test file** for the schema being migrated
2. **Set up fixtures** using the established patterns in `conftest.py`
3. **Establish baseline tests** before making changes

#### A.2 Performance Baseline Establishment
```bash
# Establish current performance metrics
poetry run python scripts/analyze_api_patterns.py --schema YourSchemaName
```

**Baseline Metrics to Capture:**
- Current validation time
- Memory usage patterns
- Conversion cycle performance
- Any existing TypeAdapter performance

### Phase B: Schema Pattern Implementation

#### B.1 Four-Layer Conversion Implementation

**Step 1: Assess Current State**
```python
# Check existing methods in your schema
class YourSchema(BaseEntity[YourDomain, YourOrmModel]):
    # Assess which methods exist vs required methods
    pass
```

**Step 2: Implement Missing Methods**

For **Entity/Value Object schemas**, implement all four methods:

```python
@classmethod
def from_domain(cls, domain_obj: YourDomain) -> 'YourSchema':
    """Convert domain object to API schema."""
    return cls(
        id=domain_obj.id,
        # Handle computed properties materialization
        computed_field=domain_obj.computed_property,  # Materialize @cached_property
        # Handle collection conversions
        tags=frozenset(ApiTag.from_domain(tag) for tag in domain_obj.tags),
        # Use appropriate type conversions based on patterns/type-conversions.md
    )

def to_domain(self) -> YourDomain:
    """Convert API schema to domain object."""
    return YourDomain(
        id=self.id,
        # Convert collections back to domain types
        tags=set(tag.to_domain() for tag in self.tags),
        # Handle value objects and nested conversions
    )

@classmethod  
def from_orm_model(cls, orm_obj: YourOrmModel) -> 'YourSchema':
    """Convert ORM model to API schema."""
    return cls(
        id=orm_obj.id,
        # Handle ORM relationships and composite fields
        # Reference patterns/sqlalchemy-composite-integration.md
        composite_field=orm_obj.composite.to_dict() if orm_obj.composite else None,
        # Convert ORM lists to API frozensets
        tags=frozenset(ApiTag.from_orm_model(tag_orm) for tag_orm in orm_obj.tags),
    )

def to_orm_kwargs(self) -> dict[str, Any]:
    """Convert API schema to ORM model kwargs."""
    return {
        'id': self.id,
        # Handle composite field creation
        'composite': YourComposite(**self.composite_field) if self.composite_field else None,
        # Convert frozensets to lists for ORM
        'tags': [tag.to_orm_kwargs() for tag in self.tags],
    }
```

**Step 3: Validate Implementation**
```bash
# Test four-layer conversion cycle
poetry run python -m pytest tests/documentation/api_patterns/test_your_schema_conversion.py -v
```

#### B.2 Field Validation Implementation

**Step 1: Analyze Field Requirements**

Based on the analysis results, add validation for fields that currently lack patterns:

```python
from pydantic import field_validator, BeforeValidator
from typing_extensions import Annotated

class YourSchema(BaseEntity[YourDomain, YourOrmModel]):
    # Text fields - add trimming validation
    name: Annotated[str, BeforeValidator(validate_optional_text)]
    description: Annotated[str | None, BeforeValidator(validate_optional_text)] = None
    
    # ID fields - add format validation  
    user_id: str
    
    # Collection fields - use TypeAdapters
    tags: frozenset[ApiTag] = frozenset()
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user ID format."""
        # Reference patterns/field-validation.md for ID validation patterns
        if not v or len(v) < 1:
            raise ValueError("user_id cannot be empty")
        if len(v) > 36:
            raise ValueError("user_id too long (max 36 characters)")
        return v.strip()
    
    @field_validator('tags')
    @classmethod  
    def validate_tags(cls, v: frozenset[ApiTag]) -> frozenset[ApiTag]:
        """Validate tags collection."""
        # Use TypeAdapter for complex validation
        return TagFrozensetAdapter.validate_python(v)
```

**Step 2: Implement TypeAdapters for Collections**

If collections need complex validation, create module-level TypeAdapters:

```python
# At module level (recommended singleton pattern)
from pydantic import TypeAdapter

# Follow naming convention - must end with "Adapter"
YourCollectionAdapter = TypeAdapter(frozenset[YourNestedSchema])

class YourSchema(BaseEntity[...]):
    collection: frozenset[YourNestedSchema] = frozenset()
    
    @field_validator('collection')
    @classmethod
    def validate_collection(cls, v: frozenset[YourNestedSchema]) -> frozenset[YourNestedSchema]:
        """Validate collection using TypeAdapter."""
        return YourCollectionAdapter.validate_python(v)
```

**Step 3: Validate Field Patterns**
```bash
# Test field validation patterns
poetry run python -m pytest tests/documentation/api_patterns/test_your_field_validation.py -v
```

### Phase C: Performance Optimization

#### C.1 TypeAdapter Optimization

**Step 1: Audit Current TypeAdapter Usage**
```bash
# Check for TypeAdapter naming and usage patterns
grep -r "TypeAdapter" src/contexts/your_context/
```

**Step 2: Fix Naming Issues**
```python
# BEFORE (non-compliant naming)
recipe_list_type_adapter = TypeAdapter(list[ApiRecipe])

# AFTER (compliant naming - ends with "Adapter")
RecipeListAdapter = TypeAdapter(list[ApiRecipe])
```

**Step 3: Implement Singleton Pattern**
```python
# At module level for optimal performance
RecipeListAdapter = TypeAdapter(list[ApiRecipe])
TagFrozensetAdapter = TypeAdapter(frozenset[ApiTag])

# In conversion methods
def from_json_list(cls, json_data: list[dict]) -> list['ApiRecipe']:
    """Convert JSON list to API schema list using optimized TypeAdapter."""
    return RecipeListAdapter.validate_python(json_data)
```

**Step 4: Performance Validation**
```bash
# Validate TypeAdapter performance meets targets
poetry run python -m pytest tests/documentation/api_patterns/test_performance_regression.py::test_typeadapter_performance -v
```

#### C.2 Computed Properties Optimization

**Step 1: Identify Computed Properties**
```python
# Check domain objects for @cached_property
grep -r "@cached_property" src/contexts/your_context/domain/
```

**Step 2: Implement Materialization Pattern**
```python
class YourSchema(BaseEntity[YourDomain, YourOrmModel]):
    # Materialized computed property (no @property decorator in API)
    computed_value: float
    cached_computation: dict[str, Any] | None = None
    
    @classmethod
    def from_domain(cls, domain_obj: YourDomain) -> 'YourSchema':
        """Materialize computed properties during conversion."""
        return cls(
            computed_value=domain_obj.expensive_computation,  # Materialize @cached_property
            cached_computation=domain_obj.cached_data,        # Materialize cached results
            # ... other fields
        )
```

**Step 3: Validate Materialization Performance**
```bash
# Test computed property performance
poetry run python -m pytest tests/documentation/api_patterns/test_computed_property_materialization.py -v
```

### Phase D: Integration and Testing

#### D.1 Pattern Compliance Validation

**Step 1: Run Pattern Compliance Tests**
```bash
# Validate overall pattern compliance
poetry run python -m pytest tests/documentation/api_patterns/test_pattern_compliance_validator.py -v
```

**Step 2: Check Conversion Cycle Integrity**
```bash
# Test complete conversion cycles
poetry run python -m pytest tests/documentation/api_patterns/test_conversion_cycle_integrity.py -v
```

#### D.2 Performance Validation

**Step 1: Run Performance Regression Tests**
```bash
# Ensure no performance degradation
poetry run python -m pytest tests/documentation/api_patterns/test_performance_regression.py -v
```

**Step 2: Validate Against Baselines**
```bash
# Check performance against established baselines
poetry run python -m pytest tests/documentation/api_patterns/test_performance_baselines.py -v
```

## 🔧 Common Migration Scenarios

### Scenario 1: Schema with No Validation Patterns

**Problem**: Schema has fields but no validation patterns (45 schemas in analysis)

**Solution**:
```python
# BEFORE: No validation
class ApiUser(BaseEntity[User, UserSaModel]):
    user_id: str
    name: str
    email: str

# AFTER: Complete validation
class ApiUser(BaseEntity[User, UserSaModel]):
    user_id: str
    name: Annotated[str, BeforeValidator(validate_optional_text)]
    email: Annotated[str, BeforeValidator(validate_optional_text)]
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        if not v or len(v) < 1:
            raise ValueError("user_id cannot be empty")
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        # Add email format validation
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()
```

### Scenario 2: Missing Four-Layer Conversion Methods

**Problem**: Schema inherits from BaseEntity but missing conversion methods

**Solution**:
```python
# BEFORE: Incomplete implementation
class ApiMeal(BaseEntity[Meal, MealSaModel]):
    # Only has to_domain method
    pass

# AFTER: Complete four-layer implementation
class ApiMeal(BaseEntity[Meal, MealSaModel]):
    @classmethod
    def from_domain(cls, domain_obj: Meal) -> 'ApiMeal':
        # Implement complete domain conversion
        
    def to_domain(self) -> Meal:
        # Implement domain conversion
        
    @classmethod
    def from_orm_model(cls, orm_obj: MealSaModel) -> 'ApiMeal':
        # Implement ORM to API conversion
        
    def to_orm_kwargs(self) -> dict[str, Any]:
        # Implement API to ORM conversion
```

### Scenario 3: TypeAdapter Naming Issues

**Problem**: TypeAdapter doesn't follow naming convention

**Solution**:
```python
# BEFORE: Non-compliant naming
recipe_list = TypeAdapter(list[ApiRecipe])

# AFTER: Compliant naming
RecipeListAdapter = TypeAdapter(list[ApiRecipe])

# Update all references
def convert_recipes(data: list[dict]) -> list[ApiRecipe]:
    return RecipeListAdapter.validate_python(data)
```

## 🧪 Testing Migration Results

### Comprehensive Test Suite

After completing migration, run the full test suite:

```bash
# 1. Pattern compliance validation
poetry run python -m pytest tests/documentation/api_patterns/test_pattern_validation.py -v

# 2. Four-layer conversion testing
poetry run python -m pytest tests/documentation/api_patterns/test_meal_four_layer_conversion.py -v

# 3. Field validation testing
poetry run python -m pytest tests/documentation/api_patterns/test_field_validation_patterns.py -v

# 4. TypeAdapter performance testing
poetry run python -m pytest tests/documentation/api_patterns/test_performance_baselines.py -v

# 5. Computed property testing
poetry run python -m pytest tests/documentation/api_patterns/test_computed_property_materialization.py -v

# 6. AI agent scenario testing
poetry run python -m pytest tests/documentation/api_patterns/test_ai_agent_scenarios.py -v

# 7. Security validation
poetry run python -m pytest tests/documentation/api_patterns/test_security_validation.py -v

# 8. Performance regression testing
poetry run python -m pytest tests/documentation/api_patterns/test_performance_regression.py -v
```

### Migration Success Criteria

**✅ All tests must pass with these criteria:**
- **Pattern Compliance**: 100% compliance with documented patterns
- **Performance**: All TypeAdapters < 3ms for 10 items  
- **Conversion Integrity**: No data loss through conversion cycles
- **Field Validation**: All fields have appropriate validation
- **Security**: No validation bypasses or injection vulnerabilities

## 📊 Migration Impact Assessment

### Before/After Comparison

**Recommended approach for tracking migration impact:**

```python
# Create migration tracking test
def test_migration_impact():
    """Test migration impact on existing functionality."""
    
    # Test data integrity
    assert_conversion_cycle_integrity(your_schema_instance)
    
    # Test performance impact
    assert_performance_within_baseline(YourSchemaAdapter)
    
    # Test backward compatibility
    assert_api_compatibility(original_response, migrated_response)
```

### Risk Assessment

**Low Risk Migrations:**
- Adding field validation to command schemas
- Implementing missing `from_domain()` methods
- TypeAdapter naming fixes

**Medium Risk Migrations:**
- Adding four-layer conversion to existing entities
- Changing collection types (set ↔ frozenset ↔ list)
- Computed property materialization

**High Risk Migrations:**
- Modifying existing API response structures
- Changing validation logic that could break clients
- Performance-critical schema modifications

### Rollback Strategy

**For each migration, maintain:**
1. **Backup of original implementation**
2. **Performance baseline measurements**
3. **Test coverage before/after migration**
4. **API compatibility validation**

```bash
# Create rollback point
git branch backup/pre-migration-$(date +%Y%m%d)
git checkout -b feature/migrate-your-schema

# After migration, validate before merging
poetry run python -m pytest tests/documentation/api_patterns/ -v
```

## 📚 Reference Documentation

### Essential Reading Order
1. **Overview**: `docs/architecture/api-schema-patterns/overview.md`
2. **Type Conversions**: `docs/architecture/api-schema-patterns/patterns/type-conversions.md`
3. **Field Validation**: `docs/architecture/api-schema-patterns/patterns/field-validation.md`
4. **TypeAdapter Usage**: `docs/architecture/api-schema-patterns/patterns/typeadapter-usage.md`
5. **Computed Properties**: `docs/architecture/api-schema-patterns/patterns/computed-properties.md`
6. **Complete Example**: `docs/architecture/api-schema-patterns/examples/meal-schema-complete.md`

### Advanced Patterns
- **SQLAlchemy Integration**: `docs/architecture/api-schema-patterns/patterns/sqlalchemy-composite-integration.md`
- **Collection Handling**: `docs/architecture/api-schema-patterns/patterns/collection-handling.md`

## 🚨 Common Pitfalls and Solutions

### Pitfall 1: Breaking API Compatibility
**Problem**: Migration changes API response structure
**Solution**: Use `@computed_field` to maintain backward compatibility while adding new fields

### Pitfall 2: Performance Degradation
**Problem**: Adding validation slows down API responses
**Solution**: Use TypeAdapter singleton pattern and materialize computed properties

### Pitfall 3: Type Conversion Errors
**Problem**: Data loss during set ↔ frozenset ↔ list conversions
**Solution**: Follow established conversion matrix in type-conversions.md

### Pitfall 4: Validation Bypass
**Problem**: Complex objects not properly validated
**Solution**: Use TypeAdapters for nested object validation

### Pitfall 5: Thread Safety Issues
**Problem**: TypeAdapter performance issues under load
**Solution**: Use module-level singleton TypeAdapters, not instance-level

## 🎯 Next Steps After Migration

### 1. Documentation Updates
- Update schema documentation to reflect new patterns
- Add migration notes for future reference
- Update API documentation if needed

### 2. Performance Monitoring
- Set up monitoring for TypeAdapter performance
- Track conversion cycle performance
- Monitor memory usage patterns

### 3. Team Training
- Share migration learnings with team
- Update development guidelines
- Create schema implementation checklist

### 4. Continuous Improvement
- Regular pattern compliance audits
- Performance regression monitoring
- Pattern documentation updates based on lessons learned

---

## 📞 Support and Troubleshooting

### Getting Help
- **Pattern Questions**: Reference the comprehensive pattern documentation
- **Performance Issues**: Run performance baseline tests for comparison
- **Validation Errors**: Check field validation patterns documentation
- **Type Conversion**: Reference type conversion matrix

### Debug Commands
```bash
# Analyze specific schema patterns
poetry run python scripts/analyze_api_patterns.py --schema YourSchemaName

# Performance profiling
poetry run python -m pytest tests/documentation/api_patterns/test_performance_baselines.py::test_your_schema -v -s

# Pattern compliance check
poetry run python -m pytest tests/documentation/api_patterns/test_pattern_compliance_validator.py::test_your_schema -v
```

### Success Validation
After migration, your schema should:
- ✅ Pass all pattern compliance tests
- ✅ Meet performance baselines  
- ✅ Maintain API compatibility
- ✅ Have complete validation coverage
- ✅ Follow documented best practices

**Migration complete when all tests pass and performance targets are met.** 