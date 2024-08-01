from functools import lru_cache
from typing import Any

from fastapi import HTTPException, Request, status
from firebase_admin import auth


@lru_cache(maxsize=1024)
def verify_firebase_token(token: str) -> dict[str, Any]:
    try:
        decoded_token = auth.verify_id_token(token)
        sign_in_provider = decoded_token["firebase"]["sign_in_provider"]
        if sign_in_provider == "password":
            if decoded_token["email_verified"]:
                return decoded_token
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not verified.",
                )
        else:
            return decoded_token
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked"
        )
    except ValueError:
        # Handles cases where the token is invalid for any reason not covered above
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        if hasattr(e, "detail") and e.detail == "Email not verified.":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not verified.",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )


def _decoded_token(request: Request) -> dict[str, Any]:
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token required",
        )
    token = token.replace("Bearer ", "")
    return verify_firebase_token(token)


def current_user_id(request: Request) -> str:
    decoded_token = _decoded_token(request)
    return decoded_token["uid"]
