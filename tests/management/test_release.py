import base64
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts import android_release as release
from scripts import publish_beta as publish


@pytest.mark.parametrize("url", ["", "http://api.example.com/api/v1", "https://localhost/api/v1",
    "https://127.0.0.1/api/v1", "https://192.168.1.1/api/v1", "https://[::1]/api/v1",
    "https://backend.local/api/v1", "https://user:secret@api.example.com/api/v1",
    "https://api.example.com/api/v1?key=hidden", "https://api.example.com/api/v1#fragment",
    "https://api.example.com/", "https://api.example.com:8000/api/v1"])
def test_release_refuses_development_or_credential_urls(url):
    with pytest.raises(ValueError, match="cloud HTTPS"):
        release.validate_api_url(url)


def release_environment(monkeypatch, tmp_path):
    values = {"API_BASE_URL": "https://api.example.com/api/v1", "GITHUB_RUN_NUMBER": "45",
        "GITHUB_ENV": str(tmp_path / "github-env"), "ANDROID_KEYSTORE_BASE64": base64.b64encode(b"test-only-key").decode(),
        "ANDROID_KEYSTORE_PASSWORD": "test-only-store", "ANDROID_KEY_ALIAS": "beta",
        "ANDROID_KEY_PASSWORD": "test-only-key-password", "ANDROID_SIGNING_CERT_SHA256": "ab" * 32,
        "GITHUB_SHA": "c" * 40, "GITHUB_RUN_ID": "123", "RELEASE_BUILD_NUMBER": "1045"}
    for name, value in values.items(): monkeypatch.setenv(name, value)
    return values


def test_signing_is_explicit_and_never_overwrites_persistent_material(monkeypatch, tmp_path):
    values = release_environment(monkeypatch, tmp_path)
    android = tmp_path / "android"; android.mkdir()
    result = release.prepare(android, tmp_path / "signing")
    assert result["build_number"] == 1045
    assert "test-only-store" in (android / "key.properties").read_text()
    assert "test-only-store" not in json.dumps(result)
    assert "RELEASE_BUILD_NUMBER=1045" in Path(values["GITHUB_ENV"]).read_text()
    with pytest.raises(ValueError, match="overwrite"):
        release.prepare(android, tmp_path / "signing")
    monkeypatch.delenv("ANDROID_KEYSTORE_BASE64")
    with pytest.raises(ValueError, match="Missing ANDROID_KEYSTORE_BASE64"):
        release.prepare(android, tmp_path / "other")


def test_verify_and_publish_require_the_same_binary_source_and_certificate(monkeypatch, tmp_path):
    release_environment(monkeypatch, tmp_path)
    apk = tmp_path / "DocuMind.apk"; apk.write_bytes(b"test-only-apk")
    def sdk(args, **kwargs):
        return SimpleNamespace(returncode=0, stdout=(
            "Signer #1 certificate SHA-256 digest: " + "ab" * 32 if "verify" in args else
            "package: name='com.ncdanh0311.documind' versionCode='1045' versionName='1.0.0-beta.1'"))
    monkeypatch.setattr(release.subprocess, "run", sdk)
    manifest = release.verify(apk, Path("apksigner"), Path("aapt"), tmp_path)
    assert manifest["sha256"] == hashlib.sha256(apk.read_bytes()).hexdigest()
    monkeypatch.setenv("ACCEPTED_COMMIT", "c" * 40)
    monkeypatch.setenv("SOURCE_RUN_ID", "123")
    publish.validate_artifact(tmp_path)
    apk.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        publish.validate_artifact(tmp_path)
    monkeypatch.setenv("ANDROID_SIGNING_CERT_SHA256", "00" * 32)
    with pytest.raises(ValueError, match="signature"):
        release.verify(apk, Path("apksigner"), Path("aapt"), tmp_path)


@pytest.mark.parametrize("label", ["Signer #1", "Signer (minSdkVersion=33, maxSdkVersion=2147483647)",
    "Signer (minSdkVersion=28, maxSdkVersion=32)"])
def test_certificate_verification_accepts_numbered_and_sdk_range_signers(monkeypatch, label):
    certificate = "ab" * 32
    monkeypatch.setattr(release.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=f"{label} certificate SHA-256 digest: {certificate.upper()}\r\n"))
    release.verify_certificate(Path("test.apk"), Path("apksigner"), certificate)


@pytest.mark.parametrize("stdout,returncode,stderr,error", [
    ("Signer #1 certificate SHA-256 digest: " + "ab" * 32, 1, "DOES NOT VERIFY", "verification failed"),
    ("", 1, "UnsupportedClassVersionError: internal-private-path", "Java runtime"),
    ("Source Stamp Signer certificate SHA-256 digest: " + "ab" * 32, 0, "", "did not report"),
    ("Signer #1 certificate SHA-256 digest: " + "ab" * 32 + "\nSigner #2 certificate SHA-256 digest: " + "cd" * 32,
     0, "", "signature does not match"),
    ("Signer (minSdkVersion=33, maxSdkVersion=2147483647) certificate SHA-256 digest: " + "ab" * 32
     + "\nSigner (minSdkVersion=28, maxSdkVersion=32) certificate SHA-256 digest: " + "cd" * 32,
     0, "", "signature does not match"),
])
def test_certificate_verification_rejects_tool_errors_and_unexpected_signers(monkeypatch, stdout, returncode, stderr, error):
    monkeypatch.setattr(release.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr=stderr))
    with pytest.raises(ValueError, match=error) as result:
        release.verify_certificate(Path("test.apk"), Path("apksigner"), "ab" * 32)
    assert "internal-private-path" not in str(result.value)


def test_publish_refuses_feature_runs_and_skipped_signed_builds(monkeypatch):
    monkeypatch.setenv("SOURCE_RUN_ID", "123")
    monkeypatch.setenv("ACCEPTED_COMMIT", "c" * 40)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    run = {"head_branch": "feature/test", "head_sha": "c" * 40, "conclusion": "success",
        "path": ".github/workflows/ci.yml", "event": "push", "repository": {"full_name": "owner/repo"}}
    monkeypatch.setattr(publish, "get", lambda _: run)
    with pytest.raises(ValueError, match="successful main"):
        publish.validate_source()
    run["head_branch"] = "main"
    monkeypatch.setattr(publish, "get", lambda path: {"jobs": []} if path.endswith("per_page=100") else run)
    with pytest.raises(ValueError, match="signed beta"):
        publish.validate_source()
