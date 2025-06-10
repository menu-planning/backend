####
Current Implementation References

  Core Repository Implementation
  
  - src/contexts/seedwork/shared/adapters/seedwork_repository.py - Current generic repository implementation that needs refactoring
    - Contains SaGenericRepository class with complex filter handling, query building, and join logic
    - Has FilterColumnMapper for mapping filter keys to SQLAlchemy columns
    - Implements filter operators with postfix support (_gte, _lte, _ne, etc.)
  
  Example Domain Repositories (showing current patterns)
  
  - src/contexts/products_catalog/core/adapters/repositories/product_repository.py
    - Shows how repositories extend CompositeRepository
    - Custom query methods (list_top_similar_names, list_filter_options)
    - Override sort_stmt for custom sorting logic
  
  - src/contexts/recipes_catalog/core/adapters/meal/repositories/meal_repository.py  
    - Tag filtering with complex conditions
    - Product name search integration
    - Custom query logic for tags and tags_not_exists

####
🚨 CRITICAL: TESTING BEFORE REFACTORING IMPERATIVE 🚨

**ABSOLUTELY MANDATORY**: Before ANY refactoring of existing code, comprehensive test suites MUST be created to deeply understand current behavior. This is not optional - it is IMPERATIVE.

**Why This Is Critical:**
- The `filter_stmt` method in `SaGenericRepository` is extremely complex with multiple operators, postfix handling, and edge cases
- ORM models like `MealSaModel` have intricate relationships (recipes, tags, associations) that affect query behavior
- Current integration tests like `test_meal_repo.py` may not cover all edge cases and depend on other components (mappers, etc.)
- Without comprehensive understanding of current behavior, refactoring will introduce bugs and break existing functionality

**Testing Requirements Before Refactoring:**
1. **Isolated Unit Tests**: Create tests that DON'T depend on mappers, database connections, or other complex components
2. **Edge Case Coverage**: Think HARD about all possible scenarios - empty filters, null values, complex joins, multiple postfix operators
3. **Behavior Documentation**: Tests must serve as living documentation of how the current system works
4. **Independent Test Data**: Use mock data and fixtures that don't depend on other system components
5. **Comprehensive Filter Testing**: Every filter operator (_gte, _lte, _ne, _not_in, _is_not, _not_exists) with every data type combination
6. **Join Logic Testing**: All possible join scenarios, including edge cases with multiple tables and duplicate joins
7. **Performance Baseline**: Establish performance benchmarks before refactoring to detect regressions

**DO NOT PROCEED** with refactoring until you have:
- [ ] 95%+ test coverage of current behavior
- [ ] Tests for every filter operator combination
- [ ] Tests for all join scenarios
- [ ] Tests for edge cases (empty results, null values, invalid filters)
- [ ] Tests that run independently without database or complex dependencies
- [ ] Clear understanding of how `filter_stmt`, `_apply_filters`, and `_filter_operator_selection` currently work

####
Relevant Files

  Core Components

  - src/contexts/seedwork/shared/adapters/query_builder.py - New QueryBuilder class with SQLAlchemy Select statement construction
  - tests/contexts/seedwork/shared/adapters/test_query_builder.py - Unit tests for QueryBuilder
  - src/contexts/seedwork/shared/adapters/filter_operators.py - FilterOperator base class and implementations (EqualsOperator, GreaterThanOperator, etc.)
  - tests/contexts/seedwork/shared/adapters/test_filter_operators.py - Unit tests for all filter operators
  - src/contexts/seedwork/shared/adapters/filter_validator.py - Input validation for filters using Pydantic
  - tests/contexts/seedwork/shared/adapters/test_filter_validator.py - Unit tests for filter validation
  - src/contexts/seedwork/shared/adapters/join_manager.py - Handles table joins and relationship management
  - tests/contexts/seedwork/shared/adapters/test_join_manager.py - Unit tests for join management

  Error Handling & Logging

  - src/contexts/seedwork/shared/adapters/repository_exceptions.py - Enhanced exception hierarchy with context
  - src/contexts/seedwork/shared/adapters/repository_logger.py - Structured logging with performance tracking
  - tests/contexts/seedwork/shared/adapters/test_repository_exceptions.py - Unit tests for exceptions
  - tests/contexts/seedwork/shared/adapters/test_repository_logger.py - Unit tests for logging

  Mixins & Utilities

  - src/contexts/seedwork/shared/adapters/mixins/tag_filter_mixin.py - Reusable tag filtering logic
  - src/contexts/seedwork/shared/adapters/mixins/soft_delete_mixin.py - Soft delete handling
  - src/contexts/seedwork/shared/adapters/mixins/audit_mixin.py - Created/updated timestamp handling
  - tests/contexts/seedwork/shared/adapters/mixins/test_tag_filter_mixin.py - Unit tests for tag filtering
  - tests/contexts/seedwork/shared/adapters/mixins/test_soft_delete_mixin.py - Unit tests for soft delete
  - tests/contexts/seedwork/shared/adapters/mixins/test_audit_mixin.py - Unit tests for audit functionality

  Refactored Core

  - src/contexts/seedwork/shared/adapters/seedwork_repository.py - Refactored with new components (MODIFIED)
  - tests/contexts/seedwork/shared/adapters/test_seedwork_repository.py - Enhanced unit tests

  Domain Repository Updates

  - src/contexts/recipes_catalog/core/adapters/meal/repositories/meal_repository.py - Updated to use new components (MODIFIED)
  - src/contexts/products_catalog/core/adapters/repositories/product_repository.py - Updated implementation (MODIFIED)
  - tests/contexts/recipes_catalog/core/adapters/meal/repositories/test_meal_repository.py - Enhanced unit tests
  - tests/contexts/products_catalog/core/adapters/repositories/test_product_repository.py - Enhanced unit tests
  - tests/contexts/recipes_catalog/integration/meal/test_meal_repo.py - Enhanced integration tests (MODIFIED)
  - tests/contexts/products_catalog/integration/test_repository.py - Enhanced integration tests (MODIFIED)

  Type Definitions

  - src/contexts/seedwork/shared/adapters/types.py - TypedDict definitions for filters and configuration
  - tests/contexts/seedwork/shared/adapters/test_types.py - Unit tests for type definitions

  Current Implementation Patterns (MUST MAINTAIN COMPATIBILITY)

  FilterColumnMapper Pattern:
  ```python
  filter_to_column_mappers = [
      FilterColumnMapper(
          sa_model_type=ProductSaModel,
          filter_key_to_column_name={"name": "name", "barcode": "barcode"},
      ),
      FilterColumnMapper(
          sa_model_type=SourceSaModel,
          filter_key_to_column_name={"source": "name"},
          join_target_and_on_clause=[(SourceSaModel, ProductSaModel.source)],
      ),
  ]
  ```

  Repository Initialization Pattern:
  ```python
  class ProductRepo(CompositeRepository[Product, ProductSaModel]):
      def __init__(self, db_session: AsyncSession):
          self._generic_repo = SaGenericRepository(
              db_session=self._session,
              data_mapper=ProductMapper,
              domain_model_type=Product,
              sa_model_type=ProductSaModel,
              filter_to_column_mappers=ProductRepo.filter_to_column_mappers,
          )
  ```

  Query Method Signature:
  ```python
  async def query(
      self,
      *,
      filter: dict[str, Any] | None = None,
      starting_stmt: Select | None = None,
      sort_stmt: Callable | None = None,
      limit: int | None = None,
      already_joined: set[str] | None = None,
      sa_model: Type[S] | None = None,
      _return_sa_instance: bool = False,
  ) -> list[E]:
  ```

  Filter Operators with Postfix:
  - _gte: Greater than or equal
  - _lte: Less than or equal  
  - _ne: Not equal
  - _not_in: Not in list
  - _is_not: IS NOT (SQL)
  - _not_exists: Does not exist

  Notes

  - Use poetry run python -m pytest to run tests
  - Use from typing import TypedDict, Generic, Protocol for type definitions
  - Import structlog for structured logging: poetry add structlog
  - Use attrs for data classes where appropriate: from attrs import define, field
  - All async operations should use anyio for timeout handling
  - Critical: Maintain backward compatibility - all existing repository methods must continue to work
  - **Async Operations**: Use anyio instead of asyncio for all async operations (timeout handling, task groups, etc.)
  - **Test Marks**: Always add appropriate pytest marks:
    - `pytest.mark.anyio` for all modules that have async functions
    - `pytest.mark.integration` for modules that have integration tests
    - `pytest.mark.e2e` for modules that have end-to-end tests
  - **Testing Infrastructure Issue**: Currently conftest.py has auto-used database fixtures that force ALL tests to connect to database, even pure unit tests. Use `./manage.py test` to run tests until this is fixed.
  
Backward Compatibility Requirements:

  - All existing repository methods MUST maintain exact same signatures
  - FilterColumnMapper behavior must remain identical
  - Filter postfix operators (_gte, _lte, etc.) must work exactly as before
  - Join handling and duplicate detection must produce same results
  - Sort behavior including nulls_last must be preserved
  - The seen set tracking for domain entities must continue working
  - All existing domain repositories must work without modification
  - Query results must be identical to current implementation
  - Error types and messages should remain consistent
  - Performance should not degrade for existing use cases

####
Tasks

**PHASE 0: MANDATORY COMPREHENSIVE TESTING (MUST COMPLETE BEFORE ANY REFACTORING)**

- [ ] 0.1 **CRITICAL**: Study and map all SA model relationships for test design
  - [ ] 0.1.1 Analyze MealSaModel relationships: recipes, tags, nutri_facts (composite), menu_id, etc.
  - [ ] 0.1.2 Analyze RecipeSaModel relationships: ingredients, ratings, tags, nutri_facts, meal_id, etc.
  - [ ] 0.1.3 Analyze complex association tables: meals_tags_association, recipes_tags_association
  - [ ] 0.1.4 Map FilterColumnMapper configurations used by MealRepo and RecipeRepo
  - [ ] 0.1.5 Document all join scenarios and relationship paths for mock model design
  - [ ] 0.1.6 Identify all filter operators and postfix combinations used in practice
- [ ] 0.2 **CRITICAL**: Create comprehensive mock models that replicate relationship complexity
  - [ ] 0.2.1 Create mock SA models with same relationship structure as MealSaModel/RecipeSaModel
  - [ ] 0.2.2 Create mock association tables and foreign key relationships
  - [ ] 0.2.3 Create mock FilterColumnMapper configurations with multi-level joins
  - [ ] 0.2.4 Ensure mock models support all column types (str, int, bool, list, composite, etc.)
  - [ ] 0.2.5 Create mock data generators for complex nested structures
- [ ] 0.3 **CRITICAL**: Create isolated unit tests for SaGenericRepository.filter_stmt() method
  - [ ] 0.3.1 Test every filter operator (_gte, _lte, _ne, _not_in, _is_not, _not_exists) with different data types
  - [ ] 0.3.2 Test postfix removal and validation logic with edge cases
  - [ ] 0.3.3 Test column mapping logic with various FilterColumnMapper configurations
  - [ ] 0.3.4 Test distinct application logic with list filters and joins
  - [ ] 0.3.5 Mock SQLAlchemy components to avoid database dependencies
- [ ] 0.4 **CRITICAL**: Create isolated unit tests for SaGenericRepository._filter_operator_selection() method
  - [ ] 0.4.1 Test operator selection for each postfix with different column types
  - [ ] 0.4.2 Test fallback logic for unknown operators
  - [ ] 0.4.3 Test edge cases with None values, empty lists, type mismatches
  - [ ] 0.4.4 Test column type detection with various SQLAlchemy column types
- [ ] 0.5 **CRITICAL**: Create isolated unit tests for SaGenericRepository._apply_filters() method
  - [ ] 0.5.1 Test join logic with FilterColumnMapper configurations
  - [ ] 0.5.2 Test already_joined tracking and duplicate join prevention
  - [ ] 0.5.3 Test filter application order and statement building
  - [ ] 0.5.4 Test complex multi-table join scenarios using mock models
- [ ] 0.6 **CRITICAL**: Create isolated unit tests for SaGenericRepository.query() method
  - [ ] 0.6.1 Test complete query flow with mocked dependencies
  - [ ] 0.6.2 Test starting_stmt parameter handling
  - [ ] 0.6.3 Test sort_stmt callback functionality
  - [ ] 0.6.4 Test limit and offset application
  - [ ] 0.6.5 Test _return_sa_instance flag behavior
- [ ] 0.7 **CRITICAL**: Test complex filtering scenarios using mock models
  - [ ] 0.7.1 Test multi-level joins (Meal -> Recipe -> Ingredient) with mock models
  - [ ] 0.7.2 Test composite field filtering (nutri_facts) with mock models
  - [ ] 0.7.3 Test association table filtering (tags) with mock models
  - [ ] 0.7.4 Test performance with large mock datasets (1000+ records)
- [ ] 0.8 **CRITICAL**: Document current behavior through test cases
  - [ ] 0.8.1 Create test cases that serve as behavior documentation
  - [ ] 0.8.2 Test and document all edge cases and error conditions
  - [ ] 0.8.3 Create performance baseline tests with timing measurements
  - [ ] 0.8.4 Document any inconsistencies or bugs found in current implementation
- [ ] 0.9 **VERIFICATION**: Ensure 95%+ test coverage before proceeding
  - [ ] 0.9.1 Run coverage analysis on all SaGenericRepository code
  - [ ] 0.9.2 Identify and test any uncovered code paths
  - [ ] 0.9.3 Create missing tests for edge cases
  - [ ] 0.9.4 Verify all tests pass consistently and independently

**⚠️ WARNING: DO NOT PROCEED TO PHASE 1 UNTIL ALL PHASE 0 TASKS ARE COMPLETE ⚠️**

**Note**: Specific repository testing (MealRepo, RecipeRepo, ProductRepo) will be handled in Phase 4 when those repositories are actually refactored. Phase 0 focuses on the core SaGenericRepository that underlies all of them.

**PHASE 1: Foundation Components (Only After Phase 0 Complete)**

- [x] 1.0 Create Foundation Components for Query Building
  - [x] 1.1 Create QueryBuilder base structure using Generic[E, S] typing with TypeVar bounds from Entity and SaBase
  - [x] 1.2 Implement QueryBuilder.init method accepting AsyncSession, sa_model_type: Type[S], and optional starting_stmt: Select
  - [x] 1.3 Add QueryBuilder.select() method returning Select statement with proper type hints
  - [x] 1.4 Implement QueryBuilder.where() method accepting FilterOperator instances and building WHERE clauses
  - [x] 1.5 Create QueryBuilder.join() method with automatic duplicate join detection using set[str] tracking
  - [x] 1.6 Add QueryBuilder.order_by() method supporting both ascending/descending with nulls_last from SQLAlchemy
  - [x] 1.7 Implement QueryBuilder.limit() and QueryBuilder.offset() methods with proper validation (limit > 0, offset >= 0)
  - [x] 1.8 Create QueryBuilder.distinct() method for handling list-based filters
  - [x] 1.9 Add QueryBuilder.build() method returning final Select statement with all applied operations
  - [x] 1.10 Implement QueryBuilder.execute() method using AsyncSession.execute and returning list[E] with proper mapping
  - [x] 1.11 Add comprehensive type hints using TYPE_CHECKING pattern for forward references
  - [x] 1.12 Create detailed docstrings with examples for each QueryBuilder method
  - [x] 1.13 Create FilterOperator base class with abstract apply(stmt: Select, column: ColumnElement, value: Any) -> Select method
  - [x] 1.14 Implement EqualsOperator, GreaterThanOperator, LessThanOperator, InOperator, NotInOperator, ContainsOperator classes
  - [x] 1.15 Create FilterOperatorFactory with register_operator() and get_operator(filter_name: str, column_type: type, value: Any) methods
  - [x] 1.16 Add comprehensive unit tests in tests/contexts/seedwork/shared/adapters/test_query_builder.py with AsyncSession fixtures
  - [x] 1.17 Write unit tests for all FilterOperator implementations with edge cases (None values, empty lists, type mismatches)
  - [x] 1.18 Test QueryBuilder with complex multi-table joins and verify duplicate join detection works correctly
- 2.0 Implement Enhanced Error Handling and Logging System
  - [x] 2.1 Install structlog package: poetry add structlog and configure structured logging in logging/logger.py
  - [x] 2.2 Create RepositoryException base class inheriting from Generic[R] Exception with repository_type, operation, and context fields
  - [x] 2.3 Implement RepositoryQueryException with filter_values: dict[str, Any], sql_query: str, and execution_time: float fields
  - [x] 2.4 Create FilterValidationException with invalid_filters: list[str] and suggested_filters: list[str] fields
  - [x] 2.5 Implement JoinException with join_path: str and relationship_error: str fields for relationship mapping errors
  - [x] 2.6 Add EntityMappingException for data mapper errors with domain_obj: E and sa_obj: S context
  - [x] 2.7 Create RepositoryLogger class using structlog with correlation_id generation using uuid4().hex
  - [x] 2.8 Add RepositoryLogger.track_query() context manager measuring execution time using time.perf_counter()
  - [x] 2.9 Implement RepositoryLogger.log_filter() method with filter_key, filter_value, and filter_type parameters
  - [x] 2.10 Create RepositoryLogger.log_join() method tracking table joins with join_target and join_condition
  - [x] 2.11 Add RepositoryLogger.log_performance() method tracking query_time, result_count, and memory_usage using psutil
  - [x] 2.12 Implement warning logs for potential performance issues (large result sets > 1000, complex joins > 3 tables, missing indexes)
  - [x] 2.13 Create debug logging for SQL query construction steps with parameter binding information
  - [x] 2.14 Add integration with existing logger in src/logging/logger.py to maintain consistency
  - [x] 2.15 Write comprehensive unit tests in tests/contexts/seedwork/shared/adapters/test_repository_exceptions.py
  - [x] 2.16 Create unit tests for RepositoryLogger with mocked time and psutil dependencies
  - [x] 2.17 Test exception hierarchy and ensure proper inheritance chain with Generic typing
- 3.0 Refactor SaGenericRepository Core Logic
  - [ ] 3.0.0 **MANDATORY**: Run all Phase 0 tests before starting refactoring
  - [ ] 3.0.1 **MANDATORY**: After each refactoring step, run all tests to ensure no regression
  - [ ] 3.1 Extract query building from SaGenericRepository.query() method into separate _build_query() private method
  - [ ] 3.2 Replace complex filter processing in _apply_filters() with FilterOperator pattern using operator factory
  - [ ] 3.3 Refactor _filter_operator_selection() to use FilterOperatorFactory.get_operator(filter_name, column_type, filter_value)
  - [ ] 3.4 Simplify filter_stmt() method by delegating to FilterOperator.apply(stmt, column, value) pattern
  - [ ] 3.5 Extract join logic from _apply_filters() into JoinManager.handle_joins(stmt, required_joins: set[str])
  - [ ] 3.6 Replace hardcoded ALLOWED_POSTFIX with FilterOperator registry using @dataclass pattern
  - [ ] 3.7 Add comprehensive error handling with try-catch blocks around query execution using new exception types
  - [ ] 3.8 Implement structured logging throughout query execution pipeline using RepositoryLogger
  - [ ] 3.9 Add input validation for all filter values using FilterValidator.validate(filters: dict[str, Any])
  - [ ] 3.10 Refactor execute_stmt() method to use QueryBuilder pattern and add performance logging
  - [ ] 3.11 Add timeout handling for query execution using anyio.fail_after(timeout=30.0) wrapper
  - [ ] 3.12 Implement query result caching preparation (add hooks for future caching layer)
  - [ ] 3.13 CRITICAL: Ensure all existing method signatures remain identical for backward compatibility
  - [ ] 3.14 Add deprecation warnings for complex internal methods that should not be used directly
  - [ ] 3.15 Create FilterValidator class using Pydantic BaseModel with validate_filter_types() and validate_filter_keys() methods
  - [ ] 3.16 Implement JoinManager with track_joins: set[str], add_join(), and is_join_needed() methods
  - [ ] 3.17 Add performance monitoring with slow query detection (> 1 second) and automatic logging
  - [ ] 3.18 Write comprehensive unit tests in tests/contexts/seedwork/shared/adapters/test_seedwork_repository.py
  - [ ] 3.19 Create regression tests comparing old vs new repository behavior using existing test data
  - [ ] 3.20 Test all filter operators and postfix combinations (_gte, _lte, _ne, _not_in, _is_not, _not_exists)
- 4.0 Update Domain-Specific Repositories
  - [ ] 4.0 **MANDATORY**: Create comprehensive tests for specific repositories before refactoring
    - [ ] 4.0.1 **CRITICAL**: Test MealRepo tag filtering logic using relationship mapping from Phase 0
      - [ ] 4.0.1.1 Test _tag_match_condition() with all combinations of key-value-author_id tuples
      - [ ] 4.0.1.2 Test _tag_not_exists_condition() with complex tag negation scenarios
      - [ ] 4.0.1.3 Test product_name filtering integration with ProductRepo
      - [ ] 4.0.1.4 Test all FilterColumnMapper configurations for multi-level joins
      - [ ] 4.0.1.5 Test performance with large datasets and complex tag combinations
    - [ ] 4.0.2 **CRITICAL**: Test RecipeRepo behavior using relationship mapping from Phase 0
      - [ ] 4.0.2.1 Test tag filtering logic (similar to MealRepo but for "recipe" type)
      - [ ] 4.0.2.2 Test ingredient filtering through joins
      - [ ] 4.0.2.3 Test rating and nutri_facts filtering
      - [ ] 4.0.2.4 Test all column types and relationship paths
    - [ ] 4.0.3 **CRITICAL**: Test ProductRepo behavior before refactoring
      - [ ] 4.0.3.1 Test source relationship filtering and joins
      - [ ] 4.0.3.2 Test list_top_similar_names() functionality
      - [ ] 4.0.3.3 Test all ProductSaModel column types and relationships
      - [ ] 4.0.3.4 Test custom query methods and sort logic
  - [ ] 4.1 Create TagFilterMixin with build_tag_filter(tags: list[tuple[str, str, str]]) -> ColumnElement[bool] method
  - [ ] 4.2 Implement TagFilterMixin.build_negative_tag_filter() for tags_not_exists functionality
  - [ ] 4.3 Add TagFilterMixin.validate_tag_format() to ensure tuple[str, str, str] format
  - [ ] 4.4 Refactor MealRepo.query() method to use TagFilterMixin for tag-based filtering logic
  - [ ] 4.5 Replace complex _tag_match_condition() in MealRepo with TagFilterMixin.build_tag_filter()
  - [ ] 4.6 Extract _tag_not_exists_condition() logic into TagFilterMixin.build_negative_tag_filter() method
  - [ ] 4.7 Update MealRepo.get_meal_by_recipe_id() to use enhanced error handling with RecipeNotFoundException
  - [ ] 4.8 Add structured logging to MealRepo operations using RepositoryLogger.create_logger("MealRepo")
  - [ ] 4.9 Refactor ProductRepo to use new FilterOperator system for complex product filtering
  - [ ] 4.10 Update ClientRepo and MenuRepo to use TagFilterMixin for consistent tag filtering across repositories
  - [ ] 4.11 Add repository-specific performance logging for slow operations (> 1 second query time)
  - [ ] 4.12 Implement SoftDeleteMixin with is_discarded_filter() and exclude_discarded() methods
  - [ ] 4.13 Add AuditMixin for automatic created_at/updated_at timestamp handling with set_timestamps() method
  - [ ] 4.14 Update all repository constructors to accept optional RepositoryLogger for dependency injection
  - [ ] 4.15 WARNING: Test each repository individually after refactoring to ensure no breaking changes
  - [ ] 4.16 Create unit tests in tests/contexts/recipes_catalog/core/adapters/meal/repositories/test_meal_repository.py
  - [ ] 4.17 Create unit tests in tests/contexts/products_catalog/core/adapters/repositories/test_product_repository.py
  - [ ] 4.18 Write unit tests for all mixins in tests/contexts/seedwork/shared/adapters/mixins/
  - [ ] 4.19 Test TagFilterMixin with complex tag combinations (AND/OR logic, nested conditions)
  - [ ] 4.20 Verify that all existing repository methods maintain exact same behavior
- 5.0 Create Comprehensive Testing Suite
  - [ ] 5.1 Create pytest fixtures in tests/contexts/seedwork/shared/adapters/conftest.py for AsyncSession and sample SQLAlchemy models
  - [ ] 5.2 Write unit tests for QueryBuilder.where() with all FilterOperator types using @pytest.mark.parametrize
  - [ ] 5.3 Test QueryBuilder.join() with complex multi-table joins and duplicate join detection
  - [ ] 5.4 Create performance tests for QueryBuilder using pytest-benchmark: poetry add pytest-benchmark --group dev
  - [ ] 5.5 Write comprehensive tests in tests/contexts/seedwork/shared/adapters/test_filter_operators.py for each operator with edge cases
  - [ ] 5.6 Test FilterValidator with invalid filter combinations and verify helpful error messages
  - [ ] 5.7 Create integration tests for full query execution pipeline using test database with sample data
  - [ ] 5.8 Test TagFilterMixin with complex tag combinations in tests/contexts/seedwork/shared/adapters/mixins/test_tag_filter_mixin.py
  - [ ] 5.9 Write regression tests in tests/contexts/seedwork/shared/adapters/test_regression.py comparing old vs new behavior
  - [ ] 5.10 Create performance regression tests measuring query execution time for complex scenarios
  - [ ] 5.11 Test error handling scenarios: database connection failures, invalid SQL, timeout conditions
  - [ ] 5.12 Add memory usage tests for large result sets using memory_profiler: poetry add memory-profiler --group dev
  - [ ] 5.13 Test concurrent repository access with multiple async operations using anyio.create_task_group()
  - [ ] 5.14 Create mutation testing setup to verify test quality using mutmut: poetry add mutmut --group dev
  - [ ] 5.15 WARNING: All tests must pass before merging - aim for 95%+ coverage on new components
  - [ ] 5.16 Create end-to-end tests in tests/contexts/recipes_catalog/integration/meal/test_meal_repo.py for MealRepo
  - [ ] 5.17 Create end-to-end tests in tests/contexts/products_catalog/integration/test_repository.py for ProductRepo
  - [ ] 5.18 Add stress tests with large datasets (10,000+ records) to verify performance doesn't degrade
  - [ ] 5.19 Test all filter postfix combinations with various data types (strings, integers, booleans, lists)
  - [ ] 5.20 Create comprehensive test documentation with examples for future developers
- 6.0 Fix Test Infrastructure and Optimize Testing
  - [ ] 6.1 Remove auto-used database fixtures from conftest.py that force ALL tests to connect to database
  - [ ] 6.2 Create separate conftest.py files for unit tests vs integration tests
  - [ ] 6.3 Add pytest marks and collection rules to distinguish unit, integration, and e2e tests
  - [ ] 6.4 Create database fixtures that are only used when explicitly needed (not auto-used)
  - [ ] 6.5 Update all existing unit tests to run without database dependencies
  - [ ] 6.6 Create mock fixtures for common database-related objects for unit testing
  - [ ] 6.7 Ensure unit tests can run with simple `pytest` command without database setup
  - [ ] 6.8 Keep integration tests using `python manage.py test` or explicit database fixtures
  - [ ] 6.9 Update CI/CD pipeline to run unit tests separately from integration tests
  - [ ] 6.10 Add performance testing for test suite execution time (unit tests should be < 1 second)
#### 