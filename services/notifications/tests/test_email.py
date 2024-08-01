import base64

import httpx
import pytest
from src.config import settings
from src.email.async_email import AsyncEmailNotifications

pytestmark = pytest.mark.anyio


async def get_email_from_mailhog(user_email: str):
    async with httpx.AsyncClient() as client:
        all_emails = await client.get(
            f"http://{settings.smtp_host}:18025/api/v2/messages",
            timeout=6.1,
            follow_redirects=True,
        )
        all_emails = all_emails.json()
    return next(m for m in all_emails["items"] if user_email in str(m))


async def test_send_confirmation_email_to_new_user():
    token = "dummy_token"
    endpoint = f"https://dummy-endpoint?token={token}"
    email = "dummy_email@example.com"
    project_name = "dummy_project_name"
    await AsyncEmailNotifications().send_new_account_confirmation_email(
        endpoint=endpoint,
        receiver_email=email,
        token_expiration=15,
        project_name=project_name,
    )
    json_email = await get_email_from_mailhog(email)
    bmessage = base64.b64decode(json_email["MIME"]["Parts"][0]["Body"])
    message = bmessage.decode("utf-8")
    assert json_email["Raw"]["From"] == "app@example.com"
    assert json_email["Raw"]["To"] == [email]
    assert f"É um prazer ter você aqui conosco {email}" in message
