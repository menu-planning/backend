# Phase 2: Advanced Patterns

---
phase: 2
depends_on: [phase_1]
estimated_time: 8-10 hours
risk_level: medium
---

## Objective
Document advanced API layer patterns including type conversion utilities, field annotations, and complex validation scenarios.

## Prerequisites
- [ ] Phase 1 completed: Basic API documentation in place
- [ ] Review existing TypeConversionUtility implementation
- [ ] Understand base_api_fields.py patterns
- [ ] Access to meal_domain_factories.py and meal_orm_factories.py

# Tasks

## 2.1 Type Conversion Utilities
- [ ] 2.1.1 Document TypeConversionUtility patterns
  - Files: `docs/api-layer/implementation-guide.md` (conversion utilities section)
  - Purpose: Document domain ↔ API type conversions
  - Include all major conversion patterns used in project
- [ ] 2.1.2 Create conversion examples
  - Files: `docs/api-layer/examples/conversion-examples.py`
  - Domain UUID ↔ API string conversions
  - Set ↔ FrozenSet ↔ List transformations
  - DateTime ↔ ISO string handling
  - Complex nested object conversions
- [ ] 2.1.3 Document edge cases and error handling
  - Invalid UUID string handling
  - Timezone considerations for DateTime conversions
  - Empty collection handling

## 2.2 Field Annotations and Validation
- [ ] 2.2.1 Document typing.Annotated patterns
  - Files: `docs/api-layer/implementation-guide.md` (field annotations section)
  - Purpose: Show base_api_fields.py usage patterns
  - Include forward annotations with quotes
  - Document `from __future__ import annotations` usage
- [ ] 2.2.2 Create field validation examples
  - Files: `docs/api-layer/examples/field-validation-examples.py`
  - `AfterValidator` and `BeforeValidator` patterns
  - Custom field validation functions
  - Cross-field validation examples
- [ ] 2.2.3 Document common validation patterns
  - Email validation with custom error messages
  - UUID string validation
  - Date range validation
  - Complex business rule validation

## 2.3 Filter Classes and Query Patterns
- [ ] 2.3.1 Document filter class implementation
  - Files: `docs/api-layer/implementation-guide.md` (filter classes section)
  - Purpose: Show query parameter validation using `model_validate_python()`
  - Include repository integration patterns
- [ ] 2.3.2 Create filter examples
  - Files: `docs/api-layer/examples/filter-examples.py`
  - Basic filter with sorting and pagination
  - Complex filtering with multiple criteria
  - Search filter with text matching
- [ ] 2.3.3 Document repository integration
  - How filters integrate with repository query methods
  - Performance considerations for complex filters
  - SQL injection prevention patterns

## 2.4 Error Handling and Edge Cases
- [ ] 2.4.1 Document error handling patterns
  - Files: `docs/api-layer/implementation-guide.md` (error handling section)
  - Pydantic validation error handling
  - Custom error messages and formatting
  - Lambda error response patterns
- [ ] 2.4.2 Create error handling examples
  - Files: `docs/api-layer/examples/error-handling-examples.py`
  - ValidationError handling and formatting
  - Type conversion error handling
  - Business logic error propagation
- [ ] 2.4.3 Document common pitfalls
  - Frozen model mutation attempts
  - Type conversion failures
  - Circular reference issues in complex models

## Validation
- [ ] Tests: `poetry run python -m pytest docs/api-layer/examples/ -v`
- [ ] Type checks: `poetry run python mypy docs/api-layer/examples/`
- [ ] Integration tests: Verify conversion utilities work with real data
- [ ] Code quality: `poetry run python ruff check docs/api-layer/examples/`

## Next Steps
Ready for Phase 3: Testing Documentation (TDD approaches, data factories, parametrized testing) 