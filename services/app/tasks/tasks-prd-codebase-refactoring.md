## Relevant Files

### Mapping Infrastructure (API Schema Bridge Pattern)
- `src/contexts/seedwork/shared/adapters/mapper.py` - Current mapping registry implementation to enhance ✅ (enhanced with EnhancedModelMapper)
- `src/contexts/seedwork/shared/adapters/mapping_utils.py` - Utilities for validation and error handling ✅ (created)
- `src/contexts/seedwork/shared/adapters/mapping_decorators.py` - Type validation decorators ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/base_api_schema.py` - Base classes for API schemas ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/validators.py` - Reusable validators using Pydantic built-ins ✅ (improved)
- `src/contexts/seedwork/shared/adapters/api_schemas/README.md` - Comprehensive guide for API schema patterns ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/REFACTORING_GUIDE.md` - Step-by-step refactoring guide ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/example_refactoring.py` - Before/after examples ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/example_improved.py` - Best practices using Pydantic built-ins ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/refactor_schemas.py` - Analysis script for existing schemas ✅ (created)
- `src/contexts/seedwork/shared/adapters/mapping_utils_improved.py` - Domain mapping utilities (Pydantic-focused) ✅ (created)
- `src/contexts/seedwork/shared/adapters/api_schemas/IMPROVEMENTS_SUMMARY.md` - Summary of Pydantic improvements ✅ (created)
- `API_SCHEMA_REFACTORING_REPORT.md` - Analysis report of current API schemas ✅ (generated)
- `src/contexts/products_catalog/core/adapters/api_schemas/value_objects/score_refactored.py` - Example refactored API schema ✅ (improved)
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/classifications/base_class_refactored.py` - Example refactored classification ✅ (created)
- `src/contexts/seedwork/shared/exceptions.py` - Enhanced mapping exception types
- `src/contexts/recipes_catalog/core/adapters/ARCHITECTURE_GUIDE.md` - API schema bridge pattern guide ✅ (created)

### ORM Mappers (Database Layer)
- `src/contexts/products_catalog/core/adapters/ORM/mappers/product.py` - Complex product mapper (enhance existing)
- `src/contexts/products_catalog/core/adapters/ORM/mappers/brand.py` - Simple reference mapper (enhance existing)
- `src/contexts/products_catalog/core/adapters/ORM/mappers/source.py` - Simple reference mapper (enhance existing)
- `src/contexts/products_catalog/core/adapters/ORM/mappers/score.py` - Composite value object mapper (enhance existing)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/recipe/recipe.py` - Complex mapper with nested relationships (enhance existing)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/meal/meal.py` - Mapper with tag deduplication (enhance existing)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/meal/enhanced_meal_mapper.py` - Example enhanced mapper (created)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/meal/meal_mapper_with_api_bridge.py` - Example hybrid mapper (created)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/menu/menu.py` - Aggregate mapper with parent context (enhance existing)
- `src/contexts/recipes_catalog/core/adapters/ORM/mappers/client/client.py` - Client mapper with composite fields (enhance existing)

### API Schemas (Validation Layer) - To Refactor

#### Products Catalog API Schemas
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/product.py` - ApiProduct schema
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/product_filter.py` - Product filter schema
- `src/contexts/products_catalog/core/adapters/api_schemas/entities/classifications/` - Classification schemas:
  - `brand.py` - ApiBrand schema
  - `category.py` - ApiCategory schema  
  - `food_group.py` - ApiFoodGroup schema
  - `parent_category.py` - ApiParentCategory schema
  - `process_type.py` - ApiProcessType schema
  - `source.py` - ApiSource schema
- `src/contexts/products_catalog/core/adapters/api_schemas/value_objects/` - Product value objects:
  - `if_food_votes.py` - Food votes schema
  - `score.py` - Product score schema
- `src/contexts/products_catalog/core/adapters/api_schemas/commands/` - Command schemas

#### Recipes Catalog API Schemas  
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/meal/meal.py` - ApiMeal schema
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/recipe/recipe.py` - ApiRecipe schema
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/menu/menu.py` - ApiMenu schema
- `src/contexts/recipes_catalog/core/adapters/api_schemas/entities/client/client.py` - ApiClient schema
- `src/contexts/recipes_catalog/core/adapters/api_schemas/value_objects/` - Recipe value objects:
  - `ingredient.py` - Ingredient schema
  - `menu_meal.py` - MenuMeal schema
  - `rating.py` - Rating schema

#### IAM API Schemas
- `src/contexts/iam/core/adapters/api_schemas/entities/user.py` - ApiUser schema
- `src/contexts/iam/core/adapters/api_schemas/value_objects/role.py` - Role schema
- `src/contexts/iam/core/adapters/api_schemas/commands/` - IAM command schemas

#### Shared Kernel API Schemas
- `src/contexts/shared_kernel/adapters/api_schemas/value_objects/` - Shared value objects:
  - `address.py` - Address schema
  - `amount.py` - Amount schema
  - `contact_info.py` - Contact info schema
  - `nutri_facts.py` - Nutrition facts schema
  - `nutri_value.py` - Nutrition value schema
  - `profile.py` - Profile schema
  - `tag/tag.py` - Tag schema
  - `tag/tag_filter.py` - Tag filter schema

#### Seedwork API Schemas
- `src/contexts/seedwork/shared/adapters/api_schemas/value_ojbects/` - Base value objects:
  - `role.py` - Base role schema
  - `user.py` - Base user schema

### Repository Pattern
- `src/contexts/seedwork/shared/adapters/repository.py` - Base repository to simplify
- `src/contexts/products_catalog/core/adapters/repositories/product.py` - Product repository
- `src/contexts/recipes_catalog/core/adapters/repositories/recipe/recipe.py` - Recipe repository
- `src/contexts/recipes_catalog/core/adapters/repositories/meal/meal.py` - Meal repository
- `tests/products_catalog/integration/test_repository.py` - Repository tests
- `tests/recipes_catalog/integration/recipe/test_repo.py` - Recipe repository tests

### Testing Infrastructure
- `conftest.py` - Root-level test configuration to create
- `tests/conftest.py` - Existing test config to refactor
- `tests/seedwork/conftest.py` - Seedwork-specific fixtures
- `tests/products_catalog/integration/conftest.py` - Context-specific fixtures
- `tests/recipes_catalog/integration/conftest.py` - Context-specific fixtures
- `tests/utils.py` - Test utilities to consolidate

### Entity Refactoring
- `src/contexts/products_catalog/core/domain/entities/product.py` - Large product entity
- `src/contexts/recipes_catalog/core/domain/entities/recipe.py` - Complex recipe entity
- `src/contexts/recipes_catalog/core/domain/entities/meal.py` - Meal entity with relationships
- `src/contexts/recipes_catalog/core/domain/entities/menu.py` - Menu aggregate

### Notes

- **APPROACH**: API Schema Bridge Pattern - Using Pydantic schemas as validation bridge between JSON and domain models
- Architecture: JSON → API Schema (validation) → Domain Model → ORM Mapper (persistence) → Database
- Clear separation of concerns: API schemas in `api_schemas/`, ORM mappers in `ORM/mappers/`
- Existing mappers will be enhanced with utilities, not rewritten from scratch
- API schemas handle JSON validation and serialization; ORM mappers handle database persistence
- Hybrid approach for complex entities: Pydantic for validation, manual mapping for relationships
- Unit tests are placed in the `tests/` directory mirroring the `src/` structure
- Use `pytest` to run tests (e.g., `pytest tests/` or `pytest tests/specific/test_file.py`)
- Additional relevant files will be identified during implementation of each phase

## Tasks

- [ ] 1.0 Implement API Schema Bridge Pattern for Clean Architecture
  - [x] 1.1 Create mapping utilities module with common helper functions
    - Safe type conversions (UUID, datetime, enum, float, int)
    - Null/None handling utilities
    - Collection conversions (set, list)
    - Field path tracking for detailed error messages
  - [x] 1.2 Create mapping decorators for validation and error handling
    - Input validation decorator
    - Error logging decorator
    - Domain object validation decorator
    - Exception handling decorator
  - [x] 1.3 Create enhanced base mapper class (EnhancedModelMapper)
    - Built-in logging and error handling
    - Common mapping patterns
    - Relationship handling utilities
  - [x] 1.4 Refactor existing API schemas to follow consistent patterns
    - Add comprehensive field validators
    - Implement from_domain() and to_domain() methods
    - Add proper type hints and documentation
    - Ensure proper handling of optional fields
  - [ ] 1.5 Refactor Products Catalog API schemas (31 schemas)
    - [ ] 1.5.1 Refactor value object schemas (2 schemas):
      - `ApiIsFoodVotes` in value_objects/if_food_votes.py
      - `ApiScore` in value_objects/score.py (use existing refactored version as template)
    - [ ] 1.5.2 Refactor entity schemas (15 schemas):
      - `ApiProduct` in entities/product.py
      - `ApiProductFilter` in entities/product_filter.py
      - Classification schemas in entities/classifications/: `ApiBrand`, `ApiCategory`, `ApiFoodGroup`, `ApiParentCategory`, `ApiProcessType`, `ApiSource` (inherit from refactored base)
    - [ ] 1.5.3 Refactor command schemas (14 schemas):
      - Product commands: `ApiAddFoodProduct`, `ApiAddHouseInputAndCreateProductIfNeeded`, `ApiAddProductImage`, etc.
      - Classification commands: `ApiCreateClassification`, `ApiUpdateClassification`, etc.
  - [ ] 1.6 Refactor Recipes Catalog API schemas (35 schemas)
    - [ ] 1.6.1 Refactor value object schemas (4 schemas):
      - `ApiIngredient` in value_objects/ingredient.py
      - `ApiMenuMeal` in value_objects/menu_meal.py
      - `ApiRating` in value_objects/rating.py
      - `ApiUser` in value_objects/user.py
    - [ ] 1.6.2 Refactor entity schemas (16 schemas):
      - `ApiMeal` in entities/meal/meal.py
      - `ApiRecipe` in entities/recipe/recipe.py
      - `ApiMenu` in entities/menu/menu.py
      - `ApiClient` in entities/client/client.py
      - Tag-related schemas, etc.
    - [ ] 1.6.3 Refactor command schemas (15 schemas):
      - Meal commands: `ApiCopyMeal`, `ApiCreateMeal`, `ApiDeleteMeal`, `ApiUpdateMeal`
      - Recipe commands: `ApiCopyRecipe`, `ApiCreateRecipe`, `ApiDeleteRecipe`, `ApiUpdateRecipe`, `ApiRateRecipe`
      - Menu commands: `ApiCreateMenu`, `ApiDeleteMenu`, `ApiUpdateMenu`
      - Client commands: `ApiCreateClient`, `ApiDeleteClient`, `ApiUpdateClient`
  - [ ] 1.7 Refactor IAM API schemas (8 schemas)
    - [ ] 1.7.1 Refactor entity schemas:
      - `ApiUser` in entities/user.py
    - [ ] 1.7.2 Refactor value object schemas:
      - `ApiRole` in value_objects/role.py
    - [ ] 1.7.3 Refactor command schemas (6 schemas):
      - `ApiAssignRoleToUser`, `ApiCreateUser`, `ApiRemoveRoleFromUser`, etc.
  - [ ] 1.8 Refactor Shared Kernel API schemas (9 schemas)
    - [ ] 1.8.1 Refactor value object schemas:
      - `ApiAddress` in value_objects/address.py
      - `ApiAmount` in value_objects/amount.py
      - `ApiContactInfo` in value_objects/contact_info.py
      - `ApiNutriFacts` in value_objects/nutri_facts.py
      - `ApiNutriValue` in value_objects/nutri_value.py
      - `ApiProfile` in value_objects/profile.py
      - `ApiTag` in value_objects/tag/tag.py
      - `ApiTagFilter` in value_objects/tag/tag_filter.py
  - [ ] 1.9 Refactor Seedwork API schemas (3 schemas)
    - [ ] 1.9.1 Refactor base value object schemas:
      - `ApiSeedRole` in value_objects/role.py
      - `ApiSeedUser` in value_objects/user.py
  - [ ] 1.10 Create SQLAlchemy merge strategy helpers
    - Safe entity merging with integrity error handling
    - Soft-delete relationship management
    - Version conflict resolution
  - [ ] 1.11 Implement hybrid mapper examples for complex entities
    - MealMapper with API schema validation
    - RecipeMapper with nested relationship handling
    - ProductMapper with classification management
  - [ ] 1.12 Document the API schema bridge pattern
    - Architecture guide with diagrams
    - Best practices and anti-patterns
    - Migration guide for existing code
  - [ ] 1.13 Create comprehensive tests for mapping infrastructure
    - Unit tests for utilities and decorators
    - Integration tests for mappers
    - End-to-end tests for complete flow
  - [ ] 1.14 Establish clear boundaries between layers
    - API schemas handle JSON ↔ Domain conversion
    - ORM mappers handle Domain ↔ Database conversion
    - Domain models remain pure business logic

- [ ] 2.0 Simplify Repository Pattern
  - [ ] 2.1 Design two-tier repository interface (SimpleCRUD and AdvancedQuery)
  - [ ] 2.2 Implement SimpleCRUD base repository with basic CRUD operations
  - [ ] 2.3 Create AdvancedQuery repository for Products with existing filters
  - [ ] 2.4 Create AdvancedQuery repository for Recipes with search capabilities
  - [ ] 2.5 Create AdvancedQuery repository for Meals with menu relationships
  - [ ] 2.6 Add SQL query debugging hooks with formatted output
  - [ ] 2.7 Implement async session management in base repository
  - [ ] 2.8 Add explicit soft-delete methods (include/exclude/only_deleted)
  - [ ] 2.9 Create extensible query interface for future AI/RAG features
  - [ ] 2.10 Write integration tests for each repository implementation

- [ ] 3.0 Establish Testing Infrastructure
  - [ ] 3.1 Create root-level conftest.py with shared async fixtures
  - [ ] 3.2 Implement automatic async SQLAlchemy session handling in fixtures
  - [ ] 3.3 Create test factories for domain entities using factory pattern
  - [ ] 3.4 Create test factories for value objects with valid defaults
  - [ ] 3.5 Implement transaction rollback pattern for test isolation
  - [ ] 3.6 Consolidate duplicate fixtures from context-specific conftest files
  - [ ] 3.7 Create layer-specific testing patterns (domain, application, infrastructure)
  - [ ] 3.8 Write testing guidelines documentation
  - [ ] 3.9 Refactor existing tests to use new infrastructure
  - [ ] 3.10 Add pytest markers for test categorization (unit, integration, e2e)

- [ ] 4.0 Refactor Large Entities
  - [ ] 4.1 Analyze Product entity and identify aggregate boundaries
  - [ ] 4.2 Extract Product business logic into domain services
  - [ ] 4.3 Refactor Recipe entity to reduce methods to max 10
  - [ ] 4.4 Split Meal entity relationships into separate aggregates
  - [ ] 4.5 Refactor Menu aggregate for clearer boundaries
  - [ ] 4.6 Document entity relationships with cascade/soft-delete behavior
  - [ ] 4.7 Create value objects for complex entity properties
  - [ ] 4.8 Write unit tests for refactored entities
  - [ ] 4.9 Update command handlers for new entity structure
  - [ ] 4.10 Ensure backward compatibility or create migration plan

- [ ] 5.0 Documentation and Migration
  - [ ] 5.1 Document breaking changes in domain models for frontend
  - [ ] 5.2 Create migration scripts for any data structure changes
  - [ ] 5.3 Write architectural decision records (ADRs) for major changes
  - [ ] 5.4 Update developer documentation with new patterns
  - [ ] 5.5 Create code examples for common mapping scenarios
  - [ ] 5.6 Document repository usage patterns and best practices
  - [ ] 5.7 Create troubleshooting guide for common mapping errors
  - [ ] 5.8 Set up code complexity metrics monitoring
  - [ ] 5.9 Conduct developer training session on new patterns
  - [ ] 5.10 Create post-refactoring survey for developer feedback