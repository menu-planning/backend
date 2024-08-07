from typing import Any

import httpx
import jwt

COGNITO_REGION = "sa-east-1"
USER_POOL_ID = "sa-east-1_xrATmGst3"
COGNITO_CLIENT_ID = "lrbucr34nb50q6otf123o5a7f"


def get_cognito_jwks() -> dict[str, Any]:
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
