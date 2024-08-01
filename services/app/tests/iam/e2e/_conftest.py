from datetime import datetime, timedelta
from typing import Generator

import pytest
from anyio import Path
from httpx import AsyncClient
from jose import jwt
from src.config.api_config import api_settings
from src.config.app_config import app_settings
from src.main import app
from src.rabbitmq.connection import aio_pika_connection
from tenacity import retry, stop_after_delay

# def random_lower_string() -> str:
#     return "".join(random.choices(string.ascii_lowercase, k=32))


# def random_email() -> str:
#     return f"{random_lower_string()}@{random_lower_string()}.com"


# @pytest.fixture(scope="module")
# async def client() -> Generator:
#     async with AsyncClient(app=app, base_url=api_settings.api_url) as c:
#         yield c
#     conn = await aio_pika_connection.get_connection()
#     await conn.close()


# @pytest.fixture(scope="module")
# def admin_token_headers(client: AsyncClient) -> dict[str, str]:
#     login_data = {
#         "username": app_settings.first_admin_email,
#         "password": app_settings.first_admin_password.get_secret_value(),
#     }
#     r = client.post(f"{api_settings.api_v1_str}/login/access-token", data=login_data)
#     tokens = r.json()
#     a_token = tokens["access_token"]
#     headers = {"Authorization": f"Bearer {a_token}"}
#     return headers


def create_access_token(data: dict, expires_minutes: int | None = None):
    to_encode = data.copy()
    if expires_minutes:
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        app_settings.token_secret_key.get_secret_value(),
        algorithm=app_settings.algorithm,
    )
    return encoded_jwt


@pytest.fixture(scope="module")
def test_user_token_headers(httpx_client: AsyncClient) -> dict[str, str]:
    token = create_access_token(
        {"sub": app_settings.email_test_user},
        expires_minutes=app_settings.access_token_expire_minutes,
    )
    headers = {"Authorization": f"Bearer {token}"}
    return headers


# @pytest.fixture(scope="module")
# def admin_token_headers(client: AsyncClient) -> dict[str, str]:
#     return get_admin_token_headers(client)


# def user_authentication_headers(
#     *, client: AsyncClient, email: str, password: str
# ) -> dict[str, str]:
#     data = {"username": email, "password": password}
#     r = client.post(f"{api_settings.api_v1_str}/login/access-token", data=data)
#     response = r.json()
#     auth_token = response["access_token"]
#     headers = {"Authorization": f"Bearer {auth_token}"}
#     return headers


# def create_random_user() -> entities.User:
#     email = random_email()
#     password = random_lower_string()
#     hashed_pass = entities.User.get_password_hash(password=password)
#     user = entities.User.create_user(username=email, hashed_password=hashed_pass)
#     return user


# def authentication_token_from_email(
#     *, client: AsyncClient, email: str, session: Session, expired: bool = False
# ) -> dict[str, str]:
#     """
#     Return a valid token for the user with given email.

#     If the user doesn't exist it is created first.
#     """
#     password = random_lower_string()
#     repo = user_repo.UserRepo(session=session)
#     user = repo.get_by_email(email=email)
#     if not user:
#         hashed_pass = entities.User.get_password_hash(password=password)
#         user = entities.User.create_user(email=email, hashed_password=hashed_pass)
#         user.confirm_user()
#         user = repo.add(aggregate_root=user)
#         session.commit()
#     else:
#         hashed_pass = entities.User.get_password_hash(password=password)
#         user._hashed_password = hashed_pass
#         user.confirm_user()
#         repo.update(aggregate_root=user)
#         session.commit()
#     return user_authentication_headers(client=client, email=email, password=password)


# @pytest.fixture(scope="module")
# def normal_user_token_headers(client, session) -> dict[str, str]:
#     return authentication_token_from_email(
#         client=client,
#         email=app_settings.email_test_user,
#         session=session,
#     )


@pytest.fixture(scope="module")
def email_from_token(normal_user_token_headers) -> dict[str, str]:
    token = normal_user_token_headers["Authorization"].split()[1]
    payload = jwt.decode(
        token,
        app_settings.token_secret_key.get_secret_value(),
        algorithms=[app_settings.algorithm],
    )
    return payload.get("sub")


@retry(stop=stop_after_delay(10))
def wait_for_webapp_to_come_up(client: AsyncClient):
    prefix = api_settings.api_v1_str
    return client.get(f"{prefix}{api_settings.liveness_check_url}")


@pytest.fixture(scope="module")
async def restart_api(httpx_client: AsyncClient):
    path = Path(__file__).parents[4] / "main.py"
    await path.touch()
    return wait_for_webapp_to_come_up(httpx_client)


# @pytest.fixture
# async def restart_rabbitmq():
#     await wait_for_rabbitmq_to_come_up()
#     if not shutil.which("docker compose"):
#         print("skipping restart, assumes running in container")
#         return
#     await anyio.run_process(
#         ["docker compose", "restart", "-t", "0", "rabbitmq"],
#         check=True,
#     )
