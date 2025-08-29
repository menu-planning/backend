import time
from typing import Any, Generic, TypeVar, cast

import src.contexts.iam.core.endpoints.internal.get as iam_api
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects import (
    ApiSeedUser,
)
from src.logging.logger import logger

# Type variable for the specific ApiUser implementation
TApiUser = TypeVar("TApiUser", bound=ApiSeedUser)

# Constants for HTTP status codes
HTTP_OK = 200


class BaseIAMProvider(Generic[TApiUser]):
    """
    Base class for IAM providers that abstracts common logic across different contexts.

    This class eliminates code duplication by providing a generic implementation that
    can be parameterized with context-specific ApiUser types and caller contexts.

    Type Parameters:
        TApiUser: The specific ApiUser implementation for the
                  context (must extend ApiSeedUser)

    Usage:
        class ProductsIAMProvider(BaseIAMProvider[ApiUser]):
            def __init__(self):
                super().__init__(
                    api_user_class=ApiUser,
                    caller_context="products_catalog"
                )
    """

    def __init__(self, api_user_class: type[TApiUser], caller_context: str):
        """
        Initialize the IAM provider with context-specific configuration.

        Args:
            api_user_class: The specific ApiUser class for this context
            caller_context: The context name to pass to the IAM API
        """
        self.api_user_class = api_user_class
        self.caller_context = caller_context

    def _handle_invalid_response_body_type(self, response_body: Any) -> None:
        """Handle invalid response body type by raising appropriate exception."""
        error_msg = f"Invalid response body type: {type(response_body)}"
        raise TypeError(error_msg)

    async def get(self, user_id: str) -> dict[str, Any]:
        """
        Get user information from the IAM service.

        Args:
            user_id: The user ID to retrieve

        Returns:
            Dict containing either:
            - Success: {"statusCode": 200, "body": User domain object}
            - Error: {"statusCode": <error_code>, "body": <error_message>}

        Raises:
            Exception: If an unexpected error occurs during the IAM call
        """
        start_time = time.time()
        logger.info(
            f"BaseIAMProvider.get() called for user_id: {user_id}, "
            f"context: {self.caller_context}"
        )

        try:
            logger.debug(
                f"Calling internal IAM API with caller_context='{self.caller_context}' "
                "for user: {user_id}"
            )
            response = await iam_api.get(
                entity_id=user_id, caller_context=self.caller_context
            )

            elapsed_time = time.time() - start_time
            logger.debug(
                f"Internal IAM API response received in {elapsed_time:.3f}s - "
                f"Status: {response.get('statusCode')}, User: {user_id}"
            )

            if response.get("statusCode") != HTTP_OK:
                logger.warning(
                    f"IAM API returned non-200 status for user {user_id}: "
                    f"{response.get('statusCode')} - Body: {response.get('body')}"
                )
                return response

            logger.debug(
                f"Converting IAM response to domain user object for user: {user_id}"
            )
            response_body = response["body"]
            if not isinstance(response_body, str):
                logger.error(
                    f"Unexpected response body type for user {user_id}: "
                    f"{type(response_body)} - Expected string"
                )
                self._handle_invalid_response_body_type(response_body)

            # At this point, response_body is guaranteed to be a string
            response_body_str: str = cast("str", response_body)
            user = self.api_user_class.model_validate_json(
                response_body_str
            ).to_domain()

            logger.debug(
                f"User from IAMProvider - ID: {user.id}, Roles count: "
                f"{len(user.roles) if user.roles else 0}"
            )
            logger.info(
                f"BaseIAMProvider.get() completed successfully for user: "
                f"{user_id} in {elapsed_time:.3f}s, context: {self.caller_context}"
            )

        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"BaseIAMProvider.get() failed for user {user_id} after "
                f"{elapsed_time:.3f}s - Error: {type(e).__name__}: {e!s}, "
                f"context: {self.caller_context}"
            )
            raise
        else:
            return {"statusCode": HTTP_OK, "body": user}
