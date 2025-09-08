import time
from typing import Any, cast

import src.contexts.iam.core.internal_endpoints.get as iam_api
from src.contexts.seedwork.adapters.api_schemas.value_objects.api_seed_user import (
    ApiSeedUser,
)
from src.logging.logger import StructlogFactory

# Constants for HTTP status codes
HTTP_OK = 200


class BaseIAMProvider[TApiUser: ApiSeedUser]:
    """Base class for IAM providers that abstracts common logic across contexts.

    This class eliminates code duplication by providing a generic implementation that
    can be parameterized with context-specific ApiUser types and caller contexts.
    It handles the common patterns of IAM service communication, error handling,
    and response processing.

    Type Parameters:
        TApiUser: The specific ApiUser implementation for the context
                  (must extend ApiSeedUser)

    Args:
        api_user_class: The specific ApiUser class for this context
        caller_context: The context name to pass to the IAM API

    Example:
        ```python
        class ProductsIAMProvider(BaseIAMProvider[ApiUser]):
            def __init__(self):
                super().__init__(
                    api_user_class=ApiUser,
                    caller_context="products_catalog"
                )
        ```

    Features:
        - Generic user retrieval from IAM service
        - Automatic response validation and error handling
        - Performance monitoring and logging
        - Type-safe user conversion and validation
    """

    def __init__(self, api_user_class: type[TApiUser], caller_context: str):
        """Initialize the IAM provider with context-specific configuration.

        Args:
            api_user_class: The specific ApiUser class for this context
            caller_context: The context name to pass to the IAM API
        """
        self.api_user_class = api_user_class
        self.caller_context = caller_context
        self._logger = StructlogFactory.get_logger("base_iam_provider")

    def _handle_invalid_response_body_type(self, response_body: Any) -> None:
        """Handle invalid response body type by raising appropriate exception.

        Args:
            response_body: The response body that failed type validation

        Raises:
            TypeError: Always raised with descriptive error message
        """
        error_msg = f"Invalid response body type: {type(response_body)}"
        raise TypeError(error_msg)

    async def get(self, user_id: str) -> dict[str, Any]:
        """Get user information from the IAM service.

        This method retrieves user data from the IAM service, validates the
        response, and converts it to the appropriate domain object. It includes
        comprehensive error handling, performance monitoring, and logging.

        Args:
            user_id: The user ID to retrieve

        Returns:
            Dict containing either:
                - Success: {"statusCode": 200, "body": User domain object}
                - Error: {"statusCode": <error_code>, "body": <error_message>}

        Raises:
            Exception: If an unexpected error occurs during the IAM call

        Side Effects:
            - Logs operation start, success, and error conditions
            - Monitors performance and response times
            - Tracks correlation IDs for debugging
        """
        start_time = time.time()

        self._logger.info(
            "Retrieving user from IAM service",
            user_id=user_id,
            caller_context=self.caller_context,
            operation="iam_get_user",
        )

        try:
            response = await iam_api.get(id=user_id, caller_context=self.caller_context)

            elapsed_time = time.time() - start_time

            if response.get("statusCode") != HTTP_OK:
                self._logger.warning(
                    "IAM service returned error response",
                    user_id=user_id,
                    status_code=response.get("statusCode"),
                    error_body=response.get("body"),
                    elapsed_time_ms=round(elapsed_time * 1000, 2),
                    caller_context=self.caller_context,
                )
                return response

            response_body = response["body"]
            if not isinstance(response_body, str):
                self._logger.error(
                    "Invalid response body type from IAM service",
                    user_id=user_id,
                    expected_type="str",
                    actual_type=type(response_body).__name__,
                    caller_context=self.caller_context,
                )
                self._handle_invalid_response_body_type(response_body)

            # At this point, response_body is guaranteed to be a string
            response_body_str: str = cast("str", response_body)
            user = self.api_user_class.model_validate_json(
                response_body_str
            ).to_domain()

            self._logger.info(
                "Successfully retrieved and converted user from IAM service",
                user_id=user_id,
                roles_count=len(user.roles) if user.roles else 0,
                elapsed_time_ms=round(elapsed_time * 1000, 2),
                caller_context=self.caller_context,
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            self._logger.error(
                "Failed to retrieve user from IAM service",
                user_id=user_id,
                error_type=type(e).__name__,
                error_message=str(e),
                elapsed_time_ms=round(elapsed_time * 1000, 2),
                caller_context=self.caller_context,
                exc_info=True,
            )
            raise
        else:
            return {"statusCode": HTTP_OK, "body": user}
