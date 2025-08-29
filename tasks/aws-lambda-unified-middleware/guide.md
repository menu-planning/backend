# Implementation Guide: AWS Lambda Unified Middleware

---
feature: aws-lambda-unified-middleware
complexity: standard
risk_level: high
estimated_time: 7-10 weeks
phases: 4
---

## Overview
Consolidate all middleware patterns into a unified, composable system within `shared_kernel`, establish consistent patterns for authentication, error handling, and logging, and migrate all existing Lambda functions to use the unified middleware stack.

## Architecture
Simple middleware composition pattern using decorators and base classes. Each middleware component handles one concern (auth, logging, error handling) and can be composed together. Configuration is centralized but simple.

**Key Features:**
- **Timeout Management**: Built-in timeout handling using anyio cancel scopes
- **Exception Groups**: Proper exception handling with cancellation propagation
- **Cancel Scopes**: Leverages anyio's powerful cancellation mechanisms
- **FastAPI Ready**: Designed to work with both AWS Lambda and FastAPI

## Files to Modify/Create
### Core Files ✅ COMPLETED
- `src/contexts/shared_kernel/middleware/core/base_middleware.py` - Base middleware class with timeout support ✅
- `src/contexts/shared_kernel/middleware/core/middleware_composer.py` - Composition logic with cancel scopes ✅

### Remaining Files
- `src/contexts/shared_kernel/middleware/auth/authentication.py` - Unified auth (NEW)
- `src/contexts/shared_kernel/middleware/error_handling/exception_handler.py` - Error handling (NEW)
- `src/contexts/shared_kernel/middleware/logging/structured_logger.py` - Unified logging (NEW)
- `src/contexts/shared_kernel/middleware/decorators/lambda_handler.py` - Main decorator (NEW)

### Migration Files
- Update all Lambda handlers in `client_onboarding`, `products_catalog`, `recipes_catalog` contexts
- Remove duplicate middleware implementations from individual contexts

## Phase Overview
1. **Phase 1**: Core Infrastructure ✅ COMPLETED
   - Base middleware architecture with timeout support
   - Middleware composer with cancel scope handling
2. **Phase 2**: Middleware Implementation
   - Authentication, error handling, and logging middleware
3. **Phase 3**: Migration and Testing
   - Migrate all Lambda functions to unified middleware
4. **Phase 4**: Cleanup and Optimization
   - Remove duplicates, optimize performance, prepare for FastAPI

## Testing Strategy
- Commands: `uv run python pytest tests/contexts/shared_kernel/middleware/`
- Coverage target: 90%
- Focus on integration tests for middleware composition
- **New**: Test timeout handling and cancel scope behavior

## Phase Dependencies
1. Core infrastructure ✅ → 2. Middleware implementation → 3. Migration → 4. Cleanup
- Each phase builds on the previous
- Migration can be done incrementally by context

## Risk Mitigation
- Comprehensive testing before migration
- Gradual rollout by context
- Rollback plan for each phase
- Performance monitoring throughout
- **New**: Test timeout scenarios and cancellation behavior

## Success Criteria
1. Zero duplicate middleware implementations across all contexts
2. All Lambda functions use unified middleware stack
3. Performance overhead <5ms per request
4. 90%+ test coverage for middleware components
5. **New**: Proper timeout handling with anyio cancel scopes ✅
6. **New**: FastAPI compatibility for future deployments 