# PRD: Codebase Refactoring for Improved Maintainability

## Introduction/Overview

This PRD outlines a comprehensive refactoring effort for the menu-planning backend application to address critical maintainability issues that are slowing down development and introducing bugs. The refactoring focuses on three main areas: simplifying the complex mapping between different data representations, improving the generic repository pattern, and establishing a cleaner testing infrastructure. The goal is to maintain the sophisticated DDD architecture while reducing accidental complexity that has accumulated over time.

## Goals

1. **Reduce mapping-related bugs by 80%** through implementing a unified mapping strategy between Pydantic schemas, domain entities, SQLAlchemy models, and attrs value objects
2. **Simplify the generic repository pattern** while maintaining powerful querying capabilities for Products, Recipes, and Meals
3. **Establish a clear, maintainable testing infrastructure** with reduced duplication and proper async/fixture handling
4. **Reduce development time for new features by 40%** through clearer patterns and better error handling
5. **Improve code readability** by reducing entity complexity and establishing clear boundaries

## User Stories

1. **As a developer**, I want to map between Pydantic schemas and domain models without worrying about null/type mismatches, so that I can focus on business logic rather than data transformation bugs
2. **As a developer**, I want to use a repository pattern that is both powerful and easy to debug, so that I can quickly identify and fix query-related issues
3. **As a developer**, I want a testing setup that clearly handles async operations and SQLAlchemy sessions, so that I can write reliable tests without boilerplate
4. **As a developer**, I want smaller, more focused entities, so that I can understand and modify business logic without analyzing massive classes
5. **As a developer**, I want clear patterns for handling soft-deleted entities in relationships, so that I can avoid integrity errors

## Functional Requirements

### Phase 1: Mapping Infrastructure (Priority 1)

1. **The system must provide a centralized mapping registry** that handles transformations between Pydantic ↔ Domain ↔ SQLAlchemy ↔ attrs
2. **The mapping system must handle nullable fields explicitly** with clear rules for None propagation
3. **The system must provide automatic serialization handling** for sets, custom types, and nested models
4. **The mapping system must validate type compatibility at startup** rather than runtime
5. **The system must provide clear error messages** when mapping fails, including the full path to the problematic field
6. **The system must handle soft-deleted entities transparently** in relationship mappings
7. **The mapping system must support merge strategies** for SQLAlchemy to prevent integrity errors

### Phase 2: Repository Pattern Simplification (Priority 2)

8. **The system must provide a two-tier repository pattern**: 
   - Simple CRUD repository for basic operations
   - Advanced query repository for complex filtering (Products, Recipes, Meals)
9. **The repository must provide clear debugging hooks** for generated SQL queries
10. **The repository must handle async session management** without requiring manual session handling in business logic
11. **The repository must provide explicit methods** for including/excluding soft-deleted entities
12. **The repository pattern must support future AI/RAG capabilities** through extensible query interfaces

### Phase 3: Testing Infrastructure (Continuous with Phase 1 & 2)

13. **The system must provide a single, clear conftest.py** at the root level with shared fixtures
14. **Test fixtures must handle async SQLAlchemy sessions automatically** with proper cleanup
15. **The system must provide test factories** for creating valid domain entities and value objects
16. **Tests must use explicit transaction rollback** for database isolation
17. **The system must provide clear patterns** for testing each layer (domain, application, infrastructure)

### Phase 4: Entity Refactoring (Priority 3)

18. **Large entities must be split** into smaller aggregates with clear boundaries
19. **Each entity must have a maximum of 10 methods** excluding property getters/setters
20. **Complex business logic must be extracted** into domain services where appropriate
21. **Entity relationships must be explicitly documented** including cascade and soft-delete behavior

## Non-Goals (Out of Scope)

1. **Will NOT change the overall DDD architecture** or bounded context structure
2. **Will NOT modify the AWS Lambda deployment model** or address cold start issues
3. **Will NOT change the database schema significantly** (only minor adjustments for mapping)
4. **Will NOT introduce new major dependencies** without explicit discussion
5. **Will NOT implement event sourcing** or other architectural patterns not currently in use
6. **Will NOT change the async/await patterns** currently implemented

## Design Considerations

### Mapping Strategy
- Consider using a library like `cattrs` more extensively for structured conversions
- Implement a `Mapper` protocol that each bounded context can customize
- Use type annotations and runtime validation to catch mapping issues early

### Repository Pattern
- Keep the generic repository for complex queries but provide simpler alternatives
- Consider implementing a query builder pattern for better debugging
- Use SQLAlchemy 2.0's new features for better async support

### Testing Infrastructure
- Leverage `pytest-asyncio` more effectively with proper fixture scopes
- Consider using `factory_boy` or similar for test data generation
- Implement a clear layer-based testing strategy

## Technical Considerations

1. **Maintain Python 3.11+ compatibility** for all refactoring
2. **Preserve SQLAlchemy 2.0+ async patterns** while simplifying session handling
3. **Ensure Pydantic v2 features are used** for better performance
4. **Keep PostgreSQL-specific features** (pg_trgm, etc.) for advanced queries
5. **Document breaking changes** in domain models for frontend coordination
6. **Create migration scripts** for any data structure changes

## Success Metrics

1. **Reduction in mapping-related bugs**: Track bugs labeled as "mapping" or "type-error" - target 80% reduction
2. **Development velocity**: Measure time to implement new features - target 40% improvement
3. **Test execution time**: Maintain or improve current test suite performance
4. **Code complexity metrics**: Reduce average entity size by 50%
5. **Developer satisfaction**: Conduct before/after survey on code maintainability

## Open Questions

1. **Mapping Library Choice**: Should we adopt a more comprehensive mapping library like `marshmallow-sqlalchemy` or build on existing `cattrs` usage?
2. **Repository Interface**: What specific query patterns are most important for the AI/RAG features planned?
3. **Breaking Changes**: Are there specific API contracts with the frontend that must be preserved despite internal refactoring?
4. **Performance Requirements**: Are there specific performance benchmarks the refactored code must meet?
5. **Soft Delete Strategy**: Should we implement a global soft-delete filter or keep it explicit in queries?
6. **Testing Coverage Target**: What test coverage percentage should we aim for after refactoring?