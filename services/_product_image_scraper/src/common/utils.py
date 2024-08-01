from enum import Enum

import requests
from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from anyio import Event, from_thread
from selenium import webdriver
from src.contexts.product_image_scraper.config import selenium_settings
from src.contexts.product_image_scraper.exceptions import ScrapingError
from src.logging.logger import logger


class CouldNotSolveCaptcha(Exception):
    pass


ANTI_CAPTCHA_API_KEY = "788709a88100805e30f7ac2ac185b80e"
SCRAPER_API_KEY = "b050aca4a43ada4a5980ffa730c55500"


def get_driver(event: Event | None = None):
    # proxy_options = {
    #     "proxy": {
    #         "http": f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001",  # noqa
    #         "https": f"http://scraperapi:{SCRAPER_API_KEY}@proxy-server.scraperapi.com:8001",  # noqa
    #         "no_proxy": "localhost,127.0.0.1",
    #     }
    # }
    # seleniumwire_options = {
    #     "suppress_connection_errors": False,
    #     "auto_config": False,
    #     "addr": "0.0.0.0",
    #     "port": 8087,
    #     # "proxy": {"no_proxy": "localhost,127.0.0.1"},  # excludes
    # }
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=es")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("start-maximized")
        # chrome_options.add_argument("disable-infobars")
        chrome_options.add_argument("disable-extentions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_experimental_option("useAutomationExtension", False)
        # chrome_options.add_argument("--proxy-server=cfe-scraper-worker:8087")
        r = requests.get(selenium_settings.url + "/status").json()
        if not r.get("value", {}).get("ready", False):
            raise ScrapingError("Selenium server not ready")
        driver = webdriver.Remote(
            command_executor=selenium_settings.url,
            # desired_capabilities=chrome_options.to_capabilities(),
            options=chrome_options,
        )
        # service = Service(executable_path=ChromeDriverManager().install())
        # driver = webdriver.Chrome(
        #     service=service,
        #     options=options,
        #     # seleniumwire_options=proxy_options,
        # )
        # driver.execute_script(
        #     "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"  # noqa
        # )
        return driver
    except Exception as e:
        logger.error(f"Error starting remote WebDriver: {e}")
        # return None
    finally:
        if event:
            from_thread.run_sync(event.set)


def fetch_captcha_g_response(
    website_url: str, website_key: str, event: Event | None = None
) -> str:
    solver = recaptchaV2Proxyless()
    solver.set_verbose(1)
    solver.set_key(ANTI_CAPTCHA_API_KEY)
    solver.set_website_url(website_url)
    solver.set_website_key(website_key)
    solver.set_soft_id(0)
    g_response = solver.solve_and_return_solution()
    try:
        if g_response != 0:
            return g_response
        else:
            raise CouldNotSolveCaptcha(f"Task finished with error: {solver.error_code}")
    finally:
        event.set()
