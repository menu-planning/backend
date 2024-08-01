import functools
import re
import time
from datetime import datetime
from types import TracebackType
from typing import Type

import anyio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright.async_api._generated import (Browser, BrowserContext, Locator,
                                             Page)
from playwright.async_api._generated import Playwright as AsyncPlaywright
from selenium.webdriver.remote.webdriver import WebDriver
from src.common.anti_captcha import fetch_captcha_g_response
from src.common.browser_driver import get_driver
from src.common.exceptions import ScrapingException
from src.logger import logger

SLEEP = 10
MOUSE_DELAY = 2


def check_for_error(element_id: str = "dialog-modal", timeout: int = 10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self: "Scraper", *args, **kwargs):
            t_end = time.time() + timeout
            while time.time() < t_end:
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e1:
                    try:
                        locator = self.page.locator(f"#{element_id}")
                        msg = await locator.all_text_contents()
                        msg = msg[0].lower()
                        if "o suporte" in msg:
                            msg = f"Invalid cfe_key: {self.cfe_key}"
                        elif "o texto digitado não confere" in msg:
                            msg = f"Wrong g captcha response. cfe_key={self.cfe_key}"
                        elif "cupom temporariamente indisponível" in msg:
                            msg = f"Cupom temporariamente indisponível. cfe_key={self.cfe_key}"
                        elif "acesso inválida" in msg:
                            msg = f"Invalid receipt id. cfe_key={self.cfe_key}"
                        else:
                            msg = f"Found error dialog. cfe_key={self.cfe_key}"
                        break
                    except Exception as e:
                        msg = f"Request processing time excedeed limit. {e1}. {e}"
                        pass
            logger.error(msg)
            raise ScrapingException(msg)

        return wrapper

    return decorator


def parse_to_english(string: str):
    try:
        num = float(string.replace(",", "."))
        if "," in string:
            return num
        else:
            return string
    except ValueError:
        return string


# def run(playwright: Playwright) -> None:
#     browser = playwright.chromium.launch(headless=False)
#     context = browser.new_context(ignore_https_errors=True)
#     page = context.new_page()
#     page.goto("https://satsp.fazenda.sp.gov.br/COMSAT/Public/ConsultaPublica/ConsultaPublicaCfe.aspx")
#     page.locator("#conteudo_txtChaveAcesso").click()

#     # ---------------------
#     context.close()
#     browser.close()


class Scraper:
    URL = "https://satsp.fazenda.sp.gov.br/COMSAT/Public/ConsultaPublica/ConsultaPublicaCfe.aspx"
    SITE_KEY = "6LeEy8wUAAAAAHN6Wu2rNdku25fyHUVgovX-rJqM"
    # example cfe_key = 35210944480747000160590005263392324011310866

    def __init__(
        self,
        cfe_key: str,
        qrcode: str | None = None,
    ) -> None:
        self.cfe_key = cfe_key
        self.qrcode = qrcode
        self.date: datetime = None
        self.seller: dict[str, str] = {}
        self.items: list[dict[str, str | float]] = []
        self.pages: dict[str, str] = {}
        self.driver: WebDriver | None = None
        self.apw: AsyncPlaywright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    async def __aenter__(self):
        if self.driver is not None:
            try:
                self.driver.current_url
            except Exception:
                event = anyio.Event()
                self.driver = await anyio.to_thread.run_sync(get_driver, event)
        else:
            event = anyio.Event()
            self.driver = await anyio.to_thread.run_sync(get_driver, event)
        self.apw = async_playwright()
        p = await self.apw.__aenter__()
        self.browser = await p.chromium.launch(headless=False)
        self.context = await self.browser.new_context(ignore_https_errors=True)
        self.page = await self.context.new_page()
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        try:
            await self.context.close()
        except Exception:
            pass
        try:
            await self.browser.close()
        except Exception:
            pass
        try:
            await self.apw.__aexit__(exc_type, exc_value, traceback)
        except Exception:
            pass
        try:
            await anyio.to_thread.run_sync(self.driver.quit)
        except Exception:
            pass

    # async def start_driver_session(self):
    #     await self.__aenter__()

    async def close(self):
        await self.__aexit__()

    async def get_g_response(self) -> str:
        # return "dummy"
        try:
            event = anyio.Event()
            response = await anyio.to_thread.run_sync(
                fetch_captcha_g_response,
                Scraper.URL,
                Scraper.SITE_KEY,
                event,
            )
            return response
        except Exception:
            logger.error(
                f"Error while fetching captcha g-response. cfe_key={self.cfe_key}"
            )
            raise ScrapingException(
                f"Could not fetch captcha g-response. cfe_key={self.cfe_key}"
            )

    @check_for_error()
    async def get_cfe_key_input_box(self, element_id: str) -> Locator:
        assert self.driver is not None, "First start the session"
        try:
            return self.page.locator(f"#{element_id}")
        except Exception:
            raise ScrapingException(
                f"Could not find the cfe_key input element. Possibly wrong URL. cfe_key={self.cfe_key}, URL={Scraper.URL}"
            )

    @check_for_error()
    async def break_captcha(
        self, g_response: str, cfe_key_input_locator: Locator
    ) -> None:
        assert self.driver is not None, "First start the session"
        try:
            await cfe_key_input_locator.click()
            await anyio.sleep(0.5)
            await self.page.keyboard.type(self.cfe_key, delay=0.5)
            # await anyio.sleep(MOUSE_DELAY)
            await cfe_key_input_locator.inner_html()
            await self.page.evaluate(
                "g_response => {document.getElementById('g-recaptcha-response').innerHTML = g_response}",
                g_response,
            )
            return
        except Exception:
            raise ScrapingException(f"Could not solve captcha. cfe_key={self.cfe_key}")

    # @check_for_error()
    # async def get_button_to_access_main_page(self, element_id: str) -> Locator:
    #     assert self.driver is not None, "First start the session"
    #     try:
    #         return self.page.locator(f"#{element_id}")
    #     except Exception:
    #         raise ScrapingException(
    #             f"Could not find the button to access the main page. Possibly wrong URL. cfe_key={self.cfe_key}, URL={Scraper.URL}"
    #         )

    @check_for_error()
    async def enable_button_to_access_main_page_and_click_it(
        self, element_id: str
    ) -> None:
        assert self.driver is not None, "First start the session"
        try:
            await self.page.eval_on_selector(
                "#conteudo_btnConsultar", "el => el.removeAttribute('disabled')"
            )
            await self.page.locator(f"#{element_id}").click()
        except Exception:
            raise ScrapingException(
                f"Could not enable button to access main page. cfe_key={self.cfe_key}"
            )

    @check_for_error()
    async def find_button_to_access_items_page_and_click_it(
        self,
        element_id: str,
    ) -> None:
        assert self.driver is not None, "First start the session"
        try:
            await self.page.locator(f"#{element_id}").click()
        except Exception:
            raise ScrapingException(
                f"Could not find the button to access the items page. Possibly wrong URL. cfe_key={self.cfe_key}, URL={Scraper.URL}"
            )

    @check_for_error()
    async def find_button_to_access_products_tab_and_click_it(
        self,
        element_id: str,
    ) -> None:
        assert self.driver is not None, "First start the session"
        try:
            await self.page.locator(f"#{element_id}").click()
        except Exception:
            raise ScrapingException(
                f"Could not find the button to access the products tab. Possibly wrong URL. cfe_key={self.cfe_key}, URL={Scraper.URL}"
            )

    @check_for_error()
    async def save_page(self, page_name: str):
        assert self.driver is not None, "First start the session"
        try:
            await self.page.wait_for_load_state("domcontentloaded")
            self.pages[page_name] = await self.page.content()
        except Exception:
            raise ScrapingException(
                f"Could not save {page_name} page source. cfe_key={self.cfe_key}"
            )

    def extract_date(self) -> None:
        assert self.pages.get("main") is not None, "First scrape the main page"
        soup = BeautifulSoup(self.pages.get("main"), "html.parser")

        day_patterns = {
            "[0-9]{2}/[0-9]{2}/[0-9]{4}": "%d/%m/%Y",
            "[0-9]{4}-[0-9]{2}-[0-9]{2}": "%Y-%m-%d",
        }
        hour_patterns = {"[0-9]{2}:[0-9]{2}:[0-9]{2}": "%H:%M:%S"}

        try:
            date = soup.find(id="conteudo_lblDataEmissao").text.strip()
            day = ""
            hour = ""
            day_pattern = ""
            hour_pattern = ""
            for pattern in day_patterns.keys():
                try:
                    day = re.findall(pattern, date)[0]
                    day_pattern = day_patterns[pattern]
                    break
                except Exception:
                    pass
            for pattern in hour_patterns.keys():
                try:
                    hour = re.findall(pattern, date)[0]
                    hour_pattern = hour_patterns[pattern]
                    break
                except Exception:
                    pass
            date_pattern = f"{day_pattern}{hour_pattern}"
            date = datetime.strptime(f"{day}{hour}", date_pattern)
            date = date.isoformat()
            self.date = date
        except Exception as e:
            logger.error(f"Error extracting receipt date: {e}")

    def extract_seller(self) -> None:
        assert self.pages.get("main") is not None, "First scrape the main page"
        soup = BeautifulSoup(self.pages.get("main"), "html.parser")
        name = soup.find(id="conteudo_lblNomeEmitente").text.strip()
        cnpj = soup.find(id="conteudo_lblCnpjEmitente").text.strip()
        state_registration = soup.find(id="conteudo_lblIeEmitente").text.strip()
        try:
            street, number = soup.find(id="conteudo_lblEnderecoEmitente").text.split(
                ","
            )
        except AttributeError:
            street, number = soup.find(id="conteudo_lblEnderecoEmintente").text.split(
                ","
            )
        district = soup.find(id="conteudo_lblBairroEmitente").text.strip()
        city = soup.find(id="conteudo_lblMunicipioEmitente").text.strip()
        state = (
            soup.find(id="conteudo_lblMunicipioEmitente")
            .find_next_sibling("span")
            .text.strip()[-2:]
        )
        zip_code = soup.find(id="conteudo_lblCepEmitente").text.strip()

        address = {
            "street": street.lower(),
            "number": re.findall("[0-9]+|$", number)[0],
            "zip_code": zip_code,
            "district": district.lower(),
            "city": city.lower(),
            "state": state,
        }

        seller = {
            "name": name.lower(),
            "cnpj": cnpj,
            "state_registration": state_registration,
            "address": address,
        }
        self.seller = seller

    def extract_items(self) -> list[dict[str, str | float]]:
        assert self.pages.get("items") is not None, "First scrape the items page"
        soup = BeautifulSoup(self.pages.get("items"), "html.parser")
        table = soup.find("table", id="conteudo_grvProdutosServicos")
        rows = table.find_all("tr")
        if rows[0].find_all("th"):
            rows = rows[1:]

        headers = {}

        thead = table.find_all("th")
        for i in range(len(thead)):
            headers[i] = thead[i].text.strip().lower()

        datum = []
        for row in rows:
            cells = row.find_all("td")
            if thead:
                items = {}
                for index in headers:
                    try:
                        num = float(cells[index].text.strip().replace(",", "."))
                        if "," in cells[index].text.strip():
                            items[headers[index]] = num
                        else:
                            items[headers[index]] = cells[index].text.strip()
                    except ValueError:
                        items[headers[index]] = cells[index].text.strip()
            else:
                items = []
                for index in cells:
                    items.append(index.text.strip())
            datum.append(items)

        self.items = datum

    async def scrape(self):
        await self.page.goto(Scraper.URL)
        g_response = await self.get_g_response()
        input_element = await self.get_cfe_key_input_box("conteudo_txtChaveAcesso")
        await self.break_captcha(g_response, input_element)
        await self.enable_button_to_access_main_page_and_click_it(
            "conteudo_btnConsultar"
        )
        await self.save_page("main")
        await self.find_button_to_access_items_page_and_click_it("conteudo_btnDetalhe")
        await self.find_button_to_access_products_tab_and_click_it(
            "conteudo_tabProdutoServico"
        )
        products_table = self.page.locator("#conteudo_grvProdutosServicos")
        await products_table.wait_for()
        await self.save_page("items")
        self.extract_date()
        self.extract_seller()
        self.extract_items()


