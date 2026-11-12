import asyncio
import httpx
import pytest
from backend.app.api import auth
from backend.app.core.config import settings
from backend.app.services import gmail_mailer


@pytest.fixture
def gmail_settings(monkeypatch):
    for name, value in {"EMAIL_PROVIDER": "gmail_api", "GMAIL_SENDER_EMAIL": "sender@gmail.com",
        "GMAIL_CLIENT_ID": "test-client", "GMAIL_CLIENT_SECRET": "test-client-secret",
        "GMAIL_REFRESH_TOKEN": "test-refresh-token"}.items():
        monkeypatch.setattr(settings, name, value)


def gmail_transport(monkeypatch, respond):
    original = httpx.AsyncClient
    monkeypatch.setattr(gmail_mailer.httpx, "AsyncClient",
                        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs))


def test_gmail_refreshes_then_sends_utf8_mime_over_https(gmail_settings, monkeypatch, caplog):
    import base64
    import json
    from email import policy
    from email.parser import BytesParser
    from urllib.parse import parse_qs
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={"access_token": "test-access-token"} if len(requests) == 1 else {"id": "mail-id"})
    gmail_transport(monkeypatch, respond)
    asyncio.run(auth.send_reset_otp_email("recipient@example.com", "824316"))
    assert [str(x.url) for x in requests] == ["https://oauth2.googleapis.com/token", "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"]
    assert parse_qs(requests[0].content.decode())["grant_type"] == ["refresh_token"]
    assert requests[1].headers["Authorization"] == "Bearer test-access-token"
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(json.loads(requests[1].content)["raw"]))
    assert message["To"] == "recipient@example.com" and "sender@gmail.com" in message["From"]
    assert "khôi phục mật khẩu" in message["Subject"]
    assert "824316" in message.get_body(preferencelist=("html",)).get_content()
    assert all(value not in caplog.text for value in ("824316", "test-access-token", "test-refresh-token", "test-client-secret"))


@pytest.mark.parametrize("missing", ["GMAIL_SENDER_EMAIL", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"])
def test_gmail_missing_configuration_never_connects(gmail_settings, monkeypatch, missing):
    monkeypatch.setattr(settings, missing, "")
    def forbidden(**kwargs): raise AssertionError("Must not open a client")
    monkeypatch.setattr(gmail_mailer.httpx, "AsyncClient", forbidden)
    with pytest.raises(RuntimeError, match="ERR_EMAIL_NOT_CONFIGURED"):
        asyncio.run(auth.send_reset_otp_email("recipient@example.com", "824316"))


@pytest.mark.parametrize("token_body,token_status,send_status,expected_calls", [
    ({"error": "invalid_grant", "detail": "test-refresh-token"}, 400, 200, 1),
    ({}, 200, 200, 1), ([], 200, 200, 1),
    ({"access_token": "test-access-token"}, 200, 403, 2),
])
def test_gmail_provider_errors_are_sanitized_and_not_retried(gmail_settings, monkeypatch, caplog, token_body, token_status, send_status, expected_calls):
    requests = []
    def respond(request):
        requests.append(request)
        return httpx.Response(token_status, json=token_body) if len(requests) == 1 else httpx.Response(send_status, json={"error": "test-access-token"})
    gmail_transport(monkeypatch, respond)
    with pytest.raises(RuntimeError, match="^ERR_EMAIL_DELIVERY$"):
        asyncio.run(auth.send_reset_otp_email("recipient@example.com", "824316"))
    assert len(requests) == expected_calls
    assert "test-refresh-token" not in caplog.text and "824316" not in caplog.text


def test_gmail_failure_keeps_forgot_password_response_generic(resources, gmail_settings, monkeypatch, caplog):
    client, _, _, alice, _ = resources
    # PostgreSQL auth tests cover the rate limiter; this test isolates delivery.
    monkeypatch.setattr(auth, "consume_reset_rate_limit", lambda *args: True)
    gmail_transport(monkeypatch, lambda request: httpx.Response(400, json={"error": "invalid_grant", "detail": "test-client-secret"}))
    known = client.post("/api/v1/auth/forgot-password", json={"email": alice.email})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "unknown@example.com"})
    assert known.status_code == unknown.status_code == 200
    assert known.json() == unknown.json() == {"message": "MSG_OTP_SENT"}
    assert "test-client-secret" not in caplog.text and "invalid_grant" not in caplog.text


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
