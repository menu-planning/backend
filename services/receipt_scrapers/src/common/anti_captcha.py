from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless
from anyio import Event
from src.common.exceptions import CouldNotSolveCaptchaException

ANTI_CAPTCHA_API_KEY = "788709a88100805e30f7ac2ac185b80e"
SCRAPER_API_KEY = "b050aca4a43ada4a5980ffa730c55500"

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
            raise CouldNotSolveCaptchaException(f"Task finished with error: {solver.error_code}")
    finally:
        event.set()