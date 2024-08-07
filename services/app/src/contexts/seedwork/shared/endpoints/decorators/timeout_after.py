import functools
import json
from typing import Any, Callable

from anyio import fail_after
from pydantic_core import ValidationError
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)


def timeout_after(timeout: int = 10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with fail_after(timeout):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def lambda_exception_handler(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return await func(event, context)
        except EntityNotFoundException as e:
            return {"statusCode": 404, "body": json.dumps({"detail": str(e)})}
        except MultipleEntitiesFoundException as e:
            return {"statusCode": 409, "body": json.dumps({"detail": str(e)})}
        except TimeoutError as e:
            return {
                "statusCode": 408,
                "body": json.dumps(
                    {"detail": "Request processing time exceeded limit"}
                ),
            }
        except ValidationError as e:
            return {"statusCode": 422, "body": json.dumps({"detail": str(e)})}
        except ValueError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"detail": f"Error processing data: {str(e)}"}),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"detail": f"An unexpected error occurred: {str(e)}"}
                ),
            }

    return wrapper


COGNITO_REGION = "sa-east-1"
USER_POOL_ID = "YOUR_USER_POOL_ID"
COGNITO_CLIENT_ID = "YOUR_CLIENT_ID"


# Fetch JWKS from the Cognito User Pool
def get_cognito_jwks() -> Dict[str, Any]:
    jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"
    response = httpx.get(jwks_url)
    response.raise_for_status()
    return response.json()


JWKS = get_cognito_jwks()


def verify_cognito_token(token: str) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
        kid = header["kid"]
        keys = {key["kid"]: key for key in JWKS["keys"]}

        if kid not in keys:
            return {"status_code": 401, "body": "Token key not recognized"}

        key = keys[kid]
        rsa_key = {"kty": key["kty"], "e": key["e"], "n": key["n"]}

        decoded_token = jwt.decode(
            token,
            key=rsa_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}",
        )
        return {"status_code": 200, "body": decoded_token}
    except jwt.ExpiredSignatureError:
        return {"status_code": 401, "body": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"status_code": 401, "body": "Invalid token"}


def require_auth(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if request is None or "Authorization" not in request.headers:
            return {"status_code": 401, "body": "Authorization token required"}

        token = request.headers["Authorization"].replace("Bearer ", "")
        verification_result = verify_cognito_token(token)

        if verification_result["status_code"] != 200:
            return verification_result

        # Attach the user information to kwargs if needed
        kwargs["user"] = verification_result["body"]
        return func(*args, **kwargs)

    return wrapper
