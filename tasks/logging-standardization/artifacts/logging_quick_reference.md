# Logging Quick Reference Guide

## Quick Start

```python
from src.logging.logger import logger

# Basic structured log
logger.info(
    "Operation completed",
    extra={
        'user_id': 'user_123',
        'operation': 'create_recipe',
        'status': 'success'
    }
)
```

## Common Patterns

### User Operations
```python
logger.info(
    "User action performed",
    extra={
        'user_id': user_id,
        'operation': 'operation_name',
        'context': 'bounded_context_name',
        'duration_ms': 150,
        'status': 'success'
    }
)
```

### Database Operations
```python
logger.info(
    "Database query executed",
    extra={
        'user_id': user_id,
        'operation': 'get_user_data',
        'component': 'user_repository',
        'query_type': 'SELECT',
        'duration_ms': 45,
        'rows_returned': 1
    }
)
```

### Error Logging
```python
try:
    # operation
    pass
except Exception as e:
    logger.error(
        "Operation failed",
        extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'user_id': user_id,
            'operation': 'operation_name',
            'component': 'service_name'
        },
        exc_info=True
    )
```

### Security Events
```python
logger.warning(
    "Security event detected",
    extra={
        'security_event': True,
        'event_type': 'unauthorized_access',
        'user_id': user_id,
        'client_ip': request.client_ip,
        'resource': 'protected_resource'
    }
)
```

## Correlation ID Management

```python
from src.logging.logger import set_correlation_id, generate_correlation_id

# For background tasks
correlation_id = generate_correlation_id()
set_correlation_id(correlation_id)

# All subsequent logs will include correlation_id automatically
```

## Bounded Context Patterns

### Client Onboarding
```python
extra={
    'context': 'client_onboarding',
    'user_id': user_id,
    'operation': 'verify_email',
    'step': 'email_verification'
}
```

### Products Catalog
```python
extra={
    'context': 'products_catalog',
    'user_id': user_id,
    'operation': 'search_products',
    'query': search_term,
    'results_count': len(results)
}
```

### Recipes Catalog
```python
extra={
    'context': 'recipes_catalog',
    'user_id': user_id,
    'operation': 'create_recipe',
    'recipe_id': recipe.id,
    'recipe_name': recipe.name
}
```

### IAM
```python
extra={
    'context': 'iam',
    'user_id': user_id,
    'operation': 'authenticate_user',
    'auth_method': 'jwt_token',
    'permissions': user.permissions
}
```

### Shared Kernel
```python
extra={
    'context': 'shared_kernel',
    'operation': 'publish_event',
    'event_type': 'recipe_created',
    'event_id': event.id
}
```

## Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational information  
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events (application can continue)
- **CRITICAL**: Serious error events

## Do's and Don'ts

### ✅ Do
- Use structured logging with `extra` parameter
- Include relevant context (user_id, operation, component)
- Log errors with sufficient debugging information
- Use appropriate log levels
- Include correlation IDs for request tracing

### ❌ Don't
- Log sensitive data (passwords, tokens, PII)
- Use f-strings for log messages with sensitive data
- Include stack traces for security errors
- Over-log (every function call)
- Log without context

## Performance Tips

- Keep structured data < 1KB per log entry
- Use appropriate log levels to control volume
- Avoid logging in tight loops
- Consider async logging for high-volume operations

## Testing Logs

```python
import logging
from io import StringIO

def test_operation_logging():
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger().addHandler(handler)
    
    # Execute operation
    perform_operation()
    
    # Verify logging
    log_output = log_capture.getvalue()
    assert 'Operation completed' in log_output
```

## Environment Variables

```bash
# Local development
export LOG_LEVEL=DEBUG
export REPOSITORY_DEBUG=true

# Production
export LOG_LEVEL=INFO
```

## Common Fields Reference

| Field | Description | Example |
|-------|-------------|---------|
| `user_id` | User performing operation | `"user_123"` |
| `operation` | Specific operation | `"create_recipe"` |
| `context` | Bounded context | `"recipes_catalog"` |
| `component` | Service/repository | `"recipe_service"` |
| `duration_ms` | Operation duration | `150` |
| `status` | Operation result | `"success"` |
| `error_type` | Exception type | `"ValidationError"` |
| `error_message` | Error description | `"Invalid input"` |

For complete documentation, see `logging_guidelines.md`.
