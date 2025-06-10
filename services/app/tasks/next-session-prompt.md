# Repository Refactoring - Next Session Prompt

## Current Status Summary

**✅ PHASE 0 COMPLETED**: Comprehensive testing infrastructure is complete and validated
- **Test Suite**: 1895+ lines of comprehensive tests across 5 focused modules
- **Test Results**: 55/55 tests passing consistently with isolated unit tests  
- **Mock Models**: Full complexity replication with 80+ column composite fields, relationships, edge cases
- **Coverage**: All major SaGenericRepository methods thoroughly tested
- **File Organization**: Successfully split 3000+ line test file into maintainable focused modules

**📋 CURRENT TASK**: Ready to proceed with **Phase 3: Refactor SaGenericRepository Core Logic**

---

## Context for AI Assistant

You are continuing a repository pattern refactoring project. The previous session completed **Phase 0** (comprehensive testing) and the test infrastructure is now ready. 

**CRITICAL SUCCESS FACTORS:**
1. **NO REFACTORING WITHOUT TESTS**: All Phase 0 tests MUST pass after every refactoring step
2. **Backward Compatibility**: All existing method signatures and behavior must remain identical
3. **Test-Driven Refactoring**: Run tests after each change to ensure no regressions

---

## Phase 3 Tasks (NEXT PRIORITIES)

### Immediate Tasks for This Session:

#### 3.0.0-3.0.1 **MANDATORY PRE-FLIGHT CHECKS**
- [ ] **CRITICAL**: Run all Phase 0 tests to verify current state: `poetry run python -m pytest tests/contexts/seedwork/shared/adapters/test_seedwork_repository_*.py -v`
- [ ] **CRITICAL**: Confirm all 55+ tests are passing before ANY refactoring begins
- [ ] **CRITICAL**: Set up test-after-each-change workflow (run tests after every refactoring step)

#### 3.1-3.4 **Query Building Extraction** 
- [ ] 3.1 Extract query building from `SaGenericRepository.query()` method into separate `_build_query()` private method
- [ ] 3.2 Replace complex filter processing in `_apply_filters()` with FilterOperator pattern using operator factory  
- [ ] 3.3 Refactor `_filter_operator_selection()` to use `FilterOperatorFactory.get_operator(filter_name, column_type, filter_value)`
- [ ] 3.4 Simplify `filter_stmt()` method by delegating to `FilterOperator.apply(stmt, column, value)` pattern

#### 3.5-3.8 **Architecture Improvements**
- [ ] 3.5 Extract join logic from `_apply_filters()` into `JoinManager.handle_joins(stmt, required_joins: set[str])`
- [ ] 3.6 Replace hardcoded `ALLOWED_POSTFIX` with FilterOperator registry using @dataclass pattern
- [ ] 3.7 Add comprehensive error handling with try-catch blocks around query execution using new exception types
- [ ] 3.8 Implement structured logging throughout query execution pipeline using RepositoryLogger

---

## Key Files and Current State

### Test Files (DO NOT MODIFY - They define the contract)
- `tests/contexts/seedwork/shared/adapters/conftest.py` - Comprehensive mock models and fixtures
- `tests/contexts/seedwork/shared/adapters/test_seedwork_repository_core.py` - Core functionality tests  
- `tests/contexts/seedwork/shared/adapters/test_seedwork_repository_joins.py` - Join scenario tests
- `tests/contexts/seedwork/shared/adapters/test_seedwork_repository_edge_cases.py` - Edge case tests
- `tests/contexts/seedwork/shared/adapters/test_seedwork_repository_behavior.py` - Behavior documentation

### Implementation Files (REFACTOR TARGETS)
- `src/contexts/seedwork/shared/adapters/seedwork_repository.py` - **PRIMARY REFACTOR TARGET**
- Foundation components (QueryBuilder, FilterOperator, etc.) - **TO BE CREATED**

### Reference Documentation
- `tasks/repository-analysis-reference.md` - Complete technical analysis of current implementation
- `tasks/tasks-prd-refactor-repository.md` - Full task breakdown and requirements

---

## Key Constraints and Requirements

### **ABSOLUTELY CRITICAL CONSTRAINTS:**
1. **Test-First Approach**: Run tests after EVERY change. If tests fail, revert immediately.
2. **Method Signature Preservation**: All public methods must keep exact same signatures
3. **Behavior Preservation**: Query results must be identical to current implementation  
4. **FilterColumnMapper Compatibility**: All existing mapper configurations must work unchanged
5. **Postfix Operator Behavior**: `_gte`, `_lte`, `_ne`, `_not_in`, `_is_not` must work exactly as before

### **Implementation Guidelines:**
- Use `from typing import TypedDict, Generic, Protocol` for type definitions
- Import `structlog` for structured logging: `poetry add structlog`
- Use `attrs` for data classes where appropriate: `from attrs import define, field`
- All async operations should use `anyio` for timeout handling
- Add appropriate pytest marks: `pytest.mark.anyio` for async modules

---

## Success Criteria for This Session

**MINIMUM REQUIREMENTS:**
- [ ] All 55+ Phase 0 tests still passing
- [ ] At least tasks 3.1-3.4 completed (query building extraction)
- [ ] No breaking changes to existing functionality  
- [ ] Clear progress toward cleaner architecture

**STRETCH GOALS:**
- [ ] Tasks 3.5-3.8 completed (architecture improvements)
- [ ] Foundation components (FilterOperator, JoinManager) implemented
- [ ] Structured logging and error handling added

---

## Notes and Warnings

### **IMPORTANT REMINDERS:**
- The repository implementation has extreme complexity (6+ filter operators, multi-level joins, tag groupby logic)
- Tag filtering logic in `MealRepo._tag_match_condition` is particularly complex - handle with care
- The `_not_in` operator has special NULL handling that must be preserved
- FilterColumnMapper join chains must maintain exact dependency order

### **KNOWN ISSUES TO ADDRESS LATER:**
- Self-referential many-to-many relationship testing temporarily removed (will complete in future session)
- Some foundation components (Phase 1-2) may need to be implemented during refactoring

### **TEST EXECUTION:**
- Use `poetry run python -m pytest` to run tests
- Use `./manage.py test` if conftest.py database fixtures cause issues
- Individual test modules can be run: `pytest tests/contexts/seedwork/shared/adapters/test_seedwork_repository_core.py -v`

---

## Getting Started Commands

```bash
# 1. Verify current test state
poetry run python -m pytest tests/contexts/seedwork/shared/adapters/test_seedwork_repository_*.py -v

# 2. Run specific test module  
poetry run python -m pytest tests/contexts/seedwork/shared/adapters/test_seedwork_repository_core.py -v

# 3. Watch mode for continuous testing (if available)
poetry run python -m pytest tests/contexts/seedwork/shared/adapters/test_seedwork_repository_core.py --watch

# 4. Current working directory
cd /home/jap/projects/menu-planning/backend/services/app
```

**START WITH:** Running all tests to confirm current state, then begin with task 3.1 (extract _build_query method). 