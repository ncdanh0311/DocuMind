"""Send reset mail through Gmail HTTPS endpoints, without logging credentials."""
import base64
from email.message import EmailMessage
from email.utils import formataddr

import httpx

from backend.app.core.config import settings


async def send_gmail_email(recipient: str, html: str):
    if not all((settings.GMAIL_SENDER_EMAIL, settings.GMAIL_CLIENT_ID,
                settings.GMAIL_CLIENT_SECRET, settings.GMAIL_REFRESH_TOKEN)):
        raise RuntimeError("ERR_EMAIL_NOT_CONFIGURED")
    try:
        message = EmailMessage()
        message["From"] = formataddr((settings.PROJECT_NAME, settings.GMAIL_SENDER_EMAIL))
        message["To"] = recipient
        message["Subject"] = "Mã xác thực khôi phục mật khẩu DocuMind"
        message.set_content("Mã xác thực nằm trong phần HTML của email này. Mã có hiệu lực trong 5 phút.")
        message.add_alternative(html, subtype="html")
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": settings.GMAIL_REFRESH_TOKEN,
                "grant_type": "refresh_token",
            })
            token_response.raise_for_status()
            payload = token_response.json()
            token = payload.get("access_token") if isinstance(payload, dict) else None
            if not isinstance(token, str) or not token:
                raise ValueError("Missing access token")
            response = await client.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers={"Authorization": "Bearer " + token},
                json={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")})
            response.raise_for_status()
    except (httpx.HTTPError, ValueError, TypeError):
        # Neither Google's error body nor MIME/OTP/token values enter logs.
        raise RuntimeError("ERR_EMAIL_DELIVERY") from None
