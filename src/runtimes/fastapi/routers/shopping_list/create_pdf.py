# """FastAPI router for meal create endpoint."""

# from typing import Any
# from src.runtimes.fastapi.routers.helpers import (
#     create_success_response,
#     create_router,
# )
# from src.contexts.shopping_list.core.adapters.api_schema.value_objects.api_shopping_list import ApiShoppingList

# router = create_router(prefix="/shopping-list")

# @router.post("pdf]")
# async def create_shopping_list_pdf(
#     request_body: ApiShoppingList,
# ) -> Any:
    
    
#     return create_success_response(
#         {"message": "PDF created successfully", "shopping-list": pdf},
#         status_code=201
#     )
