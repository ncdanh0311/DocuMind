import asyncio
import httpx
from backend.app.api import auth
from backend.app.core.config import settings


def test_brevo_uses_https_and_keeps_otp_out_of_logs(resources, monkeypatch, caplog):
    import json
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(201, json={"messageId": "test-only-message"})
    original = httpx.AsyncClient
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "brevo")
    monkeypatch.setattr(settings, "BREVO_API_KEY", "test-only-brevo-key")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "sender@example.com")
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))
    asyncio.run(auth.send_reset_otp_email("recipient@example.com", "824316"))
    assert str(requests[0].url) == "https://api.brevo.com/v3/smtp/email"
    body = json.loads(requests[0].content)
    assert body["sender"]["email"] == "sender@example.com" and "824316" in body["htmlContent"]
    assert "824316" not in caplog.text and "test-only-brevo-key" not in caplog.text
