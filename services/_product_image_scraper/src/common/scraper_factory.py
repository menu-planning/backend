from collections.abc import Mapping
from datetime import datetime
from typing import Protocol

from attrs import frozen
from selenium.webdriver.remote.webdriver import WebDriver
from src.contexts.product_image_scraper.endpoints.SP.model_59.scraper import (
    Scraper as SP59Scraper,
)
from src.contexts.product_image_scraper.exceptions import BadRequest
from src.contexts.product_image_scraper.SP.model_65.scraper import (
    Scraper as SP65Scraper,
)
from src.contexts.product_image_scraper.utils import ReceiptIDCodes


class Scraper(Protocol):
    cfe_key: str
    qrcode: str
    date: datetime
    seller: dict[str, str]
    items: list[dict[str, str | float]]
    pages: dict[str, str]
    driver: WebDriver | None

    async def scrape(self): ...


@frozen
class Mapper:
    models: dict[str, Scraper] | Scraper
    model_slice: slice | None = slice(20, 22)


class ScraperFactory:
    def __init__(self):
        self._scrapers: dict[str, Mapper] = {
            ReceiptIDCodes.SP.name: Mapper(
                model_slice=slice(20, 22),
                models={
                    "65": SP65Scraper,
                    "59": SP59Scraper,
                },
            ),
        }

    def get_scraper(self, cfe_key: str) -> type[Scraper]:
        cfe_key = str(cfe_key)
        if len(cfe_key) != 44:
            raise BadRequestException(
                f"Receipt id must have 44 digits. Got {len(cfe_key)} -> {cfe_key}"
            )
        try:
            state_code = int(str(int(cfe_key))[:2])
        except ValueError:
            raise BadRequestException(
                f"Receipt id must contain only numbers. cfe_key={cfe_key}"
            )
        try:
            state = ReceiptIDCodes(state_code).name
        except ValueError:
            raise BadRequestException(
                f"There is no state with receipt code={state_code}."
            )
        try:
            mapper = self._scrapers[state]
        except KeyError:
            raise BadRequestException(f"Could not find scraper for state={state}")

        if not isinstance(mapper.models, Mapping):
            return mapper.models
        if len(mapper.models) == 1:
            return mapper.models.values()[0]
        if not mapper.model_slice:
            raise BadRequestException(f"Must define a model_slice for state={state}.")

        model = str(cfe_key[mapper.model_slice])

        if model not in mapper.models:
            raise BadRequestException(f"Could not find a scraper for model={model}.")

        return mapper.models[model]
