"""
Delete Form Lambda Handler

Lambda endpoint for deleting onboarding forms with proper authorization and validation.
"""

from typing import Any, Dict
import anyio

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.form_management_commands import (
    DeleteFormCommand,
)

from src.contexts.client_onboarding.core.adapters.middleware.logging_middleware import (
    create_api_logging_middleware,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id
from src.contexts.client_onboarding.core.adapters.internal_providers.iam.iam_provider_api_for_client_onboarding import (
    IAMProvider,
)
from src.contexts.client_onboarding.core.domain.commands.delete_onboarding_form import (
    DeleteOnboardingFormCommand,
)

from .CORS_headers import CORS_headers

container = Container()
logging_middleware = create_api_logging_middleware()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to delete an onboarding form.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        logger.debug(f"Delete form event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
        
        # Validate user authentication and get user object
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Extract and validate form_id from path parameters
        form_id_raw = event.get("pathParameters", {}).get("form_id")
        if not form_id_raw:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Form ID is required in path parameters"}',
            }

        try:
            form_id = int(form_id_raw)
        except Exception:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Invalid form ID format"}',
            }

        # Delegate business logic to command handler via MessageBus
        bus: MessageBus = container.bootstrap()
        try:
            cmd = DeleteOnboardingFormCommand(
                user_id=current_user.id, form_id=form_id
            )
            await bus.handle(cmd)
            logger.info(f"Successfully dispatched delete command for form {form_id} by user {current_user.id}")
        except Exception as e:
            logger.error(f"Failed to delete form: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during form deletion"}',
            }

        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": '{"message": "Form deleted successfully"}',
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler entry point for deleting forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context) 