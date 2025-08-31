import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.iam.core.domain.root_aggregate.user import User
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
import src.contexts.iam.core.endpoints.internal.get as internal
from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.iam.core import Container, Permission
from src.contexts.iam.core.adapters import ApiAssignRoleToUser, ApiUser
from src.contexts.seedwork import lambda_exception_handler
from src.logging.logger import generate_correlation_id, set_correlation_id, structlog_logger

# Constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle role assignment request asynchronously."""
    logger = structlog_logger("iam.assign_role")
    try:
        user_id = event["pathParameters"]["id"]
    except KeyError:
        logger.error(
            "Missing required user ID in path parameters",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            error_type="validation_error",
            error_category="missing_parameter",
            event_path_parameters=event.get("pathParameters", {}),
            http_method=event.get("httpMethod"),
            resource_path=event.get("resource")
        )
        return {
            "statusCode": HTTP_BAD_REQUEST,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User ID not found in path parameters."}),
        }
    try:
        body = json.loads(event.get("body", ""))
    except json.JSONDecodeError as e:
        logger.error(
            "Invalid JSON in request body",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            error_type="validation_error",
            error_category="invalid_json",
            json_error=str(e),
            raw_body=event.get("body", "")
        )
        return {
            "statusCode": HTTP_BAD_REQUEST,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid JSON in request body."}),
        }

    try:
        authorizer_context = event["requestContext"]["authorizer"]
        caller_user_id = authorizer_context.get("claims").get("sub")
    except (KeyError, AttributeError) as e:
        logger.error(
            "Missing or invalid authorization context",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            error_type="authorization_error",
            error_category="missing_auth_context",
            auth_error=str(e),
            request_context=event.get("requestContext", {})
        )
        return {
            "statusCode": HTTP_FORBIDDEN,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid authorization context."}),
        }
    
    logger.info(
        "Processing role assignment request",
        context="iam",
        operation="assign_role",
        component="assign_role_lambda",
        caller_user_id=caller_user_id,
        target_user_id=user_id,
        request_method=event.get("httpMethod"),
        resource_path=event.get("resource"),
        status="started"
    )
    
    logger.debug(
        "Validating caller user permissions",
        context="iam",
        operation="assign_role",
        component="assign_role_lambda",
        caller_user_id=caller_user_id,
        target_user_id=user_id,
        validation_step="user_lookup"
    )
    
    response: dict = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != HTTP_OK:
        logger.warning(
            "Caller user validation failed - user not found or inactive",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            validation_status_code=response.get("statusCode"),
            validation_response_body=response.get("body"),
            status="validation_failed"
        )
        return response

    try:
        current_user: User = ApiUser(**body).to_domain()
    except Exception as e:
        logger.error(
            "Failed to parse user data from request body",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            error_type="validation_error",
            error_category="user_data_parsing",
            parsing_error=str(e),
            request_body_keys=list(body.keys()) if isinstance(body, dict) else "non_dict"
        )
        return {
            "statusCode": HTTP_BAD_REQUEST,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Invalid user data in request body."}),
        }
    
    logger.debug(
        "Checking user permissions for role assignment",
        context="iam",
        operation="assign_role",
        component="assign_role_lambda",
        caller_user_id=caller_user_id,
        target_user_id=user_id,
        required_permission="MANAGE_ROLES",
        validation_step="permission_check"
    )
    
    if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
        logger.warning(
            "Access denied - insufficient permissions for role assignment",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            security_event=True,
            event_type="unauthorized_access_attempt",
            resource="role_assignment",
            required_permission="MANAGE_ROLES",
            user_permissions=[p.value for p in current_user.permissions] if hasattr(current_user, 'permissions') else [],
            status="permission_denied"
        )
        return {
            "statusCode": HTTP_FORBIDDEN,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User does not have enough privileges."}),
        }

    logger.debug(
        "Preparing role assignment command",
        context="iam",
        operation="assign_role",
        component="assign_role_lambda",
        caller_user_id=caller_user_id,
        target_user_id=user_id,
        processing_step="command_preparation"
    )
    
    try:
        api = ApiAssignRoleToUser(user_id=user_id, **body)
        cmd = api.to_domain()
        bus: MessageBus = Container().bootstrap()
        
        logger.debug(
            "Executing role assignment command",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            processing_step="command_execution"
        )
        
        await bus.handle(cmd)
        
        logger.info(
            "Role assignment completed successfully",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            role_data={k: v for k, v in body.items() if k not in ["password", "secret", "token"]},  # Exclude sensitive data
            status="success"
        )
    except Exception as e:
        logger.error(
            "Role assignment failed during command execution",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            caller_user_id=caller_user_id,
            target_user_id=user_id,
            error_type="command_execution_error",
            error_category="business_logic_failure",
            execution_error=str(e),
            status="failed"
        )
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during role assignment."}),
        }
    
    return {
        "statusCode": HTTP_OK,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Role assigned successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to assign roles to a user.
    
    Args:
        event: AWS Lambda event containing request data
        context: AWS Lambda context object

    Returns:
        HTTP response dictionary with status code, headers, and body
    """
    correlation_id = generate_correlation_id()
    set_correlation_id(correlation_id)
    
    logger = structlog_logger("iam.assign_role.handler")
    
    logger.info(
        "Role assignment Lambda handler initiated",
        context="iam",
        operation="assign_role",
        component="assign_role_lambda",
        correlation_id=correlation_id,
        function_name=getattr(context, "function_name", "unknown"),
        function_version=getattr(context, "function_version", "unknown"),
        request_id=getattr(context, "aws_request_id", "unknown"),
        remaining_time_ms=getattr(context, "get_remaining_time_in_millis", lambda: 0)(),
        memory_limit_mb=getattr(context, "memory_limit_in_mb", "unknown"),
        http_method=event.get("httpMethod"),
        resource_path=event.get("resource"),
        stage=event.get("requestContext", {}).get("stage"),
        status="handler_started"
    )
    
    try:
        result = anyio.run(async_handler, event, context)
        
        logger.info(
            "Role assignment Lambda handler completed",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            correlation_id=correlation_id,
            response_status_code=result.get("statusCode"),
            status="handler_completed"
        )
        
        return result
    except Exception as e:
        logger.error(
            "Role assignment Lambda handler failed with unhandled exception",
            context="iam",
            operation="assign_role",
            component="assign_role_lambda",
            correlation_id=correlation_id,
            error_type="unhandled_exception",
            error_category="lambda_handler_failure",
            handler_error=str(e),
            status="handler_failed"
        )
        raise
