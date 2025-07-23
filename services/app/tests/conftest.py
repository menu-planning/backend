import gc
import os
import tracemalloc
from contextlib import suppress


from dotenv import dotenv_values
import pytest
from tests.utils.counter_manager import reset_all_counters

pytestmark = pytest.mark.anyio

def load_env_variables():
    """Load environment variables from .env file before any imports."""
    env_vars = dotenv_values(".env.test")
    for k, v in env_vars.items():
        if v is not None:
            os.environ[k] = v

# Load environment variables immediately when conftest.py is imported
load_env_variables()

@pytest.fixture(autouse=True, scope="function")
def reset_all_test_counters():
    """
    Reset all counters before each test for complete isolation.
    
    This fixture ensures that all global state used by data factories is reset
    before and after each test, preventing test pollution between test files.
    
    Uses centralized counter management for consistency and maintainability.
    """
    # Reset all counters before test execution
    reset_all_counters()
    
    yield
    
    # Reset all counters after test execution for extra safety
    reset_all_counters()

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def memory_tracer(anyio_backend):
    tracemalloc.start()
    tracemalloc.clear_traces()

    filters = (
        # tracemalloc.Filter(True, aiormq.__file__),
        # tracemalloc.Filter(True, pamqp.__file__),
        # tracemalloc.Filter(True, aio_pika.__file__),
    )

    snapshot_before = tracemalloc.take_snapshot().filter_traces(filters)

    try:
        yield

        with suppress(Exception):
            gc.collect()

        snapshot_after = tracemalloc.take_snapshot().filter_traces(filters)

        top_stats = snapshot_after.compare_to(
            snapshot_before,
            "lineno",
            cumulative=True,
        )

        assert not top_stats
    finally:
        tracemalloc.stop()


def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", help="run e2e tests")
    parser.addoption("--integration", action="store_true", help="run integration tests")

def pytest_runtest_setup(item):
    """Skip tests based on markers and CLI options."""
    if "e2e" in item.keywords and not item.config.getvalue("e2e"):
        pytest.skip("need --e2e option to run")
    if "integration" in item.keywords and not item.config.getvalue("integration"):
        pytest.skip("need --integration option to run")

