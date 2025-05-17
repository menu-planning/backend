import inspect

from src.contexts.products_catalog.core.adapters.product_kwargs_extractor import (
    ProductKwargsExtractorFactory,
)
from src.contexts.products_catalog.core.bootstrap.container import Container
from src.contexts.products_catalog.core.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.products_catalog.core.domain.commands.products.add_food_product_bulk import (
    AddFoodProductBulk,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def add_products_from_json(raw_data: list[dict], source: str) -> None:
    bus: MessageBus = Container().bootstrap()
    kwargs_extractor = ProductKwargsExtractorFactory().get_extractor(source=source)
    extractor = kwargs_extractor(raw_data)
    products_kwargs = extractor.kwargs
    add_product_cmd = []
    for i in products_kwargs:
        kwargs = {}
        for param in list(inspect.signature(AddFoodProduct).parameters.keys()):
            if param in i and param != "product_id":
                kwargs[param] = i[param]
        add_product_cmd.append(AddFoodProduct(**kwargs))
    cmd = AddFoodProductBulk(
        add_product_cmds=add_product_cmd,
    )
    await bus.handle(cmd)
