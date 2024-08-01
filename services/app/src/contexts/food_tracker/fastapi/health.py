from fastapi import APIRouter, status
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after

router = APIRouter()


@router.get(
    "/health/startup",
    status_code=status.HTTP_200_OK,
)
@timeout_after()
async def startup_check():
    """
    Check if the service start properly.
    """
    # await deps.current_active_user(current_user_email)
    # queries = request.query_params
    # valid_filter = {}
    # for k, v in queries.items():
    #     valid_filter[k.replace("-", "_")] = v
    # valid_filter["discarded"] = (queries.get("discarded") or False,)
    # valid_filter["limit"] = (queries.get("limit") or 500,)
    # valid_filter["sort"] = (queries.get("sort") or "-date",)
    # products_provider = container.products_catalog_provider()
    # products = await products_provider.get_products(filter=valid_filter)
    # return [ApiProduct.from_domain(product) for product in products]
