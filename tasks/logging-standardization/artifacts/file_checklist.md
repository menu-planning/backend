# File-by-File Migration Checklist

## Migration Status Legend
- ⏳ **PENDING** - Not started
- 🔄 **IN_PROGRESS** - Migration in progress
- ✅ **COMPLETED** - Migration completed and validated
- ⚠️ **NEEDS_REVIEW** - Requires special attention
- 🔒 **ALREADY_STRUCTURED** - Already using structured logging

## Priority Classification
- **P1** - Easy migration (standard logger calls)
- **P2** - Moderate complexity (private loggers, class-based)
- **P3** - High complexity (already structured, needs review)
- **P4** - Critical path (high-volume logging)

---

## Priority 1: Easy Migration (Standard Logger Calls)

### Client Onboarding Context

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/client_onboarding/aws_lambda/shared/query_executor.py` | ⏳ | 1 | P1 | Simple logging call |
| `src/contexts/client_onboarding/core/endpoints/internal/get_form_response.py` | ⏳ | 6 | P1 | Standard endpoint logging |
| `src/contexts/client_onboarding/core/endpoints/internal/get_form_responses.py` | ⏳ | 3 | P1 | Standard endpoint logging |
| `src/contexts/client_onboarding/core/services/command_handlers/delete_onboarding_form.py` | ⏳ | 1 | P1 | Simple command handler |
| `src/contexts/client_onboarding/core/services/command_handlers/process_webhook.py` | ⏳ | 1 | P1 | Simple command handler |
| `src/contexts/client_onboarding/core/services/command_handlers/setup_onboarding_form.py` | ⏳ | 1 | P1 | Simple command handler |
| `src/contexts/client_onboarding/core/services/command_handlers/update_webhook_url.py` | ⏳ | 2 | P1 | Standard command handler |

### IAM Context

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/iam/aws_lambda/assign_role.py` | ⏳ | 1 | P1 | Simple Lambda function |
| `src/contexts/iam/aws_lambda/create_user.py` | ⏳ | 4 | P1 | Standard Lambda logging |
| `src/contexts/iam/core/endpoints/internal/get.py` | ⏳ | 5 | P1 | Internal endpoint |
| `src/contexts/iam/core/services/command_handlers.py` | ⏳ | 1 | P1 | Simple command handler |

### Products Catalog Context

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/products_catalog/aws_lambda/fetch_product.py` | ⏳ | 1 | P1 | Simple Lambda function |
| `src/contexts/products_catalog/aws_lambda/fetch_product_source_name.py` | ⏳ | 1 | P1 | Simple Lambda function |
| `src/contexts/products_catalog/core/adapters/api_schemas/root_aggregate/api_product.py` | ⏳ | 1 | P1 | Schema adapter |
| `src/contexts/products_catalog/core/adapters/ORM/mappers/product_mapper.py` | ⏳ | 1 | P1 | ORM mapper |
| `src/contexts/products_catalog/core/adapters/repositories/product_repository.py` | ⏳ | 1 | P1 | Repository class |

### Recipes Catalog Context

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/recipes_catalog/core/domain/rules.py` | ⏳ | 6 | P1 | Domain rules validation |

### Seedwork Shared

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/seedwork/shared/adapters/exceptions/api_schema.py` | ⏳ | 1 | P1 | Exception handling |
| `src/contexts/seedwork/shared/adapters/repositories/sa_generic_repository.py` | ⏳ | 1 | P1 | Generic repository |
| `src/contexts/seedwork/shared/utils.py` | ⏳ | 1 | P1 | Utility functions |

### Shared Kernel

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/shared_kernel/services/messagebus.py` | ⏳ | 1 | P1 | Message bus service |

---

## Priority 2: Moderate Complexity (Private Loggers)

### Client Onboarding Context

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/client_onboarding/core/adapters/security/webhook_signature_validator.py` | ⏳ | 4 | P2 | Uses `self._logger` |
| `src/contexts/client_onboarding/core/adapters/validators/ownership_validator.py` | ⏳ | 7 | P2 | Uses `self._logger` |
| `src/contexts/client_onboarding/core/services/client_identifier_extractor.py` | ⏳ | 3 | P2 | Uses `self._logger` |

### Seedwork Shared

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/seedwork/shared/adapters/internal_providers/base_iam_provider.py` | ⏳ | 5 | P2 | Base provider class |
| `src/contexts/seedwork/shared/domain/entity.py` | ⏳ | 3 | P2 | Domain entity base |

---

## Priority 3: Already Structured (Review Required)

### Shared Kernel Middleware

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/shared_kernel/middleware/auth/authentication.py` | 🔒 | 3 | P3 | Uses structured_logger |
| `src/contexts/shared_kernel/middleware/error_handling/exception_handler.py` | 🔒 | 2 | P3 | Uses structured_logger |
| `src/contexts/shared_kernel/middleware/logging/structured_logger.py` | 🔒 | 3 | P3 | Core structured logging |

### Seedwork Repository

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/seedwork/shared/adapters/repositories/repository_logger.py` | 🔒 | 7 | P3 | Custom repository logger |

### Core Logging

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/logging/logger.py` | 🔒 | 1 | P3 | Core logging infrastructure |

---

## Priority 4: High-Volume Logging (Critical Path)

### Client Onboarding Services

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/client_onboarding/core/services/integrations/typeform/client.py` | ⚠️ | 39 | P4 | **HIGHEST VOLUME** - TypeForm integration |
| `src/contexts/client_onboarding/core/services/webhooks/manager.py` | ⚠️ | 38 | P4 | **HIGH VOLUME** - Webhook management |
| `src/contexts/client_onboarding/core/services/webhooks/security.py` | ⚠️ | 17 | P4 | Security validation logging |
| `src/contexts/client_onboarding/core/services/webhooks/processor.py` | ⚠️ | 10 | P4 | Webhook processing |

### Configuration

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/client_onboarding/config.py` | ⚠️ | 6 | P4 | Configuration validation |

---

## AWS Lambda Functions (Correlation ID Ready)

### Client Onboarding Lambda Functions
*All have correlation ID generation - Ready for structured logging*

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/client_onboarding/aws_lambda/bulk_query_responses.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/client_onboarding/aws_lambda/create_form.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/client_onboarding/aws_lambda/delete_form.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/client_onboarding/aws_lambda/query_responses.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/client_onboarding/aws_lambda/update_form.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/client_onboarding/aws_lambda/webhook_processor.py` | ⏳ | 0 | P1 | Correlation ID ready |

### Products Catalog Lambda Functions

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/products_catalog/aws_lambda/create_product.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/products_catalog/aws_lambda/get_product_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/products_catalog/aws_lambda/get_product_source_name_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/products_catalog/aws_lambda/search_product_similar_name.py` | ⏳ | 0 | P1 | Correlation ID ready |

### Recipes Catalog Lambda Functions (63 total)

| File | Status | Calls | Priority | Notes |
|------|--------|-------|----------|-------|
| `src/contexts/recipes_catalog/aws_lambda/client/create_client.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/create_menu.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/delete_client.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/delete_menu.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/fetch_client.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/get_client_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/update_client.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/client/update_menu.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/copy_meal.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/create_meal.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/delete_meal.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/fetch_meal.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/get_meal_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/meal/update_meal.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/copy_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/create_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/delete_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/fetch_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/get_recipe_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/rate_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/recipe/update_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/shopping_list/fetch_recipe.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/tag/fetch_tag.py` | ⏳ | 0 | P1 | Correlation ID ready |
| `src/contexts/recipes_catalog/aws_lambda/tag/get_tag_by_id.py` | ⏳ | 0 | P1 | Correlation ID ready |

---

## Migration Statistics

### By Priority
- **P1 (Easy)**: 95 files
- **P2 (Moderate)**: 5 files  
- **P3 (Structured)**: 5 files
- **P4 (High-Volume)**: 4 files

### By Context
- **client_onboarding**: 21 files
- **recipes_catalog**: 25 files (including 24 Lambda functions)
- **products_catalog**: 10 files (including 6 Lambda functions)
- **iam**: 4 files
- **seedwork**: 7 files
- **shared_kernel**: 4 files
- **logging**: 1 file

### By Logging Volume
- **High Volume (10+ calls)**: 4 files
- **Medium Volume (5-9 calls)**: 6 files
- **Low Volume (1-4 calls)**: 38 files
- **No Direct Calls**: 77 files (Lambda functions with correlation ID)

---

## Migration Phases

### Phase 2.1: Quick Wins (P1 Easy Migration)
**Target**: 30 files with lowest complexity
- All single-call files
- Simple endpoint and command handlers
- Lambda functions with correlation ID ready

### Phase 2.2: Standard Migration (P1 Continued)
**Target**: Remaining P1 files
- Multi-call standard logging files
- Repository and adapter classes
- Domain logic files

### Phase 2.3: Moderate Complexity (P2)
**Target**: 5 files with private loggers
- Refactor class-based logging
- Update dependency injection
- Maintain existing patterns

### Phase 2.4: High-Volume Optimization (P4)
**Target**: 4 critical path files
- Implement performance optimizations
- Consider async logging
- Monitor performance impact

### Phase 2.5: Structured Review (P3)
**Target**: 5 already structured files
- Verify format consistency
- Standardize structured patterns
- Update documentation

---

## Validation Checklist

For each migrated file:
- [ ] Import statements updated
- [ ] Logger instantiation migrated
- [ ] All logging calls converted
- [ ] Correlation ID preserved
- [ ] Performance impact measured
- [ ] Security review completed
- [ ] Tests passing
- [ ] Documentation updated

---

## Risk Mitigation

### High-Volume Files (P4)
- Implement performance monitoring
- Consider feature flags for rollback
- Use async logging where possible
- Monitor memory usage

### Private Logger Files (P2)
- Maintain existing architecture patterns
- Update dependency injection carefully
- Preserve class encapsulation
- Test thoroughly

### Already Structured Files (P3)
- Verify compatibility with new standards
- Maintain existing functionality
- Update only if necessary
- Document any changes
