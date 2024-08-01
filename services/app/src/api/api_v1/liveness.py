from fastapi import APIRouter, status

router = APIRouter()


@router.post("/healthz", status_code=status.HTTP_200_OK)
def liveness_check() -> None:
    """
    Check if the service is alive.
    """
