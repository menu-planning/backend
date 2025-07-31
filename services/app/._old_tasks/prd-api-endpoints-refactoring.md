# PRD: API Endpoints Standardization & Refactoring

---
feature: api-endpoints-refactoring
complexity: standard
created: 2024-12-28
version: 1.0
---

## Overview
**Problem**: Current AWS Lambda endpoints across contexts (recipes_catalog, products_catalog, iam) have inconsistent implementations with varying error handling, body parsing, logging, authorization flows, and response formats, creating maintenance overhead and developer confusion.

**Solution**: Standardize endpoint patterns through lightweight utilities and consistent architectural patterns that work alongside existing infrastructure (@lambda_exception_handler, MessageBus) rather than replacing it.

**Value**: Reduced development time, fewer bugs, easier debugging, improved code maintainability, and a solid foundation for advanced features while keeping the current working architecture.

## Goals & Scope
### Goals
1. Create consistent endpoint utility patterns across all contexts
2. Standardize request parsing and response formatting
3. Maintain existing proven patterns (@lambda_exception_handler, MessageBus timeouts)
4. Establish reusable Lambda event utilities
5. Introduce Pydantic TypeAdapters for collection endpoints
6. Keep simple but extensible for future enhancements

### Out of Scope
1. Domain logic modifications
2. Database schema changes
3. Frontend integration updates
4. Replacing existing working middleware (MessageBus, @lambda_exception_handler)
5. Complex middleware orchestration systems
6. Comprehensive monitoring/alerting systems

## User Stories
### Story 1: Consistent Endpoint Development
**As a** developer **I want** standardized endpoint patterns **So that** I can quickly create new endpoints without researching different implementation approaches across contexts.
- [ ] All endpoints follow the same structural pattern
- [ ] Reusable components for common functionality
- [ ] Clear documentation of patterns

### Story 2: Debugging and Monitoring
**As a** DevOps engineer **I want** consistent logging across all endpoints **So that** I can efficiently debug issues and monitor system health.
- [ ] Unified logging format with correlation IDs
- [ ] Consistent error messages and status codes
- [ ] Structured log data for analysis

### Story 3: Security Consistency
**As a** security-conscious developer **I want** consistent authorization patterns **So that** permissions are enforced uniformly across the system.
- [ ] Reusable authorization components
- [ ] Consistent permission checking
- [ ] Standardized error responses for unauthorized access

## Technical Requirements
### Architecture
```
├── shared_kernel/
│   └── endpoints/
│       └── base_endpoint_handler.py  # LambdaHelpers utilities
├── existing patterns maintained:
│   ├── @lambda_exception_handler     # Exception handling
│   ├── MessageBus                   # Business logic + timeouts  
│   ├── IAMProvider.get()            # Simple auth pattern
│   └── Direct event parsing         # Clear and debuggable
```

### Core Components
1. **LambdaHelpers**: Simple utilities for Lambda event parsing and response formatting
2. **Existing @lambda_exception_handler**: Keep current exception handling
3. **Existing MessageBus**: Keep current timeout and business logic handling
4. **Existing IAMProvider patterns**: Keep simple, explicit auth calls
5. **Pydantic TypeAdapters**: For endpoints returning collections

### Integration Points
- IAMProvider for user authentication (keep existing pattern)
- MessageBus for command/query handling (keep existing pattern)
- UnitOfWork for database operations (keep existing pattern)
- Existing CORS_headers across contexts (keep existing pattern)

## Functional Requirements
1. **FR1: Lambda Utilities Standardization**
   - Consistent helper methods for event parsing
   - Standardized response formatting utilities
   - Keep existing endpoint structure (@lambda_exception_handler + business logic)

2. **FR2: Response Format Consistency**
   - Standardized response formatting utilities
   - Proper HTTP status codes
   - Consistent CORS headers handling

3. **FR3: Request Parsing Consistency**
   - Reusable utilities for path parameters, query parameters, body parsing
   - Consistent user ID extraction
   - Clear, debuggable patterns

4. **FR4: Maintain Existing Patterns**
   - Keep @lambda_exception_handler for exception handling
   - Keep MessageBus for business logic and timeouts
   - Keep direct IAMProvider.get() calls for auth

## Quality Requirements
- **Performance**: No performance degradation from current implementation
- **Security**: Maintain existing security levels with improved consistency
- **Maintainability**: 80% code reuse for common endpoint patterns
- **Extensibility**: Design allows future addition of caching, rate limiting, advanced auth

## Testing Approach
- Unit tests for all shared components
- Integration tests for middleware combinations
- Endpoint tests to verify consistent behavior
- Manual testing for backward compatibility

## Implementation Phases
### Phase 1: Foundation Utilities (Week 1)
- [x] Create LambdaHelpers utility class for event parsing and response formatting
- [ ] Standardize CORS headers handling across contexts
- [ ] Create Pydantic TypeAdapters for collection endpoints
- [ ] Document utility patterns and usage examples

### Phase 2: Endpoint Consistency (Week 1-2)
- [ ] Update products_catalog endpoints to use LambdaHelpers
- [ ] Update recipes_catalog endpoints to use LambdaHelpers  
- [ ] Update iam endpoints to use LambdaHelpers
- [ ] Ensure consistent request parsing patterns
- [ ] Ensure consistent response formatting

### Phase 3: Testing & Documentation (Week 2)
- [ ] Test migrated endpoints for consistency
- [ ] Verify no performance degradation
- [ ] Create developer documentation for LambdaHelpers
- [ ] Backward compatibility verification

## Success Metrics
- All endpoints use standardized patterns (100% coverage)
- Developer onboarding time for new endpoints reduced by 30%
- Consistent error message format across all APIs
- Unified log format enabling efficient debugging
- Zero breaking changes for existing API consumers

## Risks & Mitigation
- **Breaking Changes**: Thorough testing and gradual rollout with feature flags
- **Performance Impact**: Benchmark before/after, optimize middleware if needed
- **Developer Adoption**: Clear documentation and examples, pair programming sessions
- **Future Extensibility**: Over-engineering for MVP - Keep simple, well-documented extension points

## Dependencies
- Existing IAMProvider functionality
- Current MessageBus and UnitOfWork patterns
- Pydantic library for TypeAdapters
- anyio for async handling

## Timeline
- **Phase 1**: 3 days (Foundation Utilities)
- **Phase 2**: 5 days (Endpoint Updates) 
- **Phase 3**: 2 days (Testing & Docs)
- **Total**: 10 days

## Future Extensibility Design
While keeping MVP simple, the architecture will support future additions:
- Advanced authentication (OAuth2, JWT)
- Rate limiting and throttling
- Caching layers
- Comprehensive observability (metrics, tracing)
- API versioning
- Request/response transformation
- Advanced validation rules

Each component will have clear extension points and interfaces for these future enhancements. 