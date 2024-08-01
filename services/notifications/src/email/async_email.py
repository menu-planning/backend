# pylint: disable=too-few-public-methods
import logging
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

import aiosmtplib
import anyio
from aiosmtplib.errors import SMTPAuthenticationError, SMTPRecipientsRefused
from src.config import settings
from src.logger import logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    after_log,
    before_log,
    stop_after_attempt,
    wait_fixed,
)

max_tries = 4
wait_seconds = 5


class AsyncEmailNotifications:
    def __init__(
        self,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
    ):
        self.context = ssl.create_default_context() if settings.smtp_tls else None
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    async def send(
        self,
        destination: str,
        subject: str,
        text_template: str,
        html_template: str,
    ):
        sender = settings.smtp_user
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = destination
        text = MIMEText(text_template, "plain")
        html = MIMEText(html_template, "html")
        message.attach(text)
        message.attach(html)
        async with aiosmtplib.SMTP(
            hostname=self.smtp_host,
            port=self.smtp_port,
            tls_context=self.context,
            use_tls=settings.smtp_tls,
        ) as server:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_tries),
                    wait=wait_fixed(wait_seconds),
                    before=before_log(logger, logging.INFO),
                    after=after_log(logger, logging.WARN),
                ):
                    with attempt:
                        with anyio.fail_after(wait_seconds - 1):
                            await server.connect()
                            await server.login(
                                sender, settings.smtp_password.get_secret_value()
                            )
                            await server.send_message(message)
            except (SMTPAuthenticationError, SMTPRecipientsRefused) as e:
                logger.error(f"Non-retryable error occurred: {e}")
                # Handle or log non-retryable errors here
                raise e
            except RetryError as e:
                logger.error(e)
                raise e

    async def send_new_account_confirmation_email(
        self,
        endpoint: str,
        receiver_email: str,
        token_expiration: str,
        project_name: str,
    ):
        subject = f"{project_name} - Confirmação de conta"

        txt_path = anyio.Path(__file__).parent / "templates/confirm_email.txt"
        async with await anyio.open_file(txt_path.as_posix()) as f:
            template_txt_str = await f.read()

        html_path = anyio.Path(__file__).parent / "templates/confirm_email.html"
        async with await anyio.open_file(html_path.as_posix()) as f:
            template_html_str = await f.read()

        await self.send(
            destination=receiver_email,
            subject=subject,
            text_template=Template(template_txt_str).substitute(
                project_name=project_name,
                email=receiver_email,
                link=endpoint,
                valid_minutes=token_expiration,
            ),
            html_template=Template(template_html_str).substitute(
                project_name=project_name,
                email=receiver_email,
                link=endpoint,
                valid_minutes=token_expiration,
            ),
        )

    async def send_admin_new_event(self, event: str):
        subject = f"New event"

        txt_path = anyio.Path(__file__).parent / "email_templates/new_event.txt"
        async with await anyio.open_file(txt_path.as_posix()) as f:
            template_txt_str = await f.read()

        html_path = anyio.Path(__file__).parent / "email_templates/new_event.html"
        async with await anyio.open_file(html_path.as_posix()) as f:
            template_html_str = await f.read()

        await self.send(
            destination=settings.first_admin_email,
            subject=subject,
            text_template=Template(template_txt_str).substitute(
                event=event,
            ),
            html_template=Template(template_html_str).substitute(
                event=event,
            ),
        )
