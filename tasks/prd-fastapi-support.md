# PRD: FastAPI Support with Cognito Authentication

---
feature: fastapi-support
complexity: detailed
created: 2024-12-19
version: 1.0
---

## Executive Summary
### Problem Statement
The current menu planning backend only supports AWS Lambda deployment, limiting local development capabilities and deployment flexibility. Developers need a FastAPI runtime for better development experience, debugging, and Railway deployment while maintaining compatibility with existing AWS Lambda infrastructure.

### Proposed Solution
Implement FastAPI runtime support alongside existing AWS Lambda infrastructure, including:
- FastAPI application with context-specific routing
- Cognito authentication strategy with JWT token validation and refresh
- Middleware adaptation for FastAPI using existing patterns
- Dependency injection system for FastAPI
- Development and production configurations

### Business Value
- **Developer Experience**: Local development server with hot reload and debugging tools
- **Deployment Flexibility**: Railway deployment with automatic containerization
- **Simplified Deployment**: Railway handles containerization and deployment automatically
- **Improved Testing**: Better integration testing capabilities
- **Faster Development**: Reduced AWS dependency for local work

### Success Criteria
- All 4 business contexts (products_catalog, recipes_catalog, client_onboarding, iam) have working FastAPI endpoints
- Cognito authentication works with JWT token validation and refresh
- Existing middleware system reused effectively across both runtimes
- Local development server runs without AWS dependencies
- API responses match Lambda endpoint responses exactly

## Goals and Non-Goals
### Goals
1. **FastAPI Runtime**: Complete FastAPI application with all context endpoints
2. **Cognito Integration**: Direct JWT token validation and refresh handling
3. **Middleware Reuse**: Adapt existing middleware system for FastAPI
4. **Development Experience**: Local server with debugging and testing capabilities
5. **Railway Deployment**: Seamless deployment via Railway with GitHub integration
6. **API Compatibility**: Identical responses between Lambda and FastAPI endpoints

### Non-Goals
1. **Replace AWS Lambda**: Both runtimes will coexist
2. **Change Business Logic**: No modifications to domain models or business rules
3. **Modify Lambda Endpoints**: Existing AWS Lambda code remains unchanged
4. **Database Changes**: No schema modifications required
5. **UI Changes**: Backend-only feature

## User Stories
### Story 1: Local Development Server
**As a** backend developer **I want** to run a local FastAPI server **So that** I can develop and test without AWS dependencies

**Acceptance Criteria:**
- [ ] FastAPI server starts with `uv run python -m src.runtimes.fastapi.app`
- [ ] All endpoints accessible at `http://localhost:8000`
- [ ] Hot reload works for code changes
- [ ] Interactive API docs available at `/docs`

### Story 4: Railway Deployment
**As a** developer **I want** to deploy FastAPI to Railway **So that** I can have a production-ready API without manual containerization

**Acceptance Criteria:**
- [ ] Railway deployment configuration (railway.json)
- [ ] Environment variables configured for production
- [ ] Automatic deployment from GitHub
- [ ] Production URL accessible and functional

### Story 2: Cognito Authentication
**As a** developer **I want** to authenticate using Cognito JWT tokens **So that** I can test authenticated endpoints locally

**Acceptance Criteria:**
- [ ] JWT tokens validated against Cognito
- [ ] Token refresh handled automatically
- [ ] User context available in request handlers
- [ ] Authentication errors return proper HTTP status codes

### Story 3: Context Endpoints
**As a** developer **I want** to access all business context endpoints **So that** I can test complete functionality

**Acceptance Criteria:**
- [ ] Products catalog endpoints (`/products/*` - query, fetch, search, create)
- [ ] Recipes catalog endpoints (`/recipes/*`, `/meals/*`, `/clients/*`, `/shopping-list/*`)
- [ ] Client onboarding endpoints (`/forms/*`, `/webhooks/*`, `/query-responses/*`)
- [ ] IAM endpoints (`/users/*`, `/roles/*`, `/assign-role/*`)

## Technical Specifications
### Thread Safety & Async Considerations
**Critical Requirements for FastAPI Persistent Process:**

**Thread Safety:**
- FastAPI runs in a persistent multithreaded process (unlike Lambda's single-threaded execution)
- All shared state must be thread-safe (caching, connection pools, global variables)
- Use thread-safe data structures and synchronization primitives where needed
- Avoid mutable global state; prefer request-scoped or dependency-injected state

**Async Implementation:**
- All I/O operations must be async-compatible (no blocking calls in async context)
- Database connections must use async drivers (asyncpg for PostgreSQL)
- HTTP clients must be async (httpx, not requests)
- File I/O should use aiofiles or run in thread pool
- Cognito token validation must be async-compatible

**Caching Strategy:**
- Request-scoped caching for authentication (per-request isolation)
- Thread-safe cache implementations (avoid simple dicts for shared state)
- Consider Redis for shared caching across requests if needed
- Clear cache boundaries to prevent memory leaks

**Dependency Injection:**
- Use FastAPI's dependency system for request-scoped services
- Avoid singleton patterns that could cause thread safety issues
- Ensure database sessions are properly scoped per request

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Middleware      │    │   Business      │
│                 │    │  System          │    │   Contexts      │
│ ┌─────────────┐ │    │                  │    │                 │
│ │   Routers   │ │◄───┤ Auth Strategy    │◄───┤ Products        │
│ │             │ │    │ Logging          │    │ Recipes         │
│ │ /products   │ │    │ Error Handling   │    │ Client Onboard  │
│ │ /recipes    │ │    │                  │    │ IAM             │
│ │ /forms      │ │    │                  │    │                 │
│ │ /users      │ │    │                  │    │                 │
│ └─────────────┘ │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cognito       │    │   Database       │    │   Message Bus   │
│   JWT Tokens    │    │   PostgreSQL     │    │   & Commands    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Model
**Authentication Context**:
```python
class FastAPIAuthContext:
    user_id: str
    user_roles: list[str]
    is_authenticated: bool
    user_object: SeedUser
    token_info: dict[str, Any]
```

**Request/Response Models**:
- Reuse existing API schemas from each context
- Maintain compatibility with Lambda response format
- Add FastAPI-specific request models where needed

### API Specifications
**Base URL**: 
- Development: `http://localhost:8000`
- Production: `https://your-app.railway.app` (Railway deployment)

**Authentication**: Bearer token in Authorization header
```
Authorization: Bearer <cognito_jwt_token>
```

**Response Format**: JSON with consistent structure
```json
{
  "statusCode": 200,
  "headers": {...},
  "body": {...}
}
```

## Functional Requirements
### FR1: FastAPI Application Structure
**Description**: Main FastAPI application with routing and middleware
**Priority**: P0

**Requirements**:
- FastAPI app with context-specific routers
- Middleware composition (auth, logging, error handling)
- CORS configuration
- Health check endpoint
- Interactive API documentation

### FR2: Cognito Authentication Strategy
**Description**: JWT token validation and user context extraction
**Priority**: P0

**Requirements**:
- JWT token validation against Cognito
- User data fetching from IAM internal endpoints
- Token refresh mechanism
- Request-scoped caching
- Error handling for invalid/expired tokens

### FR3: Middleware Adaptation
**Description**: Adapt existing middleware for FastAPI
**Priority**: P0

**Requirements**:
- FastAPI authentication strategy
- FastAPI logging strategy
- FastAPI error handling strategy
- Middleware composition system
- Request/response transformation

### FR4: Context Endpoints
**Description**: FastAPI endpoints for all business contexts
**Priority**: P0

**Requirements**:
- Products catalog endpoints (query, fetch, search, create operations)
- Recipes catalog endpoints (recipes, meals, clients, shopping lists)
- Client onboarding endpoints (forms, webhooks, queries)
- IAM endpoints (users, roles, assignments)
- Consistent error handling and responses

### FR5: Dependency Injection
**Description**: FastAPI dependency injection system
**Priority**: P1

**Requirements**:
- Container integration with FastAPI
- Request-scoped dependencies
- Database session management
- Service injection patterns

### FR6: Thread Safety & Async Compatibility
**Description**: Ensure all components work safely in FastAPI's multithreaded environment
**Priority**: P0

**Requirements**:
- Thread-safe authentication caching
- Async-compatible IAM provider
- Request-scoped database sessions
- No blocking I/O in async context
- Thread-safe middleware implementations
- Proper async/await usage throughout

## Non-Functional Requirements
### Performance
- **Response time**: < 200ms for authenticated requests
- **Throughput**: Support 100+ concurrent requests
- **Memory usage**: < 512MB for development server
- **Startup time**: < 5 seconds for local server
- **Thread safety**: All components must be thread-safe for FastAPI's multithreaded environment

### Security
- **Authentication**: JWT token validation with Cognito
- **Authorization**: Role-based access control
- **CORS**: Configured for development and production
- **Input validation**: Pydantic model validation
- **Error handling**: No sensitive data in error responses

### Reliability
- **Error handling**: Consistent error responses
- **Logging**: Structured logging for all operations
- **Monitoring**: Health check endpoints
- **Graceful degradation**: Fallback for auth failures
- **Thread safety**: No race conditions in shared state
- **Async safety**: Proper async/await usage throughout

## Risk Assessment
### Technical Risks
1. **Middleware Integration Complexity** - Mitigation: Incremental implementation with existing patterns
2. **Cognito Token Handling** - Mitigation: Use proven JWT libraries and thorough testing
3. **Performance Impact** - Mitigation: Request-scoped caching and optimization
4. **API Compatibility** - Mitigation: Comprehensive testing against Lambda responses
5. **Thread Safety Issues** - Mitigation: Use thread-safe patterns, avoid shared mutable state
6. **Blocking I/O in Async Context** - Mitigation: Use async-compatible libraries, proper async patterns

### Business Risks
1. **Development Timeline** - Mitigation: Phased implementation with MVP first
2. **Maintenance Overhead** - Mitigation: Shared middleware and common patterns
3. **Deployment Complexity** - Mitigation: Clear documentation and automation

## Testing Strategy
- **Unit Tests**: 90% coverage for new FastAPI components
- **Integration Tests**: Authentication flow and endpoint functionality
- **E2E Tests**: Complete request/response cycles
- **Performance Tests**: Load testing for concurrent requests
- **Compatibility Tests**: Response matching with Lambda endpoints
- **Thread Safety Tests**: Concurrent request testing, race condition detection
- **Async Tests**: Proper async/await behavior, no blocking I/O

## Implementation Plan
### Phase 1: Core Infrastructure (Week 1-2)
- [ ] FastAPI application structure
- [ ] Basic routing system
- [ ] Middleware composition framework
- [ ] Health check and documentation endpoints

### Phase 2: Authentication System (Week 2-3)
- [ ] Cognito JWT validation
- [ ] FastAPI authentication strategy
- [ ] User context extraction
- [ ] Token refresh mechanism
- [ ] Thread-safe authentication caching
- [ ] Async-compatible IAM provider

### Phase 3: Context Endpoints (Week 3-4)
- [ ] Products catalog endpoints (query, fetch, search, create)
- [ ] Recipes catalog endpoints (recipes, meals, clients, shopping lists)
- [ ] Client onboarding endpoints (forms, webhooks, queries)
- [ ] IAM endpoints (users, roles, assignments)
- [ ] Thread-safe endpoint implementations
- [ ] Async-compatible business logic

### Phase 4: Railway Deployment (Week 4-5)
- [ ] Railway configuration and deployment
- [ ] Environment variable setup
- [ ] Production testing
- [ ] Documentation and examples

## Monitoring
### Key Metrics
- **Request latency**: Average response time per endpoint
- **Authentication success rate**: Token validation success
- **Error rates**: 4xx and 5xx response rates
- **Cache hit rates**: Authentication and user data caching

### Health Checks
- **Application health**: `/health` endpoint
- **Database connectivity**: Database health check
- **Cognito connectivity**: Authentication service health
- **Dependencies**: All external service dependencies

## Dependencies
- **Internal**: Existing middleware system, business contexts, IAM internal endpoints
- **External**: FastAPI framework, Cognito JWT validation, PostgreSQL database
- **Development**: Python 3.12+, uv package manager, local development tools
- **Deployment**: Railway platform, GitHub integration

## Timeline
- **Phase 1**: 2 weeks (Core Infrastructure)
- **Phase 2**: 1 week (Authentication)
- **Phase 3**: 1 week (Context Endpoints)
- **Phase 4**: 1 week (Integration & Testing)
- **Total**: 5 weeks

## Success Metrics
- All 4 contexts have working FastAPI endpoints
- Local development server runs without AWS dependencies
- Authentication works with Cognito JWT tokens
- API responses match Lambda endpoint responses
- Developer satisfaction with local development experience
