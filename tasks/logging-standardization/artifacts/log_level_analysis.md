# Log Level Consistency Analysis

## Current Log Level Usage Patterns

### Analyzed Files (Migrated to StructlogFactory)
1. `src/contexts/client_onboarding/core/services/command_handlers/process_webhook.py`
2. `src/contexts/client_onboarding/core/services/client_identifier_extractor.py`
3. `src/contexts/client_onboarding/core/services/integrations/typeform/client.py`
4. `src/contexts/client_onboarding/core/services/webhooks/processor.py`
5. `src/contexts/client_onboarding/core/services/webhooks/manager.py`
6. `src/contexts/shared_kernel/services/messagebus.py`
7. `src/contexts/products_catalog/core/adapters/ORM/mappers/product_mapper.py`
8. `src/contexts/products_catalog/core/services/command_handlers/classification/category/create.py`
9. `src/contexts/products_catalog/core/services/command_handlers/classification/brand/create.py`
10. `src/contexts/products_catalog/core/services/command_handlers/products/update_product.py`
11. `src/contexts/recipes_catalog/core/services/client/form_response_preview.py`
12. `src/contexts/recipes_catalog/core/services/client/form_response_transfer.py`

## Log Level Standards (Target Pattern)

### DEBUG
- **Purpose**: Detailed flow information for debugging
- **Use Cases**: 
  - Step-by-step process tracking
  - Internal state changes
  - Rate limiting enforcement
  - Security operations (non-critical)
  - Detailed parsing/validation steps

### INFO  
- **Purpose**: Business events and normal operations
- **Use Cases**:
  - Business operation start/completion
  - Successful processing milestones
  - Configuration changes
  - External API calls (successful)
  - Resource creation/updates

### WARNING
- **Purpose**: Recoverable issues that need attention
- **Use Cases**:
  - Rate limit warnings (not violations)
  - Retry operations
  - Fallback mechanisms activated
  - Configuration issues (non-fatal)
  - Security warnings (non-critical)

### ERROR
- **Purpose**: Failures that prevent operation completion
- **Use Cases**:
  - Processing failures
  - External API failures
  - Validation errors
  - Database operation failures
  - Security violations

## Current Issues Identified

### 1. Inconsistent Business Event Logging
- Some business operations use DEBUG instead of INFO
- Inconsistent granularity for business milestones

### 2. Warning vs Error Classification
- Some recoverable issues logged as ERROR
- Some warnings that should be INFO

### 3. Debug Level Overuse
- Some important business events logged as DEBUG
- Makes filtering difficult for production monitoring

## Standardization Plan

### Phase 1: Business Event Standardization
- Ensure all business operations (start/success) use INFO
- Move detailed flow tracking to DEBUG

### Phase 2: Error Classification
- Ensure all failures use ERROR with exc_info=True
- Move recoverable issues to WARNING

### Phase 3: Debug Optimization
- Keep only essential debugging information at DEBUG level
- Remove verbose debugging that impacts performance

### Phase 4: Warning Refinement
- Ensure WARNING is used for attention-worthy but non-fatal issues
- Move informational warnings to INFO
