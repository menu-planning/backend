import functools
import re
import time
from datetime import datetime
from types import TracebackType
from typing import Type

import anyio
import httpx
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


def check_for_error(element_id: str = "spnErroMaster", timeout: int = 10):
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


class Scraper:
    URL = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx"
    SITE_KEY = "6Le-PrMUAAAAABVqWmdkUJK1zdOThsHKiL78gOPp"
    QRCODE_URL = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaResponsiva/ConsultaResumidaRJFrame_v400.aspx"

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

    @check_for_error()
    async def find_button_to_access_main_page_and_click_it(
        self, element_id: str
    ) -> None:
        assert self.driver is not None, "First start the session"
        try:
            await self.page.locator(f"#{element_id}").click()
        except Exception:
            raise ScrapingException(
                f"Could not find the button to access main page. cfe_key={self.cfe_key}"
            )

    @check_for_error()
    async def find_button_to_access_all_tabs_and_click_it(
        self, element_id: str
    ) -> None:
        try:
            await self.page.locator(f"#{element_id}").click()
        except Exception:
            raise ScrapingException(
                f"Could not find the button to access the products tab. Possibly wrong URL. cfe_key={self.cfe_key}, URL={Scraper.URL}"
            )

    @check_for_error()
    async def save_page(self, page_name: str):
        try:
            await self.page.wait_for_load_state("domcontentloaded")
            self.pages[page_name] = await self.page.content()
        except Exception as e:
            raise ScrapingException(
                f"Could not save {page_name} page source. cfe_key={self.cfe_key}, error={e}"
            )

    def extract_form_data(self) -> dict[str, str]:
        data = {}
        keys = [
            "__EVENTTARGET",
            "__EVENTARGUMENT",
            "__VIEWSTATE",
            "__VIEWSTATEGENERATOR",
            "__EVENTVALIDATION",
        ]
        for page in self.pages.values():
            soup = BeautifulSoup(page, "html.parser")
            for i in soup.find_all("input"):
                if i.get("name") in keys:
                    data[i.get("name")] = i.get("value")
        return data

    def extract_date(self) -> None:
        assert self.pages.get("main") is not None, "First scrape the main page"
        soup = BeautifulSoup(self.pages.get("main"), "html.parser")

        try:
            header = soup.find("label", string="Data de Emissão")
            date_string = header.find_next_sibling().string
            date = datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S%z")
            self.date = date.isoformat()
        except Exception as e:
            logger.error(f"Error extracting receipt date: {e}")

    def extract_seller(self) -> None:
        assert self.pages.get("main") is not None, "First scrape the main page"
        soup = BeautifulSoup(self.pages.get("main"), "html.parser")
        mapping = {
            "name": "Nome / Razão Social",
            "cnpj": "CNPJ",
            "street_and_number": "Endereço",
            "district": "Bairro / Distrito",
            "zip_code": "CEP",
            "city": "Município",
            "state_registration": "Inscrição Estadual",
            "state": "UF",
        }
        kwargs = {}
        for k, v in mapping.items():
            header = soup.find("label", string=v)
            kwargs[k] = header.find_next_sibling().string

        street, number = kwargs.get("street_and_number", "").split(",")

        address = {
            "street": street.lower(),
            "number": re.findall("[0-9]+|$", number)[0],
            "zip_code": kwargs.get("zip_code", ""),
            "district": kwargs.get("district", "").lower(),
            "city": " ".join(re.findall("[a-zA-Z]+", kwargs.get("city", ""))).lower(),
            "state": kwargs.get("state", ""),
        }

        self.seller = {
            "name": kwargs.get("name", "").lower(),
            "cnpj": kwargs.get("cnpj", ""),
            "state_registration": kwargs.get("state_registration", ""),
            "address": address,
        }

    def extract_items(self) -> list[dict[str, str | float]]:
        assert self.pages.get("main") is not None, "First scrape the main page"
        soup = BeautifulSoup(self.pages.get("main"), "html.parser")
        tc_class_mapping = {
            "description": "fixo-prod-serv-descricao",
            "quantity": "fixo-prod-serv-qtd",
            "unit": "fixo-prod-serv-uc",
            "price_paid": "fixo-prod-serv-vb",
        }
        label_mapping = {
            "price_per_unit": "Valor unitário de comercialização",
            "gross_price": "Valor unitário de tributação",
            "sellers_product_code": "Código do Produto",
            "barcode": "Código EAN Comercial",
            "discount": "Valor do Desconto",
        }

        items = {}
        for k, v in tc_class_mapping.items():
            count = 1
            for i in soup.find_all("td", class_=v)[1:]:
                if items.get(count):
                    items[count][k] = i.text.strip("\t\r\n").lower()
                else:
                    items[count] = {k: i.text.strip("\t\r\n").lower()}
                count += 1

        for k, v in label_mapping.items():
            count = 1
            for i in soup.find_all("label", string=v):
                if items.get(count):
                    items[count][k] = (
                        i.find_next_sibling().string.strip("\t\r\n").lower()
                    )
                else:
                    items[count] = {
                        k: i.find_next_sibling().string.strip("\t\r\n").lower()
                    }
                count += 1

        floats = ["quantity", "price_paid", "price_per_unit", "gross_price", "discount"]
        for item in items.values():
            for f in floats:
                if item.get(f) == "":
                    item[f] = 0.0

        self.items = [{"number": k} | v for k, v in items.items()]

    async def scrape(self):
        if self.qrcode:
            async with httpx.AsyncClient() as session:
                r = await session.get(self.qrcode, follow_redirects=True)
                headers = {}
                headers["Origin"] = "https//www.nfce.fazenda.sp.gov.br"
                headers["Referer"] = self.qrcode.replace(
                    "qrcode", "NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx"
                )
                data = {}
                keys = [
                    "__EVENTTARGET",
                    "__EVENTARGUMENT",
                    "__VIEWSTATE",
                    "__VIEWSTATEGENERATOR",
                    "__EVENTVALIDATION",
                ]
                soup = BeautifulSoup(r.text, "html.parser")
                for i in soup.find_all("input"):
                    if i.get("name") in keys:
                        data[i.get("name")] = i.get("value") or ""
                data["__EVENTTARGET"] = "btnVisualizarAbas"
                r = await session.post(
                    Scraper.QRCODE_URL,
                    headers=headers,
                    data=data,
                    follow_redirects=True,
                )
                self.pages["main"] = r.text
        else:
            # async with self:
            await self.page.goto(Scraper.URL)
            g_response = await self.get_g_response()
            input_element = await self.get_cfe_key_input_box("Conteudo_txtChaveAcesso")
            await self.break_captcha(g_response, input_element)
            await self.find_button_to_access_main_page_and_click_it(
                "Conteudo_btnConsultaResumida"
            )
            await self.save_page("main")
        self.extract_date()
        self.extract_seller()
        self.extract_items()
