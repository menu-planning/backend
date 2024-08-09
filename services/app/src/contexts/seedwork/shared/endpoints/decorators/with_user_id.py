from functools import wraps
from typing import Any

import jwt
from jwt import PyJWKClient
from src.logging.logger import logger

COGNITO_REGION = "sa-east-1"
USER_POOL_ID = "sa-east-1_xrATmGst3"
COGNITO_CLIENT_ID = "lrbucr34nb50q6otf123o5a7f"

# URL to fetch the JWKS (JSON Web Key Set)
jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"


def verify_cognito_token(token: str) -> dict[str, Any]:
    try:
        # Create a JWK client from the JWKS URL
        jwk_client = PyJWKClient(jwks_url)

        # Get the signing key for the given token
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        # Decode the JWT using the signing key
        decoded_token = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{USER_POOL_ID}",
        )
        return {"status_code": 200, "body": decoded_token}
    except jwt.ExpiredSignatureError:
        return {"status_code": 401, "body": "Token has expired"}
    except jwt.InvalidTokenError as e:
        return {"status_code": 401, "body": f"Invalid token: {str(e)}"}


def get_user_id_from_token(token: str) -> str:
    verification_result = verify_cognito_token(token)

    if verification_result["status_code"] != 200:
        raise Exception("Invalid token")

    return verification_result["body"]["sub"]


def with_user_id(func):
    @wraps(func)
    async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            logger.debug(f"Event {event}")
            headers = event.get("headers", {})
            token = headers.get("Authorization")
            if token is None:
                return {"status_code": 401, "body": "Authorization token required"}
            user_id_info = verify_cognito_token(token)
            logger.debug(f"User ID info: {user_id_info}")
            if user_id_info["status_code"] != 200:
                return user_id_info
            event["user_id"] = user_id_info["body"]["sub"]
            return await func(event, context)
        except Exception as e:
            return {"statusCode": 500, "body": f"Internal Server Error: {str(e)}"}

    return wrapper
