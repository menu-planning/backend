import requests
from anyio import Event, from_thread
from selenium import webdriver
from src.common.exceptions import ScrapingException
from src.config import settings
from src.logger import logger


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
        r = requests.get(settings.url + "/status").json()
        if not r.get("value", {}).get("ready", False):
            raise ScrapingException("Selenium server not ready")
        driver = webdriver.Remote(
            command_executor=settings.url,
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
