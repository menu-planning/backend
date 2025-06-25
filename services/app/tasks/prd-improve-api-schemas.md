# PRD: Improve API Schemas

## Executive Summary

### Problem Statement
Current Pydantic API schema classes (e.g., `ApiMeal`, `ApiRecipe`, etc.) suffer from:
1. Inconsistent validation patterns and missing strict checks across nested entities.
2. Generic error handling (`ValueError`, bare `Exception`) that hinders debugging.
3. Uneven logging, making it difficult to trace serialization/conversion issues.
4. Maintenance friction when adding new fields or nested models.
5. Limited automated tests validating conversions between Domain ↔ API ↔ ORM representations.

### Proposed Solution
Introduce a unified, extensible framework for API schemas that provides:
1. Strict, nested validation using Annotated fields & custom validators.
2. Centralised exception hierarchy (`ApiSchemaError`, `ValidationConversionError`, etc.).
3. Structured logging around construction & conversion operations.
4. TypeAdapter utilities for complex nested collections with automatic JSON-ready serialisation (e.g., sets → lists).
5. Pytest-based test suite for bidirectional conversions and schema mismatch detection.
6. Refactored exemplar (`ApiMeal`) showcasing the new pattern and serving as a template for all other schemas.

### Business Value
• Faster onboarding & development for a solo developer by reducing boilerplate and debugging time.
• Higher API reliability – fewer runtime errors reach production.
• Future-proof design simplifies adding menus/meals/recipes features.

### Success Criteria
- [ ] 100 % strict validation coverage for all API schemas (including nested entities).
- [ ] Conversion operations raise specific, logged exceptions with contextual details.
- [ ] End-to-end JSON serialisation returns only standard JSON types (no sets, frozensets, etc.).
- [ ] Pytest suite (>90 % branch coverage on API layer) passes for Domain ↔ API ↔ ORM round-trips.
- [ ] No regression in existing functionality/performance.

## Goals and Non-Goals

### Goals
1. Provide a robust base for strict validation & logging.
2. Refactor `ApiMeal` to demonstrate the pattern.
3. Deliver utilities & guidelines for refactoring remaining schemas.
4. Build automated conversion test harness.

### Non-Goals
1. Changing domain or ORM business logic.
2. Performance micro-optimisations (unless validation proves to be a bottleneck).
3. Implementing new API endpoints.

## User Stories and Acceptance Criteria

### User Story 1: As a developer, I want API schemas to validate all nested data strictly so that invalid requests are rejected early.
**Acceptance Criteria**
- [ ] Attempting to instantiate `ApiMeal` with duplicate recipe IDs raises `DuplicateItemError` with a descriptive message.
- [ ] Missing required fields cause `ValidationError` showing the exact field path.

### User Story 2: As a developer, I need clear logs when conversions fail so I can debug quickly.
**Acceptance Criteria**
- [ ] Every exception raised during `to_domain`, `from_domain`, `to_orm_kwargs`, and `from_orm_model` includes a structured log entry with context (schema, operation, payload sample).

### User Story 3: As a developer, I want automated tests verifying that API, Domain, and ORM schemas remain in sync.
**Acceptance Criteria**
- [ ] Pytest suite asserts that every field in Domain ↔ API ↔ ORM mappings exists and has compatible types (collections, scalar, computed vs stored).
- [ ] Round-trip conversion (`domain → api → orm_kwargs → api → domain`) yields an object equal in value to the original.

## Technical Specifications

### System Architecture
```
sequenceDiagram
    participant Client
    participant API Schema (Pydantic)
    participant Domain Entity
    participant ORM Model (SQLAlchemy)
    Client->>API Schema: JSON payload
    API Schema->>Domain Entity: to_domain()
    Domain Entity-->>API Schema: validation errors (if any)
    Domain Entity->>ORM Model: persistence layer
    ORM Model-->>Domain Entity: data fetch
    ORM Model->>API Schema: from_orm_model()
    API Schema->>Client: JSON response
```

### Base Classes
1. **`BaseApiModel`** (existing): remains the root, add hooks:
```python
class BaseApiModel(BaseModel):
    class Config:  # rename to model_config for Pydantic v2
        strict = True

    @model_validator(mode="after")
    def _post_validate(self):
        logger.debug("Validated %s", self.__class__.__name__)
        return self
```
2. **Exception hierarchy** in `src/contexts/seedwork/shared/adapters/exceptions/api_schema.py`:
```python
from pydantic.errors import PydanticCustomError

class ApiSchemaError(Exception): ...
class ValidationConversionError(ApiSchemaError): ...

# For use *inside* Pydantic validators so they integrate with ValidationError
class DuplicateItemError(PydanticCustomError):
    """Raised when a collection contains duplicate items (e.g., duplicate recipe IDs)."""
    code = 'duplicate_item'
    msg_template = 'Duplicate {item_name} detected: {item_value}'
```

Validators will raise `DuplicateItemError` (or built-in `ValueError` / `TypeError`) which Pydantic automatically wraps into a `ValidationError`, keeping us fully compliant with the [Pydantic v2 guidelines on raising validation errors](https://docs.pydantic.dev/latest/concepts/validators/#raising-validation-errors).

Conversion methods (`to_domain`, `from_domain`, etc.) will raise `ValidationConversionError` (outside Pydantic's validation cycle) and log the structured context.

### Data Model
Refactor collections:
- Always expose JSON-serialisable lists in outward facing payloads.
- Internally allow sets/frozensets but convert via TypeAdapters.

Example `RecipeListAdapter` remains but enforces uniqueness on `id`.

### API Specifications
_No external REST spec changes; internal behaviour only._

## Functional Requirements

FR1: Strict nested validation for `ApiMeal` (recipes, tags) using validators & TypeAdapters. Priority P0.
FR2: Structured logging & custom exceptions across all conversion methods. P0.
FR3: Generic schema mismatch detector utility for tests (`assert_schema_sync(domain_cls, api_cls, orm_cls)`). P1.
FR4: Provide reusable `UniqueCollectionAdapter` for lists/sets uniqueness validation. P1.
FR5: Update JSON encoders to convert sets/frozensets to lists. P2.

## Non-Functional Requirements

### Performance
• Validation of a single `ApiMeal` with 10 recipes < 5 ms (median) on M1 laptop.

### Scalability
• Framework must support >100 API schemas without repetitive boilerplate.

### Security
• No sensitive data leakage in logs (truncate long values, hash IDs if needed).

### Reliability
• 99 % success rate of domain-api-orm round-trip tests in CI.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
| ---- | ----------- | ------ | ---------- |
| Incomplete field mapping unnoticed | Medium | High | Automated schema comparison tests in CI |
| Performance overhead from deep validation | Low | Medium | Benchmark & profile; allow caching adapters if needed |
| Logging sensitive data | Low | High | Redact IDs/tokens via formatter |

## Testing Strategy

### Coverage Requirements
- Unit tests: ≥ 90 % on `src/contexts/.../adapters`.
- Property-based tests for collection uniqueness & percentage ranges.
- Integration tests for Domain ↔ API ↔ ORM conversions.

### Test Scenarios
• **Unit**: validators raise on invalid inputs, TypeAdapters convert sets.
• **Integration**: round-trip conversions, schema sync detector.
• **Performance**: benchmark validation time with `pytest-benchmark`.

## Implementation Plan

### Phase 0: Prerequisites
- [ ] Draft exception hierarchy & logging formatter.
- [ ] Agree on logging schema (JSON vs plain text).

### Phase 1: Foundation
- [ ] Enhance `BaseApiModel` with post-validation logging hooks.
- [ ] Implement exception classes.
- [ ] Add generic `UniqueCollectionAdapter`.

### Phase 2: Refactor ApiMeal
- [ ] Apply new base & adapters.
- [ ] Replace generic `ValueError` with custom errors.
- [ ] Update unit tests for `ApiMeal`.

### Phase 3: Extend to Remaining Schemas
- [ ] Create checklist & script to migrate each API schema.
- [ ] Incrementally refactor (`ApiRecipe`, etc.).

### Phase 4: Test Automation
- [ ] Implement `assert_schema_sync` utility.
- [ ] Write pytest parametrised suite covering all schemas.

### Phase 5: Polish & Deploy
- [ ] Update docs & README.
- [ ] Final CI run including benchmarks.

### Rollout Strategy
- Feature flag not required (internal change).
- Refactor in a dedicated branch; merge after test green.
- Revert path: re-register previous `BaseApiModel` if critical issue discovered.

## Monitoring and Observability
- Add log entries for schema creation/conversion failures.
- Expose metric `api_schema.validation_failures` via Prometheus exporter.

## Documentation Requirements
- API schema developer guide in `/docs`.
- ADR documenting decision to use strict Pydantic & custom adapters.

## Dependencies and Prerequisites
- Python 3.12, Pydantic ≥ 2.6.
- `pytest`, `pytest-benchmark`, `hypothesis` for tests.

## Timeline and Milestones
| Milestone | Target Date |
| --------- | ----------- |
| Foundation complete | +3 d |
| ApiMeal refactored | +6 d |
| All schemas migrated | +14 d |
| Test automation done | +18 d |
| Production ready | +21 d |

## Open Questions and Decisions
1. Should logging be JSON-formatted by default?  (Pending)
2. Do we add SQLAlchemy validators for ORM models to catch mismatch earlier?  (Pending)

## Required Approvals
- [ ] Technical Architecture (self-review)
- [ ] Product (self-review)
- [ ] Security review (N/A) 