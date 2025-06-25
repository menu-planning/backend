# 🚨 CRITICAL: Performance Regressions & Domain Integrity 🚨

Refactoring core domain caching and aggregate rules carries **high risk** of performance regressions and hidden
state-leak bugs. Follow *every* prerequisite and checkpoint.

# Task List: Domain Refactor – Instance-Level Caching & Root-Aggregate Hardening

## Implementation Approach  
Enhancement + bug-fix refactor of existing domain code using **TDD**, starting from zero coverage.  
Primary goals: per-instance caching, strict aggregate boundaries, unified `update_properties`, ≥90 % test coverage, and measurable performance gains.

## Current Implementation References
### Core Components
- `src/contexts/**/domain/meal.py` – `Meal` aggregate root (MODIFIED)
- `src/contexts/**/domain/_recipe.py` – `_Recipe` entity (MODIFIED)
- `src/contexts/**/domain/**.py` – other domain entities using `@lru_cache` (MODIFIED)

### Shared Base / Helpers
- `src/contexts/shared/domain/entity.py` – `Entity` base class (MODIFIED)
- `src/contexts/shared/domain/mixins.py` – **NEW** `UpdatePropertiesMixin`

### Tests
- `tests/contexts/**/domain/**` – mirrored test hierarchy (NEW)

## Testing Strategy
- **Red-Green-Refactor**: write failing tests first, implement code, then clean up.
- `pytest` + `pytest-cov`; CI fails if coverage < 90 % for `*/domain/*`.
- Performance assertions: cache hit ratio ≥95 % & ≥30 % speed-up vs baseline heavy calculation.

---

# 📊 Tasks

## Phase 0: Mandatory Prerequisites ⚠️
**Skipping guarantees failure**

### 0.1 Project Tooling & Baseline
- [x] 0.1.1 Add `pytest`, `pytest-cov`, `pytest-benchmark` to dev dependencies.
- [x] 0.1.2 Configure coverage threshold (90 %) in `pyproject.toml` or `setup.cfg`.
- [x] 0.1.3 Create local coverage enforcement script (`scripts/check-coverage.sh`) with 90% threshold validation.
- [ ] 0.1.4 Capture baseline performance for heavy computed properties (e.g., `nutri_facts`) using `pytest-benchmark`.

### 0.2 Characterisation Tests (Current Behaviour)
- [ ] 0.2.1 Mirror `src/contexts/**/domain/**` structure under `tests/contexts/...`.
- [ ] 0.2.2 Write tests documenting current outputs of cached properties & mutation flows (expect shared cache BUGS).
- [ ] 0.2.3 Mark failing expectations with `xfail` to lock current buggy behaviour.

**🛑 CHECKPOINT: Tooling, CI, and baseline tests in place**

---

## Phase 1: Instance-Level Cache Foundation

### 1.0 Design & Helper Implementation
- [ ] 1.0.1 Create `_invalidate_caches(self, *attrs)` in `Entity` base; track `_cached_attrs`.
- [ ] 1.0.2 Provide back-port shim for `functools.cached_property` if Py < 3.8 (doc only).

### 1.1 Replace `@lru_cache` Decorators
- [ ] 1.1.1 **Search** for all uses of `functools.lru_cache` in domain modules.
- [ ] 1.1.2 For each, write a **failing test** asserting per-instance caching + invalidation on mutation.
- [ ] 1.1.3 Convert to `@cached_property`; register attr names in `_cached_attrs`.
- [ ] 1.1.4 Call `_invalidate_caches(...)` inside mutators affecting cached data.
- [ ] 1.1.5 Ensure calculated values remain identical pre/post refactor.

### 1.2 Documentation & Logging
- [ ] 1.2.1 Add debug-level logs in `_invalidate_caches` when caches are cleared.
- [ ] 1.2.2 Update docstrings for all converted properties.

**🛑 CHECKPOINT: All computed properties use instance-level cache; tests green.**

---

## Phase 2: Aggregate Integrity Enforcement

### 2.0 Audit & Test
- [ ] 2.0.1 Enumerate all public setters/mutators on `_Recipe` that can alter state.
- [ ] 2.0.2 Write failing tests asserting direct mutation outside `Meal` raises `DomainError`.

### 2.1 Guard Implementation
- [ ] 2.1.1 Introduce `_check_mutation_allowed` in `_Recipe`; inspect call stack or use context manager from `Meal`.
- [ ] 2.1.2 Rename public setters to protected (e.g., `_set_name`).

### 2.2 Meal-Centric APIs
- [ ] 2.2.1 Add/verify `Meal.create_recipe`, `Meal.update_recipes`, `Meal.delete_recipe`, `Meal.copy_recipe` endpoints.
- [ ] 2.2.2 Ensure these call protected `_Recipe` mutators internally.
- [ ] 2.2.3 Update integration tests to use only `Meal` APIs.

### 2.3 Deprecation & Cleanup
- [ ] 2.3.1 Emit `DeprecationWarning` for legacy direct mutation calls.
- [ ] 2.3.2 Refactor codebase eliminating all warnings.

**🛑 CHECKPOINT: Direct recipe mutation blocked; all green tests.**

---

## Phase 3: Standardise `update_properties`

### 3.0 Mixin Design
- [ ] 3.0.1 Create `UpdatePropertiesMixin` with contract: validate → apply → post_update → version bump → cache invalidate.
- [ ] 3.0.2 Unit-test mixin in isolation with dummy entity.

### 3.1 Entity Migrations
- [ ] 3.1.1 Migrate `Meal.update_properties` to mixin.
- [ ] 3.1.2 Migrate `_Recipe` and any other entities using custom patterns.
- [ ] 3.1.3 Ensure invariants and domain events fire once.

### 3.2 Cache Integration
- [ ] 3.2.1 Ensure mixin invokes `_invalidate_caches` after successful updates.

**🛑 CHECKPOINT: Uniform `update_properties` across domain; all tests green.**

---

## Phase 4: Comprehensive Test Suite & Coverage ≥ 90 %

### 4.0 Test Expansion
- [ ] 4.0.1 Add missing unit tests for edge cases (empty recipes list, extreme nutrition values, etc.).
- [ ] 4.0.2 Parameterise tests across multiple entities to avoid duplication (DRY).

### 4.1 Performance Benchmarks
- [ ] 4.1.1 Benchmark heavy computation before/after mutation to verify cache effectiveness.
- [ ] 4.1.2 Assert > 95 % cache hit ratio using custom metrics or mock-spy.

### 4.2 Coverage & CI
- [ ] 4.2.1 Run `pytest --cov=src/contexts --cov-report=term-missing` aiming for ≥ 90 %.
- [ ] 4.2.2 Optimize tests if coverage shortfall; add missing branches.

**🛑 CHECKPOINT: Coverage met; performance benchmarks passing.**

---

## Phase 5: Final Validation & Documentation

### 5.0 End-to-End Validation
- [ ] 5.0.1 Re-run full CI pipeline on clean environment.
- [ ] 5.0.2 Execute performance regression suite comparing baseline (Phase 0) metrics.
- [ ] 5.0.3 Conduct manual QA for key user flows (create meal → add recipe → update → delete).

### 5.1 Documentation & ADR
- [ ] 5.1.1 Write ADR: "Switch to instance-level cached_property & root-aggregate enforcement".
- [ ] 5.1.2 Update README with caching guidelines and aggregate rules.

### 5.2 Rollout & Monitoring
- [ ] 5.2.1 Merge feature branch behind PRs; deploy to staging.
- [ ] 5.2.2 Configure Prometheus counters: cache hit rate, domain validation exceptions/min.
- [ ] 5.2.3 Set alert: cache hit rate < 50 % for 24 h.

### 5.3 Post-Deploy Follow-Up
- [ ] 5.3.1 Monitor metrics for one week; address anomalies.
- [ ] 5.3.2 Close out deprecated APIs after grace period.

---

## 🎯 Success Criteria
1. All computed properties use instance-level caching with automatic invalidation.  
2. Direct `_Recipe` mutation outside `Meal` context raises `DomainError`.  
3. `update_properties` unified and respects contract across entities.  
4. Test coverage ≥ 90 % for `*/domain/*`; CI enforces.  
5. Performance benchmark shows ≥ 30 % speed-up & ≥ 95 % cache hit ratio.  
6. No regressions in functional behaviour; all CI jobs green. 