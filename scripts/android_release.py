"""Prepare and verify an Android beta on a trusted CI runner. Never print secrets."""
import argparse
import base64
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit

APPLICATION_ID = "com.ncdanh0311.documind"
VERSION = "1.0.0-beta.1"


def validate_api_url(value):
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        if (value != value.strip() or url.scheme != "https" or not host or "." not in host
                or url.username or url.password or url.query or url.fragment or url.path != "/api/v1"
                or host == "localhost" or host.endswith((".local", ".localhost", ".internal"))
                or url.port not in (None, 443)):
            raise ValueError
        # Production endpoints use DNS names, never developer machine addresses.
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return value
        raise ValueError
    except ValueError:
        raise ValueError("API_BASE_URL must be a cloud HTTPS URL ending in /api/v1") from None


def required(name):
    value = os.environ.get(name, "")
    if not value:
        raise ValueError(f"Missing {name}")
    return value


def prepare(android_dir, temporary_dir):
    api_url = validate_api_url(required("API_BASE_URL"))
    run_number = int(required("GITHUB_RUN_NUMBER"))
    build_number = run_number + 1000
    if not 1000 < build_number < 2100000000:
        raise ValueError("Invalid Android build number")
    certificate = required("ANDROID_SIGNING_CERT_SHA256").replace(":", "").lower()
    if not re.fullmatch(r"[a-f0-9]{64}", certificate):
        raise ValueError("Invalid expected signing certificate")
    encoded = required("ANDROID_KEYSTORE_BASE64")
    try:
        keystore = base64.b64decode(encoded, validate=True)
    except ValueError:
        raise ValueError("Invalid encoded Android keystore") from None
    if not keystore:
        raise ValueError("Empty Android keystore")
    values = {name: required(env) for name, env in (
        ("storePassword", "ANDROID_KEYSTORE_PASSWORD"), ("keyAlias", "ANDROID_KEY_ALIAS"),
        ("keyPassword", "ANDROID_KEY_PASSWORD"))}
    temporary_dir.mkdir(parents=True, exist_ok=True)
    key_path = (temporary_dir / "documind-release.jks").resolve()
    # This path belongs to the current ephemeral CI runner, not a user's existing keystore.
    if key_path.exists() or (android_dir / "key.properties").exists():
        raise ValueError("Refusing to overwrite existing signing material")
    key_path.write_bytes(keystore)
    key_path.chmod(0o600)
    values["storeFile"] = key_path.as_posix()
    def escape(value):
        return value.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")
    properties = android_dir / "key.properties"
    properties.write_text("".join(f"{key}={escape(value)}\n" for key, value in values.items()), encoding="utf-8")
    properties.chmod(0o600)
    with Path(required("GITHUB_ENV")).open("a", encoding="utf-8") as output:
        output.write(f"RELEASE_BUILD_NUMBER={build_number}\nRELEASE_VERSION={VERSION}\n")
    return {"application_id": APPLICATION_ID, "version": VERSION, "build_number": build_number, "api_url": api_url}


def verify_certificate(apk, apksigner, expected):
    signed = subprocess.run([str(apksigner), "verify", "--verbose", "--print-certs", str(apk)],
                            capture_output=True, text=True, timeout=60)
    if signed.returncode:
        # This SDK command only reads the APK. Keep diagnostics separate from a
        # valid signature made by a different key, without printing private paths.
        error = getattr(signed, "stderr", "") or ""
        if "UnsupportedClassVersionError" in error:
            raise ValueError("apksigner cannot run with the configured Java runtime")
        raise ValueError(f"apksigner verification failed (exit {signed.returncode})")
    # SDK 37 prefixes labels with the signature scheme ('V2 Signer:'); v3.1
    # signers may include an SDK range. Older tools use 'Signer #1'. Verify
    # every reported application signer; a source stamp is a separate identity.
    fingerprints = re.findall(
        r"^(?:V[1-4](?:\.\d+)? )?Signer(?: #\d+| \([^\r\n]+\))?:? certificate SHA-256 digest:[ \t]*([a-fA-F0-9]{64})[ \t\r]*$",
        signed.stdout, re.MULTILINE,
    )
    if not fingerprints:
        raise ValueError("apksigner did not report an application signing certificate")
    if any(fingerprint.lower() != expected for fingerprint in fingerprints):
        actual = ", ".join(sorted({fingerprint.lower() for fingerprint in fingerprints}))
        raise ValueError(f"APK signature does not match the persistent release certificate (actual SHA-256: {actual})")


def verify(apk, apksigner, aapt, output):
    expected = required("ANDROID_SIGNING_CERT_SHA256").replace(":", "").lower()
    verify_certificate(apk, apksigner, expected)
    package = subprocess.run([str(aapt), "dump", "badging", str(apk)], capture_output=True, text=True, timeout=60)
    if package.returncode:
        raise ValueError("Cannot inspect APK package")
    metadata = re.search(r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'", package.stdout)
    build_number = int(required("RELEASE_BUILD_NUMBER"))
    if not metadata or tuple(metadata.groups()) != (APPLICATION_ID, str(build_number), VERSION):
        raise ValueError("APK package/version does not match the release")
    if "application-debuggable" in package.stdout:
        raise ValueError("Release APK must not be debuggable")
    api_url = validate_api_url(required("API_BASE_URL"))
    sha = required("GITHUB_SHA")
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Invalid source commit")
    with apk.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    output.mkdir(parents=True, exist_ok=True)
    manifest = {"format": 1, "version": VERSION, "build_number": build_number, "application_id": APPLICATION_ID,
                "commit": sha, "api_base_url": api_url, "signing_certificate_sha256": expected,
                "apk": apk.name, "sha256": digest, "run_id": required("GITHUB_RUN_ID")}
    (output / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / "SHA256SUMS").write_text(f"{digest}  {apk.name}\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "verify"))
    parser.add_argument("--android-dir", type=Path, default=Path("mobile/android"))
    parser.add_argument("--temporary-dir", type=Path)
    parser.add_argument("--apk", type=Path)
    parser.add_argument("--apksigner", type=Path)
    parser.add_argument("--aapt", type=Path)
    parser.add_argument("--output", type=Path, default=Path("release-artifacts"))
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            if not args.temporary_dir: raise ValueError("--temporary-dir required")
            result = prepare(args.android_dir, args.temporary_dir)
        else:
            if not all((args.apk, args.apksigner, args.aapt)): raise ValueError("APK and Android SDK tools required")
            result = verify(args.apk, args.apksigner, args.aapt, args.output)
        print(json.dumps(result))
    except Exception as exc:
        # SDK/provider exception messages may contain credentials or private paths.
        print(str(exc) if isinstance(exc, ValueError) else f"Android release failed ({type(exc).__name__})")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
