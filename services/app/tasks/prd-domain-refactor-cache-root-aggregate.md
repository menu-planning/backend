# PRD: Domain Refactor – Instance-Level Caching & Root-Aggregate Hardening

## Executive Summary

### Problem Statement
Current domain entities rely on `functools.lru_cache` to cache computed properties such as `nutri_facts`.  
`lru_cache` is *function-level* & **shared across instances**, leading to cross-instance state leakage, unpredictable invalidation, and hidden memory retention.  
In addition, some behaviours in `Meal` and `_Recipe` blur aggregate boundaries (e.g.
updating a `Recipe` directly rather than through its parent `Meal`).  
Finally, the `update_properties` helper is inconsistently implemented across entities, risking silent rule violations and stale domain events.

### Proposed Solution
1. Replace all `@lru_cache` decorators on domain entities with **instance-level caching** via `functools.cached_property` (Py≥3.8) or explicit `self._cache` attrs with proper invalidation hooks.  
2. Enforce that **`Meal` is the sole root aggregate** for `Recipe` by restricting direct mutation of `Recipe` and exposing safe façade methods on `Meal`.  
3. Standardise `update_properties` to validate invariants, fire events, bump versions, and reset caches.  
4. Add a comprehensive test suite (≥90 % coverage) under `tests/` mirroring the `src/` hierarchy to guard behaviour before and after refactor.

### Business Value
• Faster, deterministic behaviour (no cross-instance cache bleed).  
• Safer domain model that prevents illegal state transitions.  
• Higher developer confidence through extensive automated tests.  
• Reduced production defects and easier debugging thanks to clear aggregate boundaries & logging.

### Success Criteria
• All computed-property caches are instance-specific and invalidate on state change.  
• Direct calls that mutate `Recipe` without `Meal` fail at type or runtime.  
• `update_properties` behaves consistently (passes spec tests).  
• Pytest coverage ≥ 90 % across all `*/domain/*` modules.  
• No regression in existing features (all green CI pipeline).

---

## Goals and Non-Goals

### Goals
1. Introduce instance-level caching for computed properties (`nutri_facts`, `macro_division`, rating averages, etc.).
2. Refactor `Meal` and `_Recipe` so that `Meal` orchestrates all child modifications.
3. Unify `update_properties` contract and ensure rule checks + event emission.
4. Deliver exhaustive, structured Pytest suite with coverage reports.
5. Maintain existing public APIs & persistence schema.

### Non-Goals
1. Re-designing nutritional algorithms.  
2. Migrating database schemas or data models.  
3. Changing external API contracts (GraphQL/REST).  
4. Optimising performance beyond cache correctness.

---

## User Stories and Acceptance Criteria

### User Story 1: Correct Caching
**As a** backend developer  
**I want** computed properties to be cached per entity instance  
**So that** one entity's changes don't pollute another's results.

**Acceptance Criteria**
- [ ] Calling `meal.nutri_facts` twice on the same instance performs heavy calculations only once.
- [ ] Mutating `meal.recipes` invalidates the cache automatically.
- [ ] Two different `Meal` objects never share cached results (verified via unit test).

### User Story 2: Aggregate Integrity
**As a** domain engineer  
**I want** all `Recipe` mutations to go through `Meal`  
**So that** aggregate invariants (author, meal_id, positions, etc.) are preserved.

**Acceptance Criteria**
- [ ] Direct property setters on `_Recipe` raise a `DomainError` when invoked outside `Meal` context.
- [ ] `Meal.create_recipe`, `Meal.update_recipes`, `Meal.delete_recipe`, `Meal.copy_recipe`, etc., are the supported mutation pathways.

### User Story 3: Consistent `update_properties`
**As a** maintainer  
**I want** a single, documented pattern for `update_properties`  
**So that** future entities stay uniform and predictable.

**Acceptance Criteria**
- [ ] Method validates entity is not discarded.
- [ ] Performs rule checks before state mutation.
- [ ] Emits domain events when changes affect external aggregates.
- [ ] Increments version exactly once per call.
- [ ] Clears related caches.

### User Story 4: High Test Coverage
**As a** QA engineer  
**I want** ≥90 % statement coverage for all domain modules  
**So that** refactors are protected by fast feedback loops.

**Acceptance Criteria**
- [ ] Running `pytest --cov=src/contexts --cov-report=term-missing` shows ≥ 90 % for `*/domain/*` paths.
- [ ] Tests reside in `tests/contexts/<context>/core/domain/...` mirroring `src` structure.

---

## Technical Specifications

### System Architecture
```mermaid
graph TD
    Meal((Meal – Aggregate Root)) --> Recipe1[_Recipe]
    Meal --> Recipe2[_Recipe]
    Meal -- updates --> |invalidates cache| Cache[(Instance Cache)]
```

### Instance-Level Cache Design
| Aspect | Decision |
| --- | --- |
| Mechanism | `functools.cached_property` for Python ≥ 3.8  *(falls back to custom descriptor if needed)* |
| Invalidated by | Any state-changing setter or method that affects inputs (e.g.
`recipes`, `ratings`, `weight_in_grams`) |
| Invalidation API | Central `self._invalidate_caches(*attr_names)` helper in `Entity` base class |
| Thread safety | Not a concern in typical sync web-request lifecycle; document caveats for async tasks |

Example implementation snippet:
```python
from functools import cached_property

class Entity:
    _cached_attrs: set[str] = set()

    def _invalidate_caches(self, *attrs: str) -> None:
        for attr in attrs or self._cached_attrs:
            self.__dict__.pop(attr, None)

class Meal(Entity):
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        ... # heavy calculation
    
    def recipes(self, value: list[_Recipe]):
        self._recipes = value
        self._invalidate_caches('nutri_facts', 'macro_division')
```

### Root-Aggregate Enforcement
1. Mark `_Recipe` setters **protected** (prefix `_set_*`) where direct access is required internally.  
2. Provide public mutation APIs only on `Meal`.  
3. Add runtime guard in `_Recipe._check_mutation_allowed(self)` that asserts `inspect.stack()` caller is inside `Meal` (or use context manager).

### Standardised `update_properties`
Pseudo-code contract:
```python
def update_properties(self, **kwargs):
    self._check_not_discarded()
    initial_state = {k: getattr(self, k) for k in kwargs}
    # 1) Domain rule validation first
    self._validate_update(**kwargs)
    # 2) Apply updates
    super()._update_properties(**kwargs)
    # 3) Aggregate-level side-effects (events, cache invalidation)
    self._post_update(initial_state)
    # 4) Version bump (exactly once)
    self._increment_version()
```
A mixin `UpdatePropertiesMixin` will encapsulate common logic.

### Data Model
(No DB schema changes.)

### Logging & Error Handling
- Use `src.logging.logger` for debug-level cache invalidation messages.
- Raise `DomainValidationError` (custom) for invariant violations.

---

## Functional Requirements

### FR-1 Instance Cache
**Description**: Replace `@lru_cache` with instance cache for all computed props in domain entities.  
**Priority**: P0  
**Dependencies**: Python ≥ 3.8 or back-port helper.

### FR-2 Aggregate Mutation Guards
**Description**: Prevent external code from mutating `_Recipe` without `Meal`.  
**Priority**: P0

### FR-3 Unified `update_properties`
**Description**: Introduce shared mixin and refactor existing entities.  
**Priority**: P1

### FR-4 High-Coverage Tests
**Description**: Add/expand Pytest suite to ≥90 % coverage.  
**Priority**: P0

---

## Non-Functional Requirements

### Performance
- Caching must reduce repeated heavy computations by ≥95 % in hot-path benchmarks.

### Reliability
- Cache invalidation must occur within the same method that mutates dependent state.

### Security & Compliance
- Logs should redact PII if any (none expected in these entities).

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
| --- | --- | --- | --- |
| Stale cache after complex mutation | Medium | High | Centralised `_invalidate_caches` helper + unit tests |
| Breaking hidden callers that directly mutate `_Recipe` | High | Medium | Deprecation warnings + code search + integration tests |
| Python < 3.8 environments | Low | Medium | Provide back-port descriptor |
| Test coverage gap | Medium | Medium | CI fails if coverage < 90 % |

---

## Testing Strategy

### Unit Tests
- Test each computed property caching & invalidation.
- Verify aggregate invariants (author_id, meal_id consistency).  
- Validate `update_properties` event emission & version bump.

### Integration Tests
- End-to-end flow: create meal → add recipes → update → delete → ensures events fire and caches clear.

### Coverage
- Use `pytest-cov`; threshold in `pyproject.toml`/`setup.cfg`.

### Directory Layout
```
/tests
  └─ contexts/
       └─ recipes_catalog/
            └─ core/
                 └─ domain/
                      └─ meal/
                          test_meal.py
```

---

## Implementation Plan

### Phase 0: Prerequisites
- [ ] Agree on cache design (`cached_property` vs custom).
- [ ] Add CI step enforcing coverage threshold.

### Phase 1: Instance Cache Foundation
- [ ] Implement `_invalidate_caches` in `Entity` base.
- [ ] Replace `@lru_cache` with `@cached_property`.
- [ ] Add invalidation calls to mutating setters/methods.

### Phase 2: Aggregate Integrity
- [ ] Guard `_Recipe` mutations; expose `Meal` APIs.
- [ ] Refactor existing call-sites.

### Phase 3: `update_properties` Standardisation
- [ ] Introduce mixin; migrate `Meal`, `_Recipe`, others.

### Phase 4: Testing & Polish
- [ ] Write/expand Pytests to ≥90 %.
- [ ] Update docs & runbook.

### Rollout Strategy
- Feature branch with incremental PRs.  
- Each phase behind its own PR; merge when CI green.  
- Canary deploy to staging; monitor error rate.

---

## Monitoring and Observability
- Metric: cache hit rate per entity (custom Prometheus counter).  
- Metric: domain validation exceptions/min after deploy.  
- Alert if cache hit rate <50 % for 24 h (indicates invalidation loop).

---

## Documentation Requirements
- ADR: "Switch to instance-level cached_property".  
- README update for domain guidelines.  
- Docstrings on new mixins/helpers.

---

## Dependencies and Prerequisites
- Python 3.10 runtime (current project).  
- `pytest`, `pytest-cov` dev-deps.

---

## Timeline and Milestones
| Milestone | Target Date |
| --- | --- |
| Phase 0 complete | +2 d |
| Phase 1 merge | +6 d |
| Phase 2 merge | +10 d |
| Phase 3 merge | +14 d |
| Coverage 90 % | +16 d |
| Production deploy | +18 d |

---

## Open Questions and Decisions
1. Should we back-port `cached_property` for Python < 3.8 or enforce ≥3.8?  
2. Do any external services introspect `Recipe` directly (e.g., GraphQL resolvers) that need adaptation?  
3. Preferred domain error class hierarchy?  
4. Desired Prometheus label cardinality for cache metrics?

### Required Approvals
- [ ] Tech Lead (Domain)  
- [ ] QA Lead  
- [ ] Product Owner 