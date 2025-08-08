"""
Create Form Lambda Handler

Lambda endpoint for creating new onboarding forms with proper authorization and validation.
"""

from typing import Any, Dict
import anyio
from pydantic import ValidationError

from src.contexts.client_onboarding.core.bootstrap.container import Container
from src.contexts.client_onboarding.core.adapters.api_schemas.commands.form_management_commands import (
    CreateFormCommand,
)
# Note: No middleware imports needed beyond logging for this thin handler
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
from src.contexts.client_onboarding.core.domain.commands.setup_onboarding_form import (
    SetupOnboardingFormCommand,
)

from .CORS_headers import CORS_headers

container = Container()
logging_middleware = create_api_logging_middleware()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function handler to create a new onboarding form.
    """
    async with logging_middleware.log_request_response(event, context) as operation_context:
        logger.debug(f"Create form event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
        
        # Validate user authentication and get user object
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Authorization context (not needed here; handled in domain layer)
        
        # Parse and validate request body
        try:
            body = LambdaHelpers.extract_request_body(event, parse_json=True)
            create_command = CreateFormCommand.model_validate(body)
            logger.debug(f"Parsed create form command: {create_command}")
        except ValidationError as e:
            logger.warning(f"Invalid create form request body: {e}")
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": f'{{"message": "Invalid request body", "errors": {e.errors()}}}',
            }
        except Exception as e:
            logger.error(f"Failed to parse request body: {e}")
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": '{"message": "Invalid request body format"}',
            }

        # Delegate business logic to command handler via MessageBus
        bus: MessageBus = container.bootstrap()
        try:
            cmd = SetupOnboardingFormCommand(
                user_id=current_user.id,
                typeform_id=create_command.typeform_id,
                webhook_url=str(create_command.webhook_url),
                auto_activate=bool(create_command.auto_activate),
            )
            await bus.handle(cmd)
            logger.info(
                f"Successfully dispatched setup command for user {current_user.id}, form {create_command.typeform_id}"
            )
        except Exception as e:
            logger.error(f"Failed to set up onboarding form: {e}")
            return {
                "statusCode": 500,
                "headers": CORS_headers,
                "body": '{"message": "Internal server error during form setup"}',
            }

        return {
            "statusCode": 201,
            "headers": CORS_headers,
            "body": '{"message": "Form setup initiated successfully"}',
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda function handler entry point for creating forms."""
    generate_correlation_id()
    return anyio.run(async_handler, event, context) 