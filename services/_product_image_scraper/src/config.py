import os
from functools import lru_cache

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings

# DOTENV_PATH = "dotenv"


class Settings(BaseSettings):
    max_concurrency: int = min(32, os.cpu_count() + 4)
    image_size: tuple[int, int] = os.getenv("IMAGE_SIZE") or 300, 300
    image_cdn_url_prefix: AnyHttpUrl = (
        os.getenv("IMAGE_CDN_URL_PREFIX") or "https://d3j9no8psp2tiv.cloudfront.net"
    )
    image_S3_bucket: str = os.getenv("IMAGE_S3_BUCKET") or "vlep"

    work_timeout: int = 20
    cleanup_timeout: int = 5

    def image_source_url(self, barcode: str) -> list[AnyHttpUrl]:
        return [
            f"http://www.eanpictures.com.br:9000/api/gtin/{barcode}",
            f"https://gtin-img.s3.ca-central-1.amazonaws.com/product/{barcode}.webp",
            f"https://cdn-cosmos.bluesoft.com.br/products/{barcode}",
            f"https://s3.amazonaws.com/infoprice-prd-imagens/gtin/0{barcode}.jpg",
        ]


@lru_cache()
def get_settings() -> Settings:
    # TODO fix path
    # load_dotenv(f"{DOTENV_PATH}/.env")
    return Settings()


settings = get_settings()
