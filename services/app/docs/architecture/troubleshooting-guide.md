[← Index](./README.md) | [Quick Start](./quick-start-guide.md) | [Workflows](./ai-agent-workflows.md) | [Patterns](./pattern-library.md) | [Troubleshooting](./troubleshooting-guide.md)

---

# Troubleshooting Guide - Menu Planning Backend

## 🎯 Quick Problem Resolution

This guide provides step-by-step solutions for common issues AI agents encounter when working with the menu planning backend. Each section includes actual error messages, root causes, and proven solutions.

## 📋 Problem Categories

- [Common Import Errors](#common-import-errors) - Module resolution and path issues
- [Test Failures](#test-failures) - Debug failing tests and fixtures
- [Cache Issues](#cache-issues) - Domain and repository cache problems
- [Database Connection Problems](#database-connection-problems) - PostgreSQL and SQLAlchemy issues
- [Lambda Deployment Issues](#lambda-deployment-issues) - AWS deployment problems
- [Quick Reference](#quick-reference) - Command cheat sheet

---

## Common Import Errors

### Problem: ModuleNotFoundError with domain imports

**Error Message:**
```
ModuleNotFoundError: No module named 'src.contexts.shared_kernel.domain.value_objects.nutri_facts'
```

**Root Cause:** 
The import path structure changed or the module is in a different location.

**Solution:**
```python
# ❌ Incorrect (old path)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

# ✅ Correct (current path)
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
```

**Verification Command:**
```bash
poetry run python -c "from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts; print('Import successful')"
```

### Problem: Cannot import domain aggregates

**Error Message:**
```
ImportError: cannot import name 'Meal' from 'src.contexts.recipes_catalog.core.domain.meal'
```

**Root Cause:** 
Trying to import from package directory instead of specific module.

**Solution:**
```python
# ❌ Incorrect (package import)
from src.contexts.recipes_catalog.core.domain.meal import Meal

# ✅ Correct (specific module import)
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
```

**Verification Command:**
```bash
poetry run python -c "from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal; print('Meal import successful')"
```

### Problem: Pydantic validation errors on import

**Error Message:**
```
pydantic.errors.ConfigError: field "nutri_facts" not yet prepared so type is still a ForwardRef
```

**Root Cause:** 
Circular import or missing model rebuild call.

**Solution:**
```python
# Add this after all model definitions
from pydantic import BaseModel

# Rebuild models to resolve ForwardRefs
BaseModel.model_rebuild()

# Or for specific models:
ApiMeal.model_rebuild()
```

**Verification:**
```bash
poetry run python -c "
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
print('API schema import successful')
"
```

### Problem: Repository import failures

**Error Message:**
```
ModuleNotFoundError: No module named 'src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository'
```

**Root Cause:** 
Repository class naming convention confusion.

**Solution:**
```python
# ❌ Incorrect (wrong class name)
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepository

# ✅ Correct (actual class name)
from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
```

**Find All Repository Classes:**
```bash
find src -name "*_repository.py" -exec grep -l "class.*Repo" {} \;
```

### Problem: Test import path issues

**Error Message:**
```
ModuleNotFoundError: No module named 'tests.contexts.recipes_catalog.core.domain.meal.conftest'
```

**Root Cause:** 
Missing `__init__.py` files in test directories or wrong import structure.

**Solution:**
```python
# ❌ Incorrect (trying to import conftest)
from tests.contexts.recipes_catalog.core.domain.meal.conftest import create_meal

# ✅ Correct (import fixtures directly)
import pytest
from tests.conftest import create_meal

# Or use the fixture in test function
def test_meal_behavior(create_meal):
    meal = create_meal(name="Test Meal")
    assert meal.name == "Test Meal"
```

**Check Test Structure:**
```bash
find tests -name "__init__.py" | head -10
poetry run python -m pytest --collect-only tests/contexts/recipes_catalog/core/domain/meal/ | head -10
```

---

## Test Failures

### Problem: Test discovery failures

**Error Message:**
```
ImportError while importing test module 'tests/contexts/recipes_catalog/core/domain/meal/test_meal.py'
```

**Root Cause:** 
Import errors in test files or missing dependencies.

**Solution Process:**
1. **Check specific test file:**
```bash
poetry run python -c "import tests.contexts.recipes_catalog.core.domain.meal.test_meal"
```

2. **Run single test to isolate issue:**
```bash
poetry run python -m pytest tests/contexts/recipes_catalog/core/domain/meal/test_meal.py::test_specific_function -v
```

3. **Check test dependencies:**
```python
# In test file, verify all imports work
import pytest
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
```

### Problem: Fixture not found

**Error Message:**
```
fixture 'benchmark_timer' not found
available fixtures: create_meal, create_recipe, db_session
```

**Root Cause:** 
Fixture defined in wrong conftest.py or not imported properly.

**Solution:**
1. **Find fixture definition:**
```bash
grep -r "def benchmark_timer" tests/
```

2. **Check conftest.py scope:**
```python
# tests/conftest.py (root level - available to all tests)
@pytest.fixture
def benchmark_timer():
    """Simple timer fixture for performance assertions"""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None
            
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
            
        def __exit__(self, *args):
            if self.start_time is not None:
                self.elapsed = time.perf_counter() - self.start_time
        
        def assert_faster_than(self, seconds):
            if self.elapsed is None:
                raise ValueError("Timer was not used in context manager")
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
    
    return Timer
```

3. **Use fixture correctly:**
```python
def test_performance(benchmark_timer):
    with benchmark_timer() as timer:
        # Your test code here
        pass
    timer.assert_faster_than(0.100)
```

### Problem: Database session fixture issues

**Error Message:**
```
sqlalchemy.exc.InvalidRequestError: Object '<Meal>' is already attached to session '2' (this is '1')
```

**Root Cause:** 
Object attached to different session or session not properly scoped.

**Solution:**
```python
# ✅ Correct fixture usage
@pytest.mark.asyncio
async def test_meal_repository(db_session):
    # Create repository with test session
    meal_repo = MealRepo(db_session)
    
    # Create meal through repository (proper session management)
    meal = Meal.create_meal(
        name="Test Meal",
        author_id="test-author",
        meal_id="test-meal-id",
        menu_id="test-menu-id"
    )
    
    # Add to repository (handles session)
    await meal_repo.add(meal)
    await db_session.commit()
    
    # Query through same session
    retrieved = await meal_repo.get("test-meal-id")
    assert retrieved.name == "Test Meal"
```

**Debug Session Issues:**
```bash
# Run with detailed SQLAlchemy logging
SQLALCHEMY_LOG_LEVEL=DEBUG poetry run python -m pytest tests/test_specific.py -v -s
```

### Problem: Async test failures

**Error Message:**
```
RuntimeError: coroutine 'test_async_meal_creation' was never awaited
```

**Root Cause:** 
Missing `@pytest.mark.asyncio` decorator or incorrect async/await usage.

**Solution:**
```python
# ✅ Correct async test structure
import pytest

@pytest.mark.asyncio
async def test_async_meal_creation(db_session):
    meal_repo = MealRepo(db_session)
    
    # All repository operations are async
    meal = await meal_repo.get("meal-id")
    results = await meal_repo.query(filter={"author_id": "test"})
    await meal_repo.add(new_meal)
    await db_session.commit()
```

**Run Async Tests:**
```bash
# Install pytest-asyncio if missing
poetry add --group dev pytest-asyncio

# Run async tests
poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/repositories/ -v
```

### Problem: Mock and fixture conflicts

**Error Message:**
```
TypeError: 'AsyncMock' object is not callable
```

**Root Cause:** 
Incorrect mock setup for async functions or fixture interaction issues.

**Solution:**
```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_with_mock(db_session):
    # ✅ Correct async mock setup
    with patch('src.some.module.async_function', new_callable=AsyncMock) as mock_func:
        mock_func.return_value = "expected_result"
        
        # Test your code
        result = await your_function_that_calls_async_function()
        
        assert result == "expected_result"
        mock_func.assert_called_once()
```

**Debug Mock Issues:**
```python
# Add debug output to understand mock state
print(f"Mock called: {mock_func.called}")
print(f"Mock call count: {mock_func.call_count}")
print(f"Mock call args: {mock_func.call_args_list}")
```

---

## Cache Issues

### Problem: Cached property not invalidating

**Error Message:**
```
AssertionError: Expected nutrition to change after recipe update, but cache returned stale value
```

**Root Cause:** 
Cache invalidation not triggered when dependent data changes.

**Solution:**
```python
# Domain aggregate with proper cache invalidation
class Meal(Entity):
    def update_properties(self, **kwargs):
        # Check if recipes are being updated
        if 'recipes' in kwargs:
            # Invalidate nutrition cache before update
            self._invalidate_caches('nutri_facts')
        
        # Perform the update
        super().update_properties(**kwargs)
    
    @cached_property
    def nutri_facts(self) -> NutriFacts | None:
        """Cached nutrition calculation"""
        if not self.recipes:
            return None
        # Calculation logic here...
```

**Debug Cache State:**
```python
# Check what's currently cached
meal = your_meal_instance
cache_info = meal.get_cache_info()
print(f"Cached properties: {cache_info['cache_names']}")
print(f"Computed caches: {cache_info['computed_caches']}")

# Manual cache invalidation for testing
meal._invalidate_caches('nutri_facts')
print(f"After invalidation: {meal.get_cache_info()['computed_caches']}")
```

### Problem: Repository cache returning stale data

**Error Message:**
```
AssertionError: Expected updated meal name 'New Name', got 'Old Name'
```

**Root Cause:** 
Repository-level caching not invalidated after updates.

**Solution:**
```python
# Repository with proper cache management
class MealRepo(SaGenericRepository[Meal]):
    async def update(self, entity: Meal) -> None:
        # Clear entity from cache before update
        self._cache.pop(entity.id, None)
        
        # Perform update
        await super().update(entity)
        
        # Optionally warm cache with fresh data
        await self.get(entity.id, use_cache=False)
```

**Clear Repository Cache:**
```python
# For debugging - clear all repository caches
meal_repo._cache.clear()

# Or disable caching temporarily
meal = await meal_repo.get("meal-id", use_cache=False)
```

### Problem: Cross-aggregate cache consistency

**Error Message:**
```
AssertionError: Menu nutrition totals don't match sum of meal nutrition
```

**Root Cause:** 
Cache invalidation doesn't propagate across aggregate boundaries.

**Solution:**
```python
# Use domain events for cross-aggregate cache invalidation
@dataclass
class MealNutritionChanged(Event):
    meal_id: str
    old_nutrition: NutriFacts
    new_nutrition: NutriFacts

# Event handler in Menu aggregate
async def handle_meal_nutrition_changed(event: MealNutritionChanged, uow: UnitOfWork):
    # Find menus containing this meal
    menus = await uow.menus.query(filter={"meal_ids__contains": [event.meal_id]})
    
    for menu in menus:
        # Invalidate menu nutrition cache
        menu._invalidate_caches('total_nutrition')
        await uow.menus.update(menu)
```

**Debug Cross-Aggregate Issues:**
```bash
# Check event handlers are registered
poetry run python -c "
from src.contexts.recipes_catalog.core.bootstrap.bootstrap import bootstrap
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
uow = UnitOfWork()
bus = bootstrap(uow)
print('Event handlers:', bus.event_handlers.keys())
"
```

### Problem: Memory leaks from cached properties

**Error Message:**
```
MemoryError: Unable to allocate array - process memory exhausted
```

**Root Cause:** 
Cached properties accumulating without cleanup in long-running processes.

**Solution:**
```python
# Implement cache size limits
class Entity:
    _cache_size_limit = 100
    
    def _invalidate_caches(self, *cache_names):
        """Invalidate caches with size management"""
        if not cache_names:
            cache_names = self._computed_caches.copy()
        
        for cache_name in cache_names:
            if hasattr(self, f'_{cache_name}_cached'):
                delattr(self, f'_{cache_name}_cached')
        
        self._computed_caches -= set(cache_names)
        
        # Cleanup if too many caches
        if len(self._computed_caches) > self._cache_size_limit:
            self._invalidate_all_caches()
```

**Monitor Memory Usage:**
```python
import psutil
import gc

# Check memory before and after operations
process = psutil.Process()
memory_before = process.memory_info().rss / 1024 / 1024  # MB

# Your operation here
meal.nutri_facts  # Trigger cache

memory_after = process.memory_info().rss / 1024 / 1024  # MB
print(f"Memory usage: {memory_before:.1f}MB -> {memory_after:.1f}MB")

# Force garbage collection if needed
gc.collect()
```

---

## Database Connection Problems

### Problem: Connection refused to PostgreSQL

**Error Message:**
```
psycopg2.OperationalError: connection to server at "localhost", port 5432 failed: Connection refused
Is the server running on that host and accepting TCP/IP connections?
```

**Root Cause:** 
PostgreSQL server not running or connection parameters incorrect.

**Solution Process:**
1. **Check PostgreSQL service status:**
```bash
# On Ubuntu/Debian
sudo systemctl status postgresql

# On macOS with Homebrew
brew services list | grep postgresql

# On Windows
pg_ctl status -D "C:\Program Files\PostgreSQL\14\data"
```

2. **Start PostgreSQL if stopped:**
```bash
# Ubuntu/Debian
sudo systemctl start postgresql

# macOS
brew services start postgresql

# Windows
pg_ctl start -D "C:\Program Files\PostgreSQL\14\data"
```

3. **Verify connection parameters:**
```python
# Check database configuration
import os
from sqlalchemy import create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/menuplanning")
print(f"Database URL: {DATABASE_URL}")

# Test connection
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute("SELECT version();")
        print(f"PostgreSQL version: {result.scalar()}")
except Exception as e:
    print(f"Connection failed: {e}")
```

4. **Create database if missing:**
```bash
# Connect as postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE menuplanning;
CREATE USER menuplanning_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE menuplanning TO menuplanning_user;
\q
```

### Problem: Database migration failures

**Error Message:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Root Cause:** 
Database schema out of sync with migration files.

**Solution:**
1. **Check migration status:**
```bash
poetry run python -m alembic current
poetry run python -m alembic history --verbose
```

2. **Reset database to head (DANGER - development only):**
```bash
# Drop all tables
poetry run python -c "
from src.contexts.seedwork.shared.adapters.db.database import get_database_engine
from sqlalchemy import MetaData
engine = get_database_engine()
metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)
print('All tables dropped')
"

# Run migrations from scratch
poetry run python -m alembic upgrade head
```

3. **Incremental migration (safer):**
```bash
# Check what migrations are pending
poetry run python -m alembic show

# Apply specific migration
poetry run python -m alembic upgrade +1

# Or go to specific revision
poetry run python -m alembic upgrade revision_id
```

4. **Generate new migration for model changes:**
```bash
# Auto-generate migration from model changes
poetry run python -m alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file before running
poetry run python -m alembic upgrade head
```

### Problem: SQLAlchemy session management issues

**Error Message:**
```
sqlalchemy.exc.InvalidRequestError: This Session's transaction has been rolled back due to a previous exception during flush
```

**Root Cause:** 
Session not properly handled after exception or rollback not called.

**Solution:**
```python
# ✅ Proper session management with error handling
from src.contexts.seedwork.shared.adapters.db.database import get_database_session

async def safe_database_operation():
    session = get_database_session()
    try:
        # Your database operations
        meal_repo = MealRepo(session)
        meal = await meal_repo.get("meal-id")
        
        # Modify and save
        meal.update_properties(name="Updated Name")
        await meal_repo.update(meal)
        await session.commit()
        
    except Exception as e:
        # Always rollback on error
        await session.rollback()
        print(f"Database operation failed: {e}")
        raise
    finally:
        # Clean up session
        await session.close()
```

**Session Factory Pattern:**
```python
# Use session factory for proper lifecycle
from contextlib import asynccontextmanager

@asynccontextmanager
async def database_session():
    session = get_database_session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Usage
async def your_operation():
    async with database_session() as session:
        meal_repo = MealRepo(session)
        # Your operations here
        # Commit/rollback handled automatically
```

### Problem: Connection pool exhaustion

**Error Message:**
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 20 overflow 10 reached, connection timed out
```

**Root Cause:** 
Too many connections open simultaneously or connections not properly closed.

**Solution:**
1. **Monitor connection usage:**
```python
from sqlalchemy import text

async def check_connections():
    async with database_session() as session:
        result = await session.execute(text("""
            SELECT 
                state,
                COUNT(*) as connection_count
            FROM pg_stat_activity 
            WHERE datname = 'menuplanning'
            GROUP BY state
            ORDER BY connection_count DESC;
        """))
        
        print("Connection states:")
        for row in result:
            print(f"  {row.state}: {row.connection_count} connections")
```

2. **Configure connection pool:**
```python
# In database configuration
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://user:pass@localhost/db"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,          # Base pool size
    max_overflow=20,       # Additional connections beyond pool_size
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=3600,     # Recycle connections after 1 hour
    pool_pre_ping=True,    # Validate connections before use
)
```

3. **Fix connection leaks:**
```bash
# Find long-running queries
poetry run python -c "
import asyncio
from sqlalchemy import text
from src.contexts.seedwork.shared.adapters.db.database import get_database_session

async def find_leaks():
    async with get_database_session() as session:
        result = await session.execute(text('''
            SELECT 
                pid,
                state,
                query_start,
                state_change,
                query
            FROM pg_stat_activity 
            WHERE datname = current_database()
            AND state != 'idle'
            ORDER BY query_start;
        '''))
        
        for row in result:
            print(f'PID {row.pid}: {row.state} since {row.state_change}')
            print(f'Query: {row.query[:100]}...')
            print('---')

asyncio.run(find_leaks())
"
```

### Problem: Transaction isolation issues

**Error Message:**
```
psycopg2.extensions.TransactionRollbackError: serialization failure
```

**Root Cause:** 
Concurrent transactions conflicting or isolation level too strict.

**Solution:**
```python
# Implement retry logic for serialization failures
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

async def retry_serialization_failure(
    operation: Callable[[], T], 
    max_retries: int = 3,
    delay: float = 0.1
) -> T:
    """Retry operation on serialization failure"""
    
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            if "serialization failure" in str(e) and attempt < max_retries - 1:
                await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                continue
            raise
    
    raise RuntimeError(f"Operation failed after {max_retries} retries")

# Usage
async def concurrent_meal_update(meal_id: str):
    async def update_operation():
        async with database_session() as session:
            meal_repo = MealRepo(session)
            meal = await meal_repo.get(meal_id)
            meal.update_properties(name=f"Updated {datetime.now()}")
            await meal_repo.update(meal)
            return meal
    
    return await retry_serialization_failure(update_operation)
```

---

## Lambda Deployment Issues

### Problem: Import errors in Lambda environment

**Error Message:**
```
Runtime.ImportModuleError: Unable to import module 'lambda_function': No module named 'src'
```

**Root Cause:** 
Lambda package doesn't include source code or PYTHONPATH not set correctly.

**Solution:**
1. **Check Lambda deployment package structure:**
```bash
# Examine deployed package
unzip -l your-lambda-package.zip | head -20

# Should contain:
# src/
# src/contexts/
# lambda_function.py
# dependencies...
```

2. **Fix packaging script:**
```bash
# Correct packaging for Lambda
mkdir lambda-package
cp -r src lambda-package/
cp lambda_function.py lambda-package/
cd lambda-package

# Install dependencies
pip install -r ../requirements.txt -t .

# Create deployment package
zip -r ../lambda-deployment.zip .
```

3. **Add PYTHONPATH to Lambda handler:**
```python
import sys
import os

# Add src to Python path for Lambda
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now imports should work
from contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
```

### Problem: Lambda timeout errors

**Error Message:**
```
Task timed out after 30.00 seconds
```

**Root Cause:** 
Operation taking too long, often due to cold starts or inefficient queries.

**Solution:**
1. **Optimize cold start performance:**
```python
# Module-level imports and initialization
import os
from src.contexts.recipes_catalog.core.bootstrap.container import Container

# Initialize container at module level (outside handler)
container = None

def get_container():
    global container
    if container is None:
        container = Container()
    return container

def lambda_handler(event, context):
    # Container already initialized - faster warm starts
    bus = get_container().bootstrap()
    
    # Check remaining time
    remaining_ms = context.get_remaining_time_in_millis()
    if remaining_ms < 5000:  # Less than 5 seconds left
        return {"statusCode": 408, "body": "Request timeout"}
    
    # Your handler logic
    pass
```

2. **Implement query optimization:**
```python
# Use pagination for large result sets
async def get_meals_paginated(author_id: str, limit: int = 50):
    meal_repo = MealRepo(session)
    
    # Set reasonable limits to prevent timeouts
    if limit > 100:
        limit = 100
    
    results = await meal_repo.query(
        filter={"author_id": author_id},
        limit=limit,
        # Use indexed columns for better performance
        order_by=["created_at"]
    )
    
    return results
```

3. **Add timeout monitoring:**
```python
import time

def lambda_handler(event, context):
    start_time = time.time()
    
    try:
        # Your logic here
        result = process_request(event)
        
        # Log performance
        duration = time.time() - start_time
        print(f"Request processed in {duration:.2f}s")
        
        return {"statusCode": 200, "body": result}
        
    except Exception as e:
        duration = time.time() - start_time
        remaining = context.get_remaining_time_in_millis() / 1000
        
        if duration > 25:  # Close to 30s timeout
            print(f"Near timeout: {duration:.2f}s elapsed, {remaining:.2f}s remaining")
        
        raise
```

### Problem: Lambda environment variable issues

**Error Message:**
```
KeyError: 'DATABASE_URL'
Environment variable DATABASE_URL not found
```

**Root Cause:** 
Environment variables not configured in Lambda function or incorrect variable names.

**Solution:**
1. **Check Lambda environment variables:**
```bash
# Using AWS CLI
aws lambda get-function-configuration --function-name your-function-name --query 'Environment.Variables'

# Should show:
# {
#   "DATABASE_URL": "postgresql://...",
#   "JWT_SECRET": "...",
#   "AWS_REGION": "us-east-1"
# }
```

2. **Add error handling for missing variables:**
```python
import os

def get_env_var(name: str, default: str = None) -> str:
    """Get environment variable with better error messages"""
    value = os.getenv(name, default)
    
    if value is None:
        available_vars = list(os.environ.keys())
        raise ValueError(
            f"Environment variable '{name}' not found. "
            f"Available variables: {available_vars[:10]}..."
        )
    
    return value

# Usage in Lambda
def lambda_handler(event, context):
    try:
        db_url = get_env_var("DATABASE_URL")
        jwt_secret = get_env_var("JWT_SECRET")
        # Process request...
        
    except ValueError as e:
        return {
            "statusCode": 500,
            "body": f"Configuration error: {str(e)}"
        }
```

3. **Set environment variables via AWS CLI:**
```bash
# Update Lambda environment variables
aws lambda update-function-configuration \
    --function-name your-function-name \
    --environment Variables='{
        "DATABASE_URL":"postgresql://user:pass@host:5432/db",
        "JWT_SECRET":"your-jwt-secret-key",
        "LOG_LEVEL":"INFO"
    }'
```

### Problem: Lambda memory and resource limits

**Error Message:**
```
Runtime exited with error: signal: killed
Runtime.ExitError
```

**Root Cause:** 
Lambda function exceeded memory limit or other resource constraints.

**Solution:**
1. **Monitor memory usage:**
```python
import psutil
import gc

def lambda_handler(event, context):
    # Check memory at start
    process = psutil.Process()
    memory_start = process.memory_info().rss / 1024 / 1024  # MB
    
    try:
        # Your processing logic
        result = process_request(event)
        
        # Check memory after processing
        memory_end = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_end - memory_start
        
        print(f"Memory usage: {memory_start:.1f}MB -> {memory_end:.1f}MB (Δ{memory_used:.1f}MB)")
        
        # Force garbage collection if using too much memory
        if memory_end > 400:  # If using > 400MB of 512MB limit
            gc.collect()
            memory_after_gc = process.memory_info().rss / 1024 / 1024
            print(f"After GC: {memory_after_gc:.1f}MB")
        
        return result
        
    except MemoryError:
        return {
            "statusCode": 507,
            "body": "Insufficient memory to process request"
        }
```

2. **Optimize memory usage:**
```python
# Use generators instead of loading all data into memory
async def process_meals_efficiently(author_id: str):
    meal_repo = MealRepo(session)
    
    # Process in batches instead of loading all at once
    batch_size = 10
    offset = 0
    
    while True:
        batch = await meal_repo.query(
            filter={"author_id": author_id},
            limit=batch_size,
            offset=offset
        )
        
        if not batch:
            break
            
        # Process batch
        for meal in batch:
            yield process_single_meal(meal)
            
        offset += batch_size
        
        # Optional: Force garbage collection between batches
        gc.collect()
```

3. **Increase Lambda memory allocation:**
```bash
# Increase memory limit (and proportionally CPU)
aws lambda update-function-configuration \
    --function-name your-function-name \
    --memory-size 1024  # Up from default 128MB
```

### Problem: VPC connectivity issues

**Error Message:**
```
Unable to connect to endpoint: Could not connect to the endpoint URL
```

**Root Cause:** 
Lambda in VPC cannot reach external services or RDS instance.

**Solution:**
1. **Check VPC configuration:**
```bash
# Get Lambda VPC configuration
aws lambda get-function-configuration \
    --function-name your-function-name \
    --query 'VpcConfig'

# Should show subnets and security groups
```

2. **Verify security group rules:**
```bash
# Check security group allows database access
aws ec2 describe-security-groups \
    --group-ids sg-your-lambda-sg \
    --query 'SecurityGroups[0].IpPermissions'

# Should allow outbound port 5432 for PostgreSQL
```

3. **Add NAT Gateway for external access:**
```bash
# Lambda in private subnet needs NAT Gateway or VPC Endpoints
# for external API calls (like AWS services)

# Check route table
aws ec2 describe-route-tables \
    --filters "Name=association.subnet-id,Values=subnet-your-lambda-subnet"
```

4. **Test connectivity from Lambda:**
```python
import socket
import urllib.request

def lambda_handler(event, context):
    # Test database connectivity
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('your-db-host', 5432))
        sock.close()
        
        if result == 0:
            print("Database port 5432 is reachable")
        else:
            print(f"Cannot reach database port 5432: {result}")
            
    except Exception as e:
        print(f"Database connectivity test failed: {e}")
    
    # Test internet connectivity
    try:
        response = urllib.request.urlopen('https://httpbin.org/ip', timeout=5)
        print(f"Internet access: {response.read().decode()}")
    except Exception as e:
        print(f"Internet connectivity test failed: {e}")
    
    return {"statusCode": 200, "body": "Connectivity tests completed"}
```

---

## Quick Reference

### Essential Commands

```bash
# Environment Setup
poetry install                                          # Install dependencies
poetry shell                                           # Activate virtual environment

# Testing
poetry run python -m pytest tests/ -v                 # Run all tests
poetry run python -m pytest tests/contexts/recipes_catalog/core/domain/meal/ -v  # Specific domain tests
poetry run python -m pytest --cov=src --cov-report=term-missing  # Coverage report
poetry run python -m pytest tests/ -k "test_meal" -v  # Run tests matching pattern

# Code Quality
poetry run python -m mypy src/                        # Type checking
poetry run python -m ruff check .                     # Linting
poetry run python -m black . --check                  # Format checking
poetry run python -m isort . --check-only             # Import sorting check

# Database
poetry run python -m alembic current                  # Check migration status
poetry run python -m alembic upgrade head             # Apply migrations
poetry run python -m alembic revision --autogenerate -m "message"  # Generate migration

# Development
poetry run python -c "from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts; print('Import test OK')"
```

### Common File Paths

```bash
# Domain Layer
src/contexts/recipes_catalog/core/domain/meal/root_aggregate/meal.py
src/contexts/recipes_catalog/core/domain/meal/entities/recipe.py
src/contexts/shared_kernel/domain/value_objects/nutri_facts.py

# Repository Layer  
src/contexts/recipes_catalog/core/adapters/meal/repositories/meal_repository.py
src/contexts/products_catalog/core/adapters/repositories/product_repository.py

# API Schemas
src/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/api_meal.py
src/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/create_meal.py

# Lambda Handlers
src/contexts/recipes_catalog/core/adapters/lambda_handlers/commands/create_meal.py
src/contexts/recipes_catalog/core/adapters/lambda_handlers/queries/get_meal.py

# Tests
tests/contexts/recipes_catalog/core/domain/meal/test_meal.py
tests/contexts/recipes_catalog/core/adapters/meal/repositories/test_meal_repository.py
```

### Debugging Commands

```bash
# Check imports
poetry run python -c "
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
print('All imports successful')
"

# Test database connection
poetry run python -c "
from src.contexts.seedwork.shared.adapters.db.database import get_database_engine
engine = get_database_engine()
with engine.connect() as conn:
    result = conn.execute('SELECT version();')
    print(f'Database: {result.scalar()}')
"

# Check test fixtures
poetry run python -m pytest --fixtures tests/contexts/recipes_catalog/core/domain/meal/

# Validate specific test
poetry run python -c "
import tests.contexts.recipes_catalog.core.domain.meal.test_meal_nutrition_facts
print('Test module imports successfully')
"

# Check cache behavior
poetry run python -c "
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
meal = Meal.create_meal('Test', 'author', 'meal-id', 'menu-id')
print('Cache info:', meal.get_cache_info())
"
```

### Performance Monitoring

```bash
# Run performance tests
poetry run python -m pytest tests/performance/ -v --benchmark-only

# Memory profiling (if memory_profiler installed)
poetry run python -m memory_profiler tests/performance/test_memory_usage.py

# Time specific operations
poetry run python -c "
import time
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

start = time.perf_counter()
meal = Meal.create_meal('Perf Test', 'author', 'meal-id', 'menu-id')
nutrition = meal.nutri_facts
elapsed = time.perf_counter() - start
print(f'Meal creation + nutrition: {elapsed:.4f}s')
"
```

### Error Recovery

```bash
# Reset database (DEVELOPMENT ONLY)
poetry run python -c "
from src.contexts.seedwork.shared.adapters.db.database import get_database_engine
from sqlalchemy import MetaData
engine = get_database_engine()
metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)
"
poetry run python -m alembic upgrade head

# Clear pytest cache
rm -rf .pytest_cache
rm -rf **/__pycache__

# Reinstall dependencies
poetry env remove python
poetry install

# Check system health
poetry run python -c "
import sys
print(f'Python: {sys.version}')
import sqlalchemy
print(f'SQLAlchemy: {sqlalchemy.__version__}')
import pytest
print(f'Pytest: {pytest.__version__}')
print('System check complete')
"
```

---

## 🆘 Emergency Procedures

### When Everything Breaks

1. **Check Python environment:**
```bash
which python
poetry env info
poetry check
```

2. **Validate core imports:**
```bash
poetry run python -c "
try:
    from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
    print('✅ NutriFacts import OK')
except Exception as e:
    print(f'❌ NutriFacts import failed: {e}')

try:
    from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
    print('✅ Meal import OK')
except Exception as e:
    print(f'❌ Meal import failed: {e}')
"
```

3. **Test basic functionality:**
```bash
poetry run python -c "
try:
    from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
    meal = Meal.create_meal('Emergency Test', 'user', 'meal-id', 'menu-id')
    print(f'✅ Meal creation OK: {meal.name}')
except Exception as e:
    print(f'❌ Meal creation failed: {e}')
"
```

4. **If all else fails:**
```bash
# Nuclear option - rebuild everything
rm -rf .venv
rm poetry.lock
poetry install
poetry run python -m pytest tests/contexts/recipes_catalog/core/domain/meal/test_meal_nutrition_facts.py -v
```

### Getting Help

- **Check logs:** Look for detailed error messages in test output
- **Isolation testing:** Run single test files to isolate issues  
- **Documentation:** Reference `docs/architecture/quick-start-guide.md` for basics
- **Code patterns:** Check `docs/architecture/pattern-library.md` for examples

Remember: Most issues are import path problems or database connectivity. Start with the basics and work up to complex scenarios. 