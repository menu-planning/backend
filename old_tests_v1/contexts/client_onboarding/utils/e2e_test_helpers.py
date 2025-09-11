"""
E2E Test Helper Utilities.

Reusable setup and teardown functions for client onboarding e2e tests
to ensure proper data isolation and consistent test environment setup.
"""

from tests.contexts.client_onboarding.fakes.fake_unit_of_work import (
    FakeUnitOfWork,
)
from tests.utils.counter_manager import reset_all_counters


def setup_e2e_test_environment():
    """
    Setup clean test environment for e2e tests.

    This function provides:
    - Clean fake repository state
    - Reset counter managers
    - Fresh UoW instance

    Returns:
        FakeUnitOfWork: Fresh unit of work instance with clean state
    """
    # Reset all shared data between tests
    FakeUnitOfWork.reset_all_data()

    # Reset counter managers for deterministic IDs
    reset_all_counters()

    # Return fresh UoW instance
    return FakeUnitOfWork()


def teardown_e2e_test_environment():
    """
    Cleanup after e2e test execution.

    Ensures no state leaks between tests.
    """
    # Reset all shared data again for safety
    FakeUnitOfWork.reset_all_data()
    reset_all_counters()
