from fastapi import APIRouter, status

router = APIRouter()


@router.post("/health/startup", status_code=status.HTTP_200_OK)
def startup_check() -> None:
    """
    Check if the service start properly.
    """
    {"startupcheck": "Everything OK!"}
    return {"startupcheck": "Everything OK!"}
