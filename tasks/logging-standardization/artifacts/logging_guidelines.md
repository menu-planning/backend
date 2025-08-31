# Logging Guidelines for Menu Planning Backend

## Overview

This document establishes the logging standards and best practices for the Menu Planning Backend application. These guidelines are based on the completed logging standardization migration and ensure consistent, structured, and observable logging across all bounded contexts.

## Table of Contents

1. [Logging Architecture](#logging-architecture)
2. [Structured Logging Standards](#structured-logging-standards)
3. [Correlation ID Management](#correlation-id-management)
4. [Context-Specific Logging](#context-specific-logging)
5. [Error Logging Best Practices](#error-logging-best-practices)
6. [Performance and Security Considerations](#performance-and-security-considerations)
7. [Development Guidelines](#development-guidelines)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Examples and Code Samples](#examples-and-code-samples)

## Logging Architecture

### Current Implementation

The application uses **structlog** as the primary logging framework, providing:

- **Structured JSON logging** for machine readability
- **Automatic correlation ID injection** for request tracing
- **ELK/CloudWatch compatibility** for log aggregation
- **Context-aware logging** across bounded contexts
- **Performance-optimized** logging with minimal overhead

### Key Components

```python
from src.logging.logger import logger, set_correlation_id, generate_correlation_id
```

- **Logger Instance**: `logger` - Main logging interface
- **Correlation ID Management**: `set_correlation_id()`, `generate_correlation_id()`
- **Structured Data**: Use `extra` parameter for contextual information
- **JSON Output**: Automatic formatting for log aggregation systems

## Structured Logging Standards

### Basic Logging Pattern

```python
from src.logging.logger import logger

# Basic structured log
logger.info(
    "User operation completed",
    extra={
        'user_id': 'user_123',
        'operation': 'create_recipe',
        'duration_ms': 245,
        'status': 'success'
    }
)
```

### Required Fields

All log entries should include these contextual fields when applicable:

- **correlation_id**: Automatically injected (do not manually add)
- **user_id**: User performing the operation
- **operation**: Specific operation being performed
- **component**: Bounded context or service component
- **timestamp**: Automatically added by the logging system

### Optional Contextual Fields

Include relevant contextual information:

```python
logger.info(
    "Database query executed",
    extra={
        'user_id': 'user_123',
        'operation': 'get_user_recipes',
        'component': 'recipes_repository',
        'query_type': 'SELECT',
        'table': 'recipes',
        'duration_ms': 45,
        'rows_returned': 12,
        'filters': {'owner_id': 'user_123', 'status': 'published'}
    }
)
```

## Correlation ID Management

### Automatic Injection

Correlation IDs are automatically injected into all log entries when set in the context:

```python
from src.logging.logger import set_correlation_id, generate_correlation_id

# Generate and set correlation ID (typically done by middleware)
correlation_id = generate_correlation_id()
set_correlation_id(correlation_id)

# All subsequent logs will include the correlation ID automatically
logger.info("Operation started")  # correlation_id automatically included
```

### Middleware Integration

The correlation ID middleware automatically handles correlation ID management for HTTP requests:

```python
# Correlation ID is extracted from headers or generated automatically
# X-Correlation-ID header takes precedence
# All logs within the request context will include the correlation ID
```

### Manual Correlation ID Management

For background tasks or async operations:

```python
import asyncio
from src.logging.logger import set_correlation_id, generate_correlation_id

async def background_task():
    # Set correlation ID for background task
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    
    logger.info("Background task started", extra={'task_type': 'data_sync'})
    # ... task logic ...
    logger.info("Background task completed", extra={'task_type': 'data_sync'})
```

## Context-Specific Logging

### Bounded Context Guidelines

Each bounded context should follow consistent logging patterns:

#### Client Onboarding Context

```python
logger.info(
    "User onboarding step completed",
    extra={
        'context': 'client_onboarding',
        'user_id': 'user_123',
        'operation': 'verify_email',
        'step': 'email_verification',
        'verification_method': 'token',
        'status': 'success'
    }
)
```

#### Products Catalog Context

```python
logger.info(
    "Product search executed",
    extra={
        'context': 'products_catalog',
        'user_id': 'user_123',
        'operation': 'search_products',
        'query': 'organic vegetables',
        'filters': ['organic', 'in_stock'],
        'results_count': 45,
        'duration_ms': 120
    }
)
```

#### Recipes Catalog Context

```python
logger.info(
    "Recipe created successfully",
    extra={
        'context': 'recipes_catalog',
        'user_id': 'user_123',
        'operation': 'create_recipe',
        'recipe_id': 'recipe_456',
        'recipe_name': 'Pasta Carbonara',
        'ingredients_count': 6,
        'difficulty': 'medium'
    }
)
```

#### IAM Context

```python
logger.info(
    "User authentication successful",
    extra={
        'context': 'iam',
        'user_id': 'user_123',
        'operation': 'authenticate_user',
        'auth_method': 'jwt_token',
        'permissions': ['recipe:read', 'recipe:write'],
        'session_duration': 3600
    }
)
```

#### Shared Kernel Context

```python
logger.info(
    "Domain event published",
    extra={
        'context': 'shared_kernel',
        'operation': 'publish_event',
        'event_type': 'recipe_created',
        'event_id': 'evt_789',
        'aggregate_id': 'recipe_456',
        'user_id': 'user_123'
    }
)
```

## Error Logging Best Practices

### Exception Logging

Always include comprehensive context for exceptions:

```python
try:
    # Business logic
    result = process_recipe_creation(recipe_data)
except ValidationError as e:
    logger.error(
        "Recipe validation failed",
        extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'user_id': 'user_123',
            'operation': 'create_recipe',
            'component': 'recipe_service',
            'validation_errors': e.errors if hasattr(e, 'errors') else [],
            'recipe_data': recipe_data,  # Ensure no sensitive data
            'timestamp': time.time()
        },
        exc_info=True  # Include stack trace
    )
    # Handle error appropriately
```

### Database Errors

```python
try:
    recipes = repository.get_user_recipes(user_id)
except ConnectionError as e:
    logger.error(
        "Database connection failed",
        extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'component': 'recipes_repository',
            'operation': 'get_user_recipes',
            'user_id': user_id,
            'database_host': 'prod-db-cluster.example.com',
            'retry_count': 3,
            'timeout_seconds': 30
        },
        exc_info=True
    )
    
    # Log recovery action
    logger.warning(
        "Attempting database failover",
        extra={
            'component': 'recipes_repository',
            'recovery_action': 'failover_to_secondary',
            'secondary_host': 'backup-db-cluster.example.com'
        }
    )
```

### Security Errors

For security-related errors, **do not include stack traces**:

```python
try:
    authorize_user_action(user_id, 'delete_recipe', recipe_id)
except PermissionError as e:
    logger.error(
        "Authorization failed",
        extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'component': 'authorization_service',
            'operation': 'delete_recipe',
            'user_id': user_id,
            'resource_id': recipe_id,
            'required_permission': 'recipe:delete',
            'user_permissions': user.permissions,
            'client_ip': request.client_ip,
            'security_event': True
        },
        exc_info=False  # No stack trace for security errors
    )
```

## Performance and Security Considerations

### Performance Guidelines

1. **Avoid Over-Logging**: Log meaningful events, not every function call
2. **Use Appropriate Log Levels**: 
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: General operational information
   - `WARNING`: Potentially harmful situations
   - `ERROR`: Error events that might still allow the application to continue
   - `CRITICAL`: Serious error events

3. **Structured Data Size**: Keep structured data reasonable (< 1KB per log entry)
4. **Async Logging**: The logging system is optimized for async operations

### Security Guidelines

1. **Never Log Sensitive Data**:
   - Passwords, tokens, API keys
   - Credit card numbers, SSNs
   - Personal identification information

2. **Sanitize User Input**:
   ```python
   # Good: Sanitized logging
   logger.info(
       "User search query",
       extra={
           'user_id': user_id,
           'query': sanitize_for_logging(user_query),
           'results_count': len(results)
       }
   )
   ```

3. **Security Event Logging**:
   ```python
   logger.warning(
       "Suspicious activity detected",
       extra={
           'security_event': True,
           'event_type': 'multiple_failed_logins',
           'user_id': user_id,
           'client_ip': request.client_ip,
           'attempt_count': 5,
           'time_window_minutes': 10
       }
   )
   ```

## Development Guidelines

### Local Development

For local development, you can enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export REPOSITORY_DEBUG=true
```

### Testing

When writing tests, capture and verify log output:

```python
import logging
from io import StringIO

def test_user_creation_logging():
    # Capture log output
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    
    # Execute operation
    create_user(user_data)
    
    # Verify logging
    log_output = log_capture.getvalue()
    assert 'User created successfully' in log_output
    assert 'user_123' in log_output
```

### Code Review Checklist

When reviewing code, ensure:

- [ ] Appropriate log levels used
- [ ] Structured data includes relevant context
- [ ] No sensitive data in logs
- [ ] Error logs include sufficient debugging information
- [ ] Correlation ID context maintained in async operations
- [ ] Log messages are clear and actionable

## Monitoring and Alerting

### Log Aggregation

Logs are automatically formatted for ELK Stack and CloudWatch:

```json
{
  "@timestamp": "2024-01-15T14:30:00.000Z",
  "level": "INFO",
  "logger": "recipes_catalog_context",
  "message": "Recipe created successfully",
  "correlation_id": "abc12345",
  "user_id": "user_123",
  "operation": "create_recipe",
  "recipe_id": "recipe_456",
  "context": "recipes_catalog"
}
```

### Alerting Patterns

Set up alerts based on structured log data:

```javascript
// Example CloudWatch/ELK query
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"term": {"component": "database_repository"}},
        {"range": {"@timestamp": {"gte": "now-5m"}}}
      ]
    }
  }
}
```

### Dashboards

Create dashboards using structured log fields:

- **Request Volume**: Count by `operation` and `context`
- **Error Rates**: Error count by `component` and `error_type`
- **Performance**: Average `duration_ms` by `operation`
- **User Activity**: Operations by `user_id`

## Examples and Code Samples

### Complete Request Flow Example

```python
from src.logging.logger import logger, set_correlation_id

async def create_recipe_endpoint(request):
    # Correlation ID set by middleware
    user_id = request.user.id
    recipe_data = request.json()
    
    logger.info(
        "Recipe creation request received",
        extra={
            'context': 'api',
            'operation': 'create_recipe',
            'user_id': user_id,
            'request_size': len(str(recipe_data))
        }
    )
    
    try:
        # Validate ingredients
        logger.info(
            "Validating recipe ingredients",
            extra={
                'context': 'products_catalog',
                'operation': 'validate_ingredients',
                'user_id': user_id,
                'ingredients_count': len(recipe_data.get('ingredients', []))
            }
        )
        
        # Create recipe
        recipe = await recipe_service.create_recipe(user_id, recipe_data)
        
        logger.info(
            "Recipe created successfully",
            extra={
                'context': 'recipes_catalog',
                'operation': 'create_recipe',
                'user_id': user_id,
                'recipe_id': recipe.id,
                'recipe_name': recipe.name
            }
        )
        
        return {"recipe_id": recipe.id, "status": "created"}
        
    except ValidationError as e:
        logger.error(
            "Recipe validation failed",
            extra={
                'error_type': 'ValidationError',
                'error_message': str(e),
                'context': 'recipes_catalog',
                'operation': 'create_recipe',
                'user_id': user_id,
                'validation_errors': e.errors
            },
            exc_info=True
        )
        raise
```

### Background Task Example

```python
import asyncio
from src.logging.logger import logger, generate_correlation_id, set_correlation_id

async def sync_nutrition_data():
    # Generate correlation ID for background task
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    
    logger.info(
        "Nutrition data sync started",
        extra={
            'context': 'background_tasks',
            'operation': 'sync_nutrition_data',
            'task_type': 'scheduled'
        }
    )
    
    try:
        # Sync logic
        products_updated = await sync_products_nutrition()
        
        logger.info(
            "Nutrition data sync completed",
            extra={
                'context': 'background_tasks',
                'operation': 'sync_nutrition_data',
                'products_updated': products_updated,
                'status': 'success'
            }
        )
        
    except Exception as e:
        logger.error(
            "Nutrition data sync failed",
            extra={
                'error_type': type(e).__name__,
                'error_message': str(e),
                'context': 'background_tasks',
                'operation': 'sync_nutrition_data',
                'status': 'failed'
            },
            exc_info=True
        )
        raise
```

## Migration Notes

### From Standard Logging

If you encounter legacy standard logging code:

```python
# OLD - Standard logging (deprecated)
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user_id} created recipe {recipe_id}")

# NEW - Structured logging
from src.logging.logger import logger
logger.info(
    "Recipe created successfully",
    extra={
        'user_id': user_id,
        'recipe_id': recipe_id,
        'operation': 'create_recipe'
    }
)
```

### Performance Impact

The migration to structured logging has a performance impact:
- **~47% slower** than standard logging
- **Acceptable for production** use with proper optimization
- **Benefits outweigh costs** for observability and debugging

## Conclusion

These logging guidelines ensure consistent, observable, and maintainable logging across the Menu Planning Backend. Following these standards will:

- Improve debugging and troubleshooting capabilities
- Enable effective monitoring and alerting
- Support compliance and security requirements
- Facilitate operational excellence

For questions or clarifications, refer to the logging standardization migration artifacts in `tasks/logging-standardization/artifacts/`.

---

**Document Version**: 1.0  
**Last Updated**: January 21, 2025  
**Migration Phase**: Phase 4 - Documentation  
**Status**: Production Ready
