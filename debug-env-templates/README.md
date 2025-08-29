# 🎯 Repository Debug Environment Templates

This directory contains environment templates for controlling repository debug logging during development and troubleshooting.

## Quick Start

### 1. Copy the template you need:
```bash
# For filter debugging
cp debug-env-templates/env.debug-filters .env

# For SQL debugging  
cp debug-env-templates/env.debug-sql .env

# For comprehensive debugging
cp debug-env-templates/env.debug-all .env
```

### 2. Run your application:
```bash
# The environment variables will be loaded automatically
python your_script.py
```

### 3. Turn off debug logging:
```bash
cp debug-env-templates/env.production .env
# or simply:
unset REPOSITORY_DEBUG DEBUG_CONTEXTS
```

## Available Templates

### 🔍 **env.debug-filters**
**Use when:** Debugging filter validation, application, or operator selection issues
- Enables: Filter-specific debug logging
- Shows: Filter validation, operator selection, filter application steps

### 🔍 **env.debug-sql** 
**Use when:** Debugging SQL generation, query building, or statement construction
- Enables: SQL construction debug logging  
- Shows: SQL building steps, WHERE/JOIN clause generation, final SQL compilation

### 🔍 **env.debug-joins**
**Use when:** Debugging table joins, relationship mapping, or join performance
- Enables: Join operations debug logging
- Shows: Table joins, relationship mapping, DISTINCT requirements, join performance

### 🔍 **env.debug-query-steps**
**Use when:** Debugging query execution flow, performance, or step-by-step execution
- Enables: Query execution step debugging
- Shows: Query pipeline, execution timing, entity mapping, result processing

### 🔍 **env.debug-combined**
**Use when:** Debugging complex issues spanning multiple components
- Enables: filters + sql + joins debugging
- Shows: End-to-end query problems, comprehensive troubleshooting

### 🎯 **env.debug-all**
**Use when:** You need to see everything (can be very verbose)
- Enables: ALL repository debug logging + verbose performance
- Shows: Complete detailed logging across all components

### 🚀 **env.production**
**Use for:** Production deployments
- Enables: Only WARNING and ERROR level logs
- Shows: Minimal logging, performance warnings, error tracking

## Environment Variable Reference

### Global Controls
```bash
REPOSITORY_DEBUG=true          # Enable ALL repository debug logging
LOG_LEVEL=DEBUG               # Global log level
VERBOSE_PERFORMANCE=true      # Enable detailed performance logging
```

### Component-Specific Controls
```bash
DEBUG_CONTEXTS=filters,sql,joins    # Enable specific contexts
FILTERS_DEBUG=true                  # Enable only filter debugging
SQL_DEBUG=true                     # Enable only SQL debugging  
JOINS_DEBUG=true                   # Enable only join debugging
QUERY_STEPS_DEBUG=true             # Enable only query step debugging
```

## Development Workflow Examples

### Scenario 1: Filter Not Working
```bash
# Enable filter debugging
export DEBUG_CONTEXTS=filters

# Run your code and see filter validation/application logs
python your_script.py

# Turn off when done
unset DEBUG_CONTEXTS
```

### Scenario 2: Wrong SQL Generated
```bash
# Enable SQL debugging
export DEBUG_CONTEXTS=sql

# See SQL construction steps
python your_script.py
```

### Scenario 3: Performance Issue
```bash
# Enable performance monitoring + query steps
export DEBUG_CONTEXTS=query_steps
export VERBOSE_PERFORMANCE=true

# See detailed timing and performance warnings
python your_script.py
```

### Scenario 4: Complex Multi-Component Issue
```bash
# Enable comprehensive debugging
export REPOSITORY_DEBUG=true

# See everything (can be verbose)
python your_script.py
```

## Interactive Debugging

### In Python Shell/Tests:
```python
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger

# See available debug options
RepositoryLogger.show_debug_usage_examples()

# Enable debug for current session
repo._repo_logger.enable_debug_for_session(['filters', 'sql'])

# ... do your debugging

# Disable when done
repo._repo_logger.disable_debug_for_session()
```

## Tips for Effective Debugging

### 1. Start Specific, Get Broader
```bash
# Start with specific component
DEBUG_CONTEXTS=filters

# If that doesn't help, expand
DEBUG_CONTEXTS=filters,sql

# Last resort: see everything
REPOSITORY_DEBUG=true
```

### 2. Use Performance Monitoring
```bash
# Always useful for debugging performance issues
VERBOSE_PERFORMANCE=true
```

### 3. Production-Safe
```bash
# These settings are safe for production troubleshooting
LOG_LEVEL=WARNING
VERBOSE_PERFORMANCE=false
```

### 4. Team Collaboration
```bash
# Each developer can use different debug settings without conflicts
# Developer A:
export DEBUG_CONTEXTS=filters

# Developer B:  
export DEBUG_CONTEXTS=sql

# No conflicts, no accidental commits
```

## Integration with IDEs

### VS Code
Add to your `.vscode/launch.json`:
```json
{
    "name": "Debug with Filters",
    "type": "python",
    "env": {
        "DEBUG_CONTEXTS": "filters"
    }
}
```

### PyCharm
Add to Run Configuration Environment Variables:
```
DEBUG_CONTEXTS=sql
VERBOSE_PERFORMANCE=true
```

## Best Practices

1. **Never commit debug environment files** - Use `.gitignore`
2. **Use specific contexts** - Don't default to `REPOSITORY_DEBUG=true`
3. **Document what you're debugging** - Add comments to your debug env files
4. **Clean up after debugging** - Unset variables or copy `env.production`
5. **Share debug scenarios** - Create custom env files for common team debugging scenarios

## Troubleshooting

### "Not seeing any debug logs?"
1. Check that you're using the right context name
2. Verify environment variables are set: `echo $DEBUG_CONTEXTS`
3. Make sure you're using the conditional debug methods in code
4. Try `REPOSITORY_DEBUG=true` to see if global debug works

### "Too much output?"
1. Use more specific contexts: `DEBUG_CONTEXTS=filters` instead of `DEBUG_CONTEXTS=all`
2. Turn off verbose performance: `VERBOSE_PERFORMANCE=false`
3. Use production settings: `cp env.production .env`

### "Debug not working in tests?"
1. Set environment variables before running tests
2. Use pytest with environment: `DEBUG_CONTEXTS=filters pytest test_file.py`
3. Use session debugging in test setup 