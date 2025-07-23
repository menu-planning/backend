# Phase 3: Recipes Catalog & IAM Migration

---
phase: 3
depends_on: [phase_1, phase_2]
estimated_time: 50 hours
risk_level: high
---

## Objective
Complete migration of recipes_catalog and iam endpoints using patterns validated in Phase 2, with special attention to IAM's unique authorization requirements and recipes' domain-specific logic.

## Prerequisites
- [x] Phase 1 schema foundation completed - see `artifacts/phase_1_schema_foundation_report.md`
- [x] IAM-specific error schemas ready: `AuthenticationErrorResponse`, `AuthorizationErrorResponse`
- [x] Recipe collection patterns ready: `CollectionResponse[ApiRecipe]` with TypeAdapter support
- [ ] Phase 2 completed with products_catalog successfully migrated
- [ ] Feature flag system tested and working
- [ ] Migration lessons learned documented
- [ ] Performance impact validated as acceptable

## Phase 1 Integration Points for IAM & Recipes
- **IAM Error Compatibility**: Use `create_message_error()` for current `{"message": "error text"}` pattern
- **IAM Authorization**: `AuthorizationErrorResponse` for permission failures
- **IAM Authentication**: `AuthenticationErrorResponse` for credential failures  
- **Recipe Collections**: `CollectionResponse[ApiRecipe]` works with existing `RecipeListAdapter`
- **Cross-Context**: Error schemas standardize responses across all three contexts

# Tasks

## 3.1 Recipes Catalog Migration
- [ ] 3.1.1 Analyze recipes-specific patterns
  - Files: `src/contexts/recipes_catalog/aws_lambda/*.py`
  - Purpose: Identify unique patterns not covered in products migration
- [ ] 3.1.2 Migrate recipes GET endpoints
  - Files: `src/contexts/recipes_catalog/aws_lambda/` (read operations)
  - Purpose: Apply validated migration patterns to recipes context
- [ ] 3.1.3 Migrate recipes collection endpoints
  - Purpose: Apply TypeAdapter patterns to recipes search/list operations
- [ ] 3.1.4 Migrate recipes POST/PUT endpoints
  - Files: `src/contexts/recipes_catalog/aws_lambda/` (write operations)
  - Purpose: Handle recipe creation/update with consistent patterns

## 3.2 IAM Context Migration
- [ ] 3.2.1 Analyze IAM authorization specifics
  - Files: `src/contexts/iam/aws_lambda/*.py`
  - Purpose: Understand self-service vs admin permission patterns
- [ ] 3.2.2 Customize auth middleware for IAM
  - Files: `src/contexts/shared_kernel/middleware/auth_middleware.py`
  - Purpose: Add IAM-specific permission checking capabilities
- [ ] 3.2.3 Migrate IAM user management endpoints
  - Files: `src/contexts/iam/aws_lambda/user_*.py`
  - Purpose: Apply patterns to user creation, update, deletion
- [ ] 3.2.4 Migrate IAM permission management endpoints
  - Files: `src/contexts/iam/aws_lambda/permission_*.py`
  - Purpose: Handle complex permission scenarios

## 3.3 Cross-Context Validation
- [ ] 3.3.1 Test auth middleware across all contexts
  - Files: `tests/integration/cross_context/test_auth.py`
  - Purpose: Ensure auth works consistently across products, recipes, iam
- [ ] 3.3.2 Validate logging correlation across contexts
  - Purpose: Ensure correlation IDs work for cross-context operations
- [ ] 3.3.3 Test error handling consistency
  - Files: `tests/integration/cross_context/test_errors.py`
  - Purpose: Verify error responses consistent across all contexts

## 3.4 Advanced Scenarios
- [ ] 3.4.1 Handle complex recipes operations
  - Purpose: Recipe sharing, versioning, complex search queries
- [ ] 3.4.2 Handle IAM edge cases
  - Purpose: Self-permission modification, admin overrides, cascading deletes
- [ ] 3.4.3 Test concurrent operations
  - Files: `tests/integration/test_concurrency.py`
  - Purpose: Ensure thread safety and correlation ID isolation

## 3.5 Performance & Optimization
- [ ] 3.5.1 Performance test all migrated contexts
  - Purpose: Validate system-wide performance impact
- [ ] 3.5.2 Optimize middleware stack if needed
  - Files: Middleware components in `src/contexts/shared_kernel/middleware/`
  - Purpose: Address any performance bottlenecks discovered
- [ ] 3.5.3 Memory usage analysis
  - Purpose: Ensure no memory leaks from middleware additions

## 3.6 Documentation & Examples
- [ ] 3.6.1 Create endpoint migration guide
  - Files: `docs/endpoint_migration_guide.md`
  - Purpose: Document patterns for future endpoint development
- [ ] 3.6.2 Add code examples for each pattern
  - Files: `docs/examples/`
  - Purpose: Provide copy-paste examples for developers
- [ ] 3.6.3 Update developer onboarding docs
  - Files: `docs/developer_onboarding.md`
  - Purpose: Include new standardized patterns in onboarding

## Validation
- [ ] Tests: `poetry run python pytest tests/contexts/recipes_catalog/` - All recipes tests pass
- [ ] Tests: `poetry run python pytest tests/contexts/iam/` - All IAM tests pass
- [ ] Tests: `poetry run python pytest tests/integration/cross_context/` - Cross-context tests pass
- [ ] Performance: System-wide performance within 5% of original baseline
- [ ] Auth: All permission scenarios working correctly across contexts
- [ ] Logs: Correlation IDs consistent across all contexts
- [ ] Error: Error handling consistent across all endpoint types

## Deliverables
- All recipes_catalog endpoints migrated and tested
- All iam endpoints migrated with enhanced auth support
- Cross-context integration validated
- Performance impact assessment
- Complete developer documentation with examples
- Migration guide for future use 