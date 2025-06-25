# Task List: Improve API Schemas

## Implementation Strategy

Based on comprehensive analysis of 100+ API schema files across all contexts, this task list follows a dependency-aware approach:
- Foundation components first (exceptions, base classes, utilities)
- Leaf nodes before dependent schemas (value objects → entities → aggregates)
- Parallel test development for immediate validation
- Exemplar-driven pattern (ApiMeal) to guide all refactoring

## Relevant Files

### Foundation Components
- `src/contexts/seedwork/shared/adapters/api_schemas/base.py` - Base classes to enhance (MODIFY)
- `src/contexts/seedwork/shared/adapters/exceptions/api_schema.py` - Exception hierarchy (NEW)
- `src/contexts/seedwork/shared/adapters/api_schemas/type_adapters.py` - Type adapter utilities (MODIFY)
- `src/contexts/seedwork/shared/adapters/api_schemas/validators.py` - Common validators (NEW)

### Exemplar Schema
- `src/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/api_meal.py` - Primary refactoring target (MODIFY)
- `src/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/api_recipe.py` - Dependent entity (MODIFY)
- `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal.py` - Comprehensive tests (NEW)

### Test Infrastructure
- `tests/contexts/seedwork/shared/adapters/api_schemas/test_schema_sync.py` - Schema sync validator (NEW)
- `tests/contexts/seedwork/shared/adapters/api_schemas/test_type_adapters.py` - Adapter tests (NEW)
- `tests/contexts/seedwork/shared/adapters/api_schemas/conftest.py` - Test fixtures (NEW)

## Testing Strategy
- Unit Tests: Field validators, type adapters, exception handling
- Integration Tests: Domain ↔ API ↔ ORM conversions
- Property Tests: Collection uniqueness, percentage validation
- Performance Tests: Validation benchmarks with pytest-benchmark

---

# 📊 Tasks

## Phase 0: Foundation Setup

### 0.1 Create Exception Hierarchy
- [x] 0.1.1 Create `src/contexts/seedwork/shared/adapters/exceptions/api_schema.py` with base exceptions
  - Define `ApiSchemaError` base class
  - Create `ValidationConversionError` for conversion failures
  - Implement `DuplicateItemError` as PydanticCustomError
  - Add `FieldMappingError` for schema mismatches
- [x] 0.1.2 Write unit tests for exception hierarchy in `tests/contexts/seedwork/shared/adapters/exceptions/test_api_schema.py`
  - Test exception inheritance chain
  - Verify error message formatting
  - Validate PydanticCustomError integration
- [x] 0.1.3 Document exception usage patterns in module docstring

### 0.2 Enhance BaseApiModel
- [x] 0.2.1 Add post-validation logging hook to BaseApiModel
  - Implement `@model_validator(mode="after")` for debug logging
  - Add class name and validation context to logs
  - Ensure no sensitive data in logs
- [x] 0.2.2 Create protected conversion wrapper methods
  - `_safe_to_domain()` with error handling and logging
  - `_safe_from_domain()` with structured error context
  - `_safe_to_orm_kwargs()` with field mapping validation
  - `_safe_from_orm_model()` with null handling
- [x] 0.2.3 Update model_config for Pydantic v2 compatibility
  - Rename `Config` class to `model_config`
  - Ensure `strict=True` for all schemas
  - Add `json_encoders` for set/frozenset handling

### 0.3 Build Core Utilities
- [x] 0.3.1 Create `UniqueCollectionAdapter` in type_adapters.py
  - Generic adapter for list validation with uniqueness
  - Support for custom uniqueness keys (id, name, etc.)
  - Proper error messages with duplicate details
  - Support for arbitrary types with ConfigDict
- [x] 0.3.2 Implement common validators in new validators.py
  - `validate_percentage_sum` for percentage fields
  - `validate_no_duplicates` for collections
  - `validate_non_empty_string` with trimming
- [x] 0.3.3 Add TypeAdapter for JSON-safe collections
  - Auto-convert sets to lists for JSON serialization
  - Preserve ordering for consistent output
  - Handle nested collections recursively

## Phase 1: Schema Analysis & Test Infrastructure

### 1.1 Build Schema Synchronization Validator
- [x] 1.1.1 Create `assert_schema_sync` utility function
  - Compare field names between Domain, API, and ORM classes
  - Validate type compatibility (considering collections)
  - Check for computed vs stored field alignment
- [x] 1.1.2 Write parametrized test discovering all schema triplets
  - Auto-discover schema files using glob patterns
  - Map corresponding Domain/API/ORM classes
  - Report mismatches with clear field-level details
- [x] 1.1.3 Create fixtures for common test scenarios
  - Valid/invalid collection data
  - Edge cases for percentage validation
  - Nested object hierarchies

### 1.2 Performance Benchmarking Setup
- [x] 1.2.1 Install and configure pytest-benchmark
- [x] 1.2.2 Create baseline benchmarks for current ApiMeal validation
  - ⚠️ Simple meal validation: actually tests < 2ms (claimed < 1ms)
  - ⚠️ Complex meal validation: actually tests < 4ms (claimed < 2ms)  
  - ✅ Performance test infrastructure with deterministic data factories
  - ✅ Basic validation logging operational
  - ⚠️ Model roundtrip tests identified serialization issues for future fix
- [x] 1.2.3 Set performance targets based on baseline measurements
  - **Validation Targets:**
    - Simple meal (no recipes): < 2ms (actually tested)
    - Standard meal (3-5 recipes): < 5ms (tested for ≤5 recipes)  
    - Large meal (10 recipes): < 8ms (production target)
    - Complex meal (all fields): < 4ms (actually tested)
  - **Conversion Targets:**
    - Domain ↔ API conversions: < 10ms for 5-recipe meal
    - ORM ↔ API conversions: < 15ms for 5-recipe meal
    - Full roundtrip: < 20ms for 5-recipe meal
  - **Field Validation Targets:**
    - Recipe list validation: < 8ms for 10 recipes from JSON
    - Tag validation: < 4ms for 5 tags from JSON
    - Nutrition facts validation: < 3ms (currently skipped due to domain cache issues)
  - **Stress Test Targets:**
    - Large meal (20 recipes): < 25ms incoming, < 30ms outgoing
    - Repeated validation (25x): < 100ms total with < 100MB memory
    - Memory efficiency: Validated through psutil monitoring

### 1.3 Implement Rigorous Performance Targets (NEW)
- [x] 1.3.1 Update performance tests with ambitious targets  
  - **Rigorous Validation Targets:**
    - Simple meal (no recipes): < 1ms (down from 2ms)
    - Standard meal (3-5 recipes): < 3ms (new dedicated test)
    - Large meal (10 recipes): < 5ms (down from 8ms) 
    - Complex meal (all fields): < 4ms (keep current)
  - **Optimized Field Validation:**
    - Recipe list validation: < 3ms for 10 recipes (down from 8ms)
    - Tag validation: < 2ms for 5 tags (down from 4ms)
    - Nutrition facts validation: < 2ms (down from 3ms)
  - **Efficient Stress Tests:**
    - Large meal (20 recipes): < 15ms incoming, < 18ms outgoing
    - Repeated validation (50x): < 100ms total (up from 25x)
- [x] 1.3.2 Add dedicated "standard meal" performance test
  - Test specifically for 3-recipe meals at < 3ms
  - Test specifically for 5-recipe meals at < 3ms  
  - Verify scaling behavior between these points
- [x] 1.3.3 Create optimization roadmap when tests fail
  - Profile current bottlenecks using cProfile
  - Identify Pydantic optimization opportunities
  - Plan lazy loading and caching strategies

## Phase 2: Refactor ApiMeal (Exemplar)

### 2.1 Analyze Current ApiMeal Implementation
- [ ] 2.1.1 Document all current validation gaps
  - Missing recipe ID uniqueness check
  - No tag validation
  - Weak error messages
- [ ] 2.1.2 Map all dependencies (ApiRecipe, ApiTag, etc.)
- [ ] 2.1.3 Create refactoring checklist specific to ApiMeal

### 2.2 Implement Strict Validation
- [ ] 2.2.1 Replace recipe list with UniqueCollectionAdapter
  - Validate uniqueness by recipe ID
  - Provide clear duplicate error messages
- [ ] 2.2.2 Add tag validation using TagSetAdapter
  - Ensure valid tag format
  - Check for duplicate tags
- [ ] 2.2.3 Implement cross-field validation
  - Validate at least one recipe exists
  - Check recipe percentage sum if applicable

### 2.3 Upgrade Conversion Methods
- [ ] 2.3.1 Refactor to_domain() with comprehensive error handling
  - Use _safe_to_domain wrapper
  - Log conversion context on failure
  - Handle nested recipe conversions
- [ ] 2.3.2 Enhance from_domain() with defensive programming
  - Validate domain object state
  - Handle optional fields gracefully
  - Convert sets to lists for JSON
- [ ] 2.3.3 Improve to_orm_kwargs() with field mapping validation
  - Verify all required ORM fields present
  - Transform nested objects appropriately
  - Add conversion audit trail
- [ ] 2.3.4 Strengthen from_orm_model() with null safety
  - Handle missing relationships
  - Provide defaults for optional fields
  - Log any data transformations

### 2.4 Comprehensive Testing for ApiMeal
- [ ] 2.4.1 Write unit tests for all validators
  - Test duplicate recipe detection
  - Verify tag validation
  - Check edge cases
- [ ] 2.4.2 Create integration tests for conversions
  - Domain → API → ORM → API → Domain roundtrip
  - Test with minimal and maximal data
  - Verify error handling paths
- [ ] 2.4.3 Add property-based tests using Hypothesis
  - Generate random valid/invalid meals
  - Test collection uniqueness properties
  - Verify percentage constraints
- [ ] 2.4.4 Performance test validation and conversions
  - Benchmark against baseline
  - Test with varying recipe counts
  - Identify any bottlenecks

## Phase 3: Refactor Dependent Schemas

### 3.1 Update ApiRecipe (Direct Dependency)
- [ ] 3.1.1 Apply validation patterns from ApiMeal
  - Unique ingredients by name
  - Validate cooking times
  - Check rating constraints
- [ ] 3.1.2 Enhance conversion methods with logging
- [ ] 3.1.3 Write comprehensive tests
- [ ] 3.1.4 Verify compatibility with refactored ApiMeal

### 3.2 Refactor Value Objects (Bottom-Up)
- [ ] 3.2.1 Update shared value objects first
  - ApiTag with format validation
  - ApiNutriFacts with percentage validation
  - ApiUser/ApiRole with permission checks
- [ ] 3.2.2 Refactor context-specific value objects
  - ApiIngredient with quantity validation
  - ApiRating with range checks
  - ApiMenuMeal with reference validation
- [ ] 3.2.3 Ensure JSON serialization compatibility

### 3.3 Update Entity Schemas
- [ ] 3.3.1 Refactor classification entities (products context)
  - ApiCategory with hierarchy validation
  - ApiBrand with uniqueness checks
  - ApiClassification base improvements
- [ ] 3.3.2 Update menu entities (recipes context)
  - ApiMenu with meal reference validation
  - Cross-reference validation with meals
- [ ] 3.3.3 Test entity-aggregate relationships

### 3.4 Refactor Remaining Root Aggregates
- [ ] 3.4.1 Update ApiProduct with classification validation
- [ ] 3.4.2 Enhance ApiClient with menu relationship checks
- [ ] 3.4.3 Improve ApiUser with role validation
- [ ] 3.4.4 Ensure consistent patterns across aggregates

## Phase 4: Command Schema Updates

### 4.1 Enhance Command Validation
- [ ] 4.1.1 Add pre-execution validation to all commands
- [ ] 4.1.2 Implement command-specific business rule checks
- [ ] 4.1.3 Improve error messages for command failures
- [ ] 4.1.4 Add audit logging for command execution

### 4.2 Test Command Schemas
- [ ] 4.2.1 Unit test all command validators
- [ ] 4.2.2 Integration test command-to-domain flows
- [ ] 4.2.3 Test authorization checks where applicable

## Phase 5: System Integration & Migration

### 5.1 Full System Testing
- [ ] 5.1.1 Run all existing tests to ensure no regression
- [ ] 5.1.2 Execute end-to-end API tests with new schemas
- [ ] 5.1.3 Validate JSON serialization in API responses
- [ ] 5.1.4 Test error response formatting

### 5.2 Performance Validation
- [ ] 5.2.1 Run full benchmark suite
- [ ] 5.2.2 Compare against baseline metrics
- [ ] 5.2.3 Optimize any bottlenecks found
- [ ] 5.2.4 Document performance characteristics

### 5.3 Migration Tooling
- [ ] 5.3.1 Create script to identify non-compliant schemas
- [ ] 5.3.2 Build migration checklist template
- [ ] 5.3.3 Document common refactoring patterns
- [ ] 5.3.4 Create code snippets for repetitive changes

## Phase 6: Documentation & Knowledge Transfer

### 6.1 Create Developer Guide
- [ ] 6.1.1 Write API schema best practices guide
- [ ] 6.1.2 Document validation patterns with examples
- [ ] 6.1.3 Create troubleshooting guide for common errors
- [ ] 6.1.4 Add architecture decision record (ADR)

### 6.2 Update Code Documentation
- [ ] 6.2.1 Add comprehensive docstrings to base classes
- [ ] 6.2.2 Document all custom validators
- [ ] 6.2.3 Include usage examples in type adapters
- [ ] 6.2.4 Update README with new patterns

## Phase 7: Monitoring & Observability

### 7.1 Implement Metrics Collection
- [ ] 7.1.1 Add Prometheus metrics for validation failures
- [ ] 7.1.2 Track conversion operation latencies
- [ ] 7.1.3 Monitor schema mismatch occurrences
- [ ] 7.1.4 Create Grafana dashboard for API health

### 7.2 Enhanced Logging
- [ ] 7.2.1 Implement structured logging for all schemas
- [ ] 7.2.2 Add correlation IDs to trace requests
- [ ] 7.2.3 Configure log levels appropriately
- [ ] 7.2.4 Set up log aggregation queries

## 🎯 Success Criteria

1. ✓ All API schemas have strict validation with clear error messages
2. ✓ 100% of conversions log structured context on failure
3. ✓ JSON serialization returns only standard types (no sets/frozensets)
4. ✓ Test coverage > 90% on all API schema modules
5. ✓ ApiMeal validation < 5ms for 10-recipe meals
6. ✓ Zero regressions in existing functionality
7. ✓ Schema sync tests pass for all Domain ↔ API ↔ ORM mappings
8. ✓ Developer guide completed and reviewed

## 📝 Notes

- Each phase builds on the previous - don't skip ahead
- Run tests after each subtask to catch issues early
- Update this list with newly discovered tasks marked with **NEW**
- Use ApiMeal as the reference implementation for all other schemas
- Consider requesting code examples after completing Phase 2