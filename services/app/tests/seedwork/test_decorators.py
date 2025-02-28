import anyio
import pytest
from src.contexts.seedwork.shared.endpoints.decorators.timeout_after import (
    timeout_after,
)

pytestmark = [pytest.mark.anyio]


async def test_timeout():
    @timeout_after(timeout=0.1)
    async def test_func():
        await anyio.sleep(0.2)

    with pytest.raises(TimeoutError):
        await test_func()


# async def test_invalid_api_schema_send_400():
#     @timeout_after()
#     async def test_func():
#         raise InvalidApiSchemaException

#     with pytest.raises(HTTPException) as exc_info:
#         await test_func()
#     assert exc_info.value.status_code == 400


# async def test_bad_request_send_400():
#     @timeout_after()
#     async def test_func():
#         raise BadRequestException

#     with pytest.raises(HTTPException) as exc_info:
#         await test_func()
#     assert exc_info.value.status_code == 400


# async def test_other_exceptions_send_500():
#     @timeout_after()
#     async def test_func():
#         raise Exception

#     with pytest.raises(HTTPException) as exc_info:
#         await test_func()
#     assert exc_info.value.status_code == 500
#     assert exc_info.value.detail == "Internal server error"
