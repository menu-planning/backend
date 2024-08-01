import os
from functools import lru_cache
from typing import Any

from pydantic import AmqpDsn, Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings


class RabbitmqSettings(BaseSettings):
    rabbitmq_user: str = os.getenv("RABBITMQ_USER") or "guest"
    rabbitmq_password: SecretStr = Field(default=SecretStr("guest"))
    # if os.getenv("RABBITMQ_PASSWORD"):
    #     rabbitmq_password: SecretStr = Field(..., env="RABBITMQ_PASSWORD")
    # else:
    #     rabbitmq_password: SecretStr = SecretStr("guest")
    rabbitmq_port: int = os.getenv("RABBITMQ_PORT") or 5672
    rabbitmq_server: str = os.getenv("RABBITMQ_SERVER") or "localhost"
    rabbitmq_vhost: str = os.getenv("RABBITMQ_VHOST") or ""

    rabbitmq_url: AmqpDsn | None = None

    @field_validator("rabbitmq_url", mode="before")
    def assemble_amqp_connection(cls, v: str | None, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        return AmqpDsn.build(
            scheme="amqp",
            username=info.data.get("rabbitmq_user"),
            password=info.data.get("rabbitmq_password").get_secret_value(),
            # if info.data.get("rabbitmq_password")
            # else "guest",
            host=info.data.get("rabbitmq_server"),
            port=info.data.get("rabbitmq_port"),
            path=info.data.get("rabbitmq_vhost"),
            # path=f"/{values.get('rabbitmq_vhost')}",
        )
        # if (
        #     os.environ.get("APP_ENVIRONMENT", default=None)
        #     and os.environ["APP_ENVIRONMENT"] != "production"
        # ):
        #     return AmqpDsn.build(
        #         scheme="amqp",
        #         user=values.get("rabbitmq_user"),
        #         password=values.get("rabbitmq_password").get_secret_value(),
        #         host=values.get("rabbitmq_server"),
        #         port=str(values.get("rabbitmq_port" or "5672")),
        #         path=f"/{values.get('rabbitmq_vhost') or ''}",
        #     )
        # servers = list(
        #     AmqpDsn.build(
        #         scheme="amqp",
        #         user=values.get("rabbitmq_user"),
        #         password=values.get("rabbitmq_password").get_secret_value(),
        #         host=f"{values.get('rabbitmq_server' or 'rabbitmq-cluster-server')}-{i}",  # noqa
        #         port=str(values.get("rabbitmq_port" or "5672")),
        #         path=f"/{values.get('rabbitmq_vhost') or ''}",
        #     )
        #     for i in range(3)
        # )
        # return ";".join(servers)

    rabbitmq_default_timeout: int = 5


@lru_cache()
def get_rabbitmq_settings() -> RabbitmqSettings:
    return RabbitmqSettings()


rabbitmq_settings = get_rabbitmq_settings()
