"""AWS Lambda handler for querying recipes."""

from typing import TYPE_CHECKING, Any

import anyio
from pydantic import TypeAdapter
from src.config.app_config import get_app_settings
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities import (
    api_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_filter import (
    ApiRecipeFilter,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.shared_kernel.middleware.auth.authentication import (
    recipes_aws_auth_middleware,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.lambda_helpers import LambdaHelpers
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import get_logger, generate_correlation_id

from ..api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

logger = get_logger(__name__)


container = Container()

# Import the API schema classes
ApiRecipe = api_recipe.ApiRecipe
RecipeListAdapter = TypeAdapter(list[ApiRecipe])


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="recipes_catalog.fetch_recipe",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
    ),
    recipes_aws_auth_middleware(),
    aws_lambda_exception_handler_middleware(
        name="fetch_recipe_exception_handler",
        logger_name="recipes_catalog.fetch_recipe.errors",
    ),
    timeout=30.0,
    name="fetch_recipe_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle GET /recipes for recipe querying with filters.

    Request:
        Query: filters (optional) - ApiRecipeFilter schema with pagination, sorting, and search criteria
        Auth: AWS Cognito JWT with valid session

    Responses:
        200: List of recipes matching criteria returned as JSON
        400: Invalid filter parameters
        401: Unauthorized (handled by middleware)
        500: Internal server error (handled by middleware)

    Idempotency:
        Yes. Multiple calls with same filters return same result.

    Notes:
        Maps to Recipe repository query() method and translates errors to HTTP codes.
        Default limit: 50, default sort: -updated_at (newest first).
        User-specific tag filtering applied automatically.
    """
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    filters = LambdaHelpers.process_query_filters_from_aws_event(
        event=event,
        filter_schema_class=ApiRecipeFilter,
        use_multi_value=True,
        default_limit=50,
        default_sort="-updated_at",
    )

    # Apply user-specific tag filtering for recipes
    if current_user:
        if filters.get("tags"):
            filters["tags"] = [
                (k, v, current_user.id) for k, vs in filters["tags"].items() for v in vs
            ]
        if filters.get("tags_not_exists"):
            filters["tags_not_exists"] = [
                (k, v, current_user.id)
                for k, vs in filters["tags_not_exists"].items()
                for v in vs
            ]

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        # Business context: Query execution with final filters
        result = await uow.recipes.query(filters=filters)

    # Convert domain recipes to API recipes
    api_recipes = []
    for recipe in result:
        api_recipe = ApiRecipe.from_domain(recipe)
        api_recipes.append(api_recipe)

    # Serialize API recipes
    response_body = RecipeListAdapter.dump_json(api_recipes)

    return {
        "statusCode": 200,
        "headers": API_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entry point for recipe querying.

    Args:
        event: AWS Lambda event with HTTP request details
        context: AWS Lambda execution context

    Returns:
        HTTP response with status code, headers, and body

    Notes:
        Generates correlation ID and delegates to async handler.
        Wraps async execution in anyio runtime.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)


event = {
    "resource": "/recipes",
    "path": "/dev/recipes",
    "httpMethod": "GET",
    "headers": {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        "Authorization": "eyJraWQiOiJDb1c5UEMxWUZxa01pS2tZTzFIejU1YVhJMkxyOCtaaGNyK0h6Z29MeU9nPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJhMzljYmFlYS0yMDMxLTcwODEtZTFiOC03NmY0Y2FiZGExYjMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnNhLWVhc3QtMS5hbWF6b25hd3MuY29tXC9zYS1lYXN0LTFfbkRwcTVhT2RJIiwiY29nbml0bzp1c2VybmFtZSI6ImEzOWNiYWVhLTIwMzEtNzA4MS1lMWI4LTc2ZjRjYWJkYTFiMyIsIm9yaWdpbl9qdGkiOiJjNTM5OGI5NS1kZDgwLTRhNTMtOTg2Zi03NzYzOGRlZTJkNDciLCJhdWQiOiI2bjYwM3Vzc3BkZm1icm5uNDhqODVycHBpMiIsImV2ZW50X2lkIjoiYjEzYTk0NTgtZDYwZC00MWJkLTkzOGUtNDMwYmM3YjkzMzZhIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NTc0MzA0MzMsImV4cCI6MTc1NzYzNTA5NiwiaWF0IjoxNzU3NjMxNDk2LCJqdGkiOiI1MDBiMjMzOS04MzE1LTQ1ODUtODAzZC0yNmUxMGU0YTBmZWQiLCJlbWFpbCI6ImpvYXF1aW0uYWx2ZXNAbXV6eWF0aG9tZS5jb20uYnIifQ.BqzFruP2yx4oWZYUf-bnI0ycuJXxZ1MoS6bv7H-cr35kK8ApzXf1agOi1LVqg1v30KcuseQBgCLJpKqg6cPG2NmR0gCkpDAf9PZTEoemxIX6dSvakYygyIziHwm57csVuLkZl7Fh8cQX-PfjsEM7zaiNKc05FSADvyAUk1HKJqBhqdBj8mo6-DxfPxqrV-DBD_mLdJx_O4EivXknH_to94KPTfGKOqfEDiDLKa0yUxEKlBwvddaVcWRYOVTByUJ2X68bu8jQ3egcnXvvdzpUmZpH1jROQQGHZn9P3LXFWTyOQXtlkS36ZjutNFwdLhaqklQj9nnc1jEnvjEi5HIorg",
        "content-type": "application/json",
        "Host": "api.vlep.com.br",
        "origin": "http://localhost:8000",
        "priority": "u=1, i",
        "referer": "http://localhost:8000/",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "X-Amzn-Trace-Id": "Root=1-68c35ea1-1abadf3a6d850202707fd7c1",
        "X-Forwarded-For": "187.0.49.191",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https",
    },
    "multiValueHeaders": {
        "accept": ["*/*"],
        "accept-encoding": ["gzip, deflate, br, zstd"],
        "accept-language": ["en-US,en;q=0.9"],
        "Authorization": [
            "eyJraWQiOiJDb1c5UEMxWUZxa01pS2tZTzFIejU1YVhJMkxyOCtaaGNyK0h6Z29MeU9nPSIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJhMzljYmFlYS0yMDMxLTcwODEtZTFiOC03NmY0Y2FiZGExYjMiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnNhLWVhc3QtMS5hbWF6b25hd3MuY29tXC9zYS1lYXN0LTFfbkRwcTVhT2RJIiwiY29nbml0bzp1c2VybmFtZSI6ImEzOWNiYWVhLTIwMzEtNzA4MS1lMWI4LTc2ZjRjYWJkYTFiMyIsIm9yaWdpbl9qdGkiOiJjNTM5OGI5NS1kZDgwLTRhNTMtOTg2Zi03NzYzOGRlZTJkNDciLCJhdWQiOiI2bjYwM3Vzc3BkZm1icm5uNDhqODVycHBpMiIsImV2ZW50X2lkIjoiYjEzYTk0NTgtZDYwZC00MWJkLTkzOGUtNDMwYmM3YjkzMzZhIiwidG9rZW5fdXNlIjoiaWQiLCJhdXRoX3RpbWUiOjE3NTc0MzA0MzMsImV4cCI6MTc1NzYzNTA5NiwiaWF0IjoxNzU3NjMxNDk2LCJqdGkiOiI1MDBiMjMzOS04MzE1LTQ1ODUtODAzZC0yNmUxMGU0YTBmZWQiLCJlbWFpbCI6ImpvYXF1aW0uYWx2ZXNAbXV6eWF0aG9tZS5jb20uYnIifQ.BqzFruP2yx4oWZYUf-bnI0ycuJXxZ1MoS6bv7H-cr35kK8ApzXf1agOi1LVqg1v30KcuseQBgCLJpKqg6cPG2NmR0gCkpDAf9PZTEoemxIX6dSvakYygyIziHwm57csVuLkZl7Fh8cQX-PfjsEM7zaiNKc05FSADvyAUk1HKJqBhqdBj8mo6-DxfPxqrV-DBD_mLdJx_O4EivXknH_to94KPTfGKOqfEDiDLKa0yUxEKlBwvddaVcWRYOVTByUJ2X68bu8jQ3egcnXvvdzpUmZpH1jROQQGHZn9P3LXFWTyOQXtlkS36ZjutNFwdLhaqklQj9nnc1jEnvjEi5HIorg"
        ],
        "content-type": ["application/json"],
        "Host": ["api.vlep.com.br"],
        "origin": ["http://localhost:8000"],
        "priority": ["u=1, i"],
        "referer": ["http://localhost:8000/"],
        "sec-ch-ua": [
            '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"'
        ],
        "sec-ch-ua-mobile": ["?0"],
        "sec-ch-ua-platform": ['"Linux"'],
        "sec-fetch-dest": ["empty"],
        "sec-fetch-mode": ["cors"],
        "sec-fetch-site": ["cross-site"],
        "User-Agent": [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        ],
        "X-Amzn-Trace-Id": ["Root=1-68c35ea1-1abadf3a6d850202707fd7c1"],
        "X-Forwarded-For": ["187.0.49.191"],
        "X-Forwarded-Port": ["443"],
        "X-Forwarded-Proto": ["https"],
    },
    "queryStringParameters": {"calories_lte": "300", "sort": "-updated_at"},
    "multiValueQueryStringParameters": {
        "calories_lte": ["300"],
        "sort": ["-updated_at"],
    },
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "edv253",
        "authorizer": {
            "claims": {
                "sub": "a39cbaea-2031-7081-e1b8-76f4cabda1b3",
                "email_verified": "true",
                "iss": "https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_nDpq5aOdI",
                "cognito:username": "a39cbaea-2031-7081-e1b8-76f4cabda1b3",
                "origin_jti": "c5398b95-dd80-4a53-986f-77638dee2d47",
                "aud": "6n603usspdfmbrnn48j85rppi2",
                "event_id": "b13a9458-d60d-41bd-938e-430bc7b9336a",
                "token_use": "id",
                "auth_time": "1757430433",
                "exp": "Thu Sep 11 23:58:16 UTC 2025",
                "iat": "Thu Sep 11 22:58:16 UTC 2025",
                "jti": "500b2339-8315-4585-803d-26e10e4a0fed",
                "email": "joaquim.alves@muzyathome.com.br",
            }
        },
        "resourcePath": "/recipes",
        "httpMethod": "GET",
        "extendedRequestId": "Qwu5PHcTGjQEUYw=",
        "requestTime": "11/Sep/2025:23:43:29 +0000",
        "path": "/dev/recipes",
        "accountId": "851725364156",
        "protocol": "HTTP/1.1",
        "stage": "dev",
        "domainPrefix": "api",
        "requestTimeEpoch": 1757634209174,
        "requestId": "5f9ca3f9-4650-4643-8afa-6a44274554fc",
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "sourceIp": "187.0.49.191",
            "principalOrgId": None,
            "accessKey": None,
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "user": None,
        },
        "domainName": "api.vlep.com.br",
        "deploymentId": "9ogiut",
        "apiId": "f342y4x349",
    },
    "body": None,
    "isBase64Encoded": False,
}
