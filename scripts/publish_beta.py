"""Validate provenance before the operator-approved beta publication."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

from scripts.android_release import APPLICATION_ID, VERSION, validate_api_url


def get(path):
    repository = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("Invalid repository")
    request = urllib.request.Request(f"https://api.github.com/repos/{repository}{path}", headers={
        "Authorization": "Bearer " + os.environ["GH_TOKEN"], "User-Agent": "DocuMind-Beta-Release",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def validate_source():
    run_id, commit = os.environ["SOURCE_RUN_ID"], os.environ["ACCEPTED_COMMIT"]
    if not run_id.isdigit() or not re.fullmatch(r"[a-f0-9]{40}", commit):
        raise ValueError("Expected a numeric CI run ID and full commit SHA")
    run = get(f"/actions/runs/{run_id}")
    if (run["head_branch"] != "main" or run["head_sha"] != commit or run["conclusion"] != "success"
            or run["path"] != ".github/workflows/ci.yml" or run["event"] not in ("push", "workflow_dispatch")
            or run["repository"]["full_name"] != os.environ["GITHUB_REPOSITORY"]):
        raise ValueError("Source must be a successful main CI run of this repository")
    jobs = get(f"/actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    if not any(j["name"] == "Signed Android Beta (Main Only)" and j["conclusion"] == "success" for j in jobs):
        raise ValueError("Source run has no successful signed beta build")
    # An existing tag must never be moved to a different binary/source commit.
    try:
        get(f"/git/ref/tags/v{VERSION}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404: raise
    else:
        raise ValueError("Beta tag already exists; create a new version instead of replacing it")


def validate_artifact(directory):
    manifest = json.loads((directory / "release-manifest.json").read_text(encoding="utf-8"))
    expected = {"version": VERSION, "application_id": APPLICATION_ID,
                "commit": os.environ["ACCEPTED_COMMIT"], "run_id": os.environ["SOURCE_RUN_ID"],
                "api_base_url": validate_api_url(os.environ["API_BASE_URL"]),
                "signing_certificate_sha256": os.environ["ANDROID_SIGNING_CERT_SHA256"].replace(":", "").lower()}
    if any(manifest.get(key) != value for key, value in expected.items()):
        raise ValueError("Release artifact provenance does not match the accepted build")
    name = manifest["apk"]
    if Path(name).name != name or "\\" in name or not name.endswith(".apk"):
        raise ValueError("Invalid APK filename")
    apk = directory / name
    if not apk.resolve().is_relative_to(directory.resolve()): raise ValueError("Invalid APK path")
    with apk.open("rb") as stream: digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if manifest["sha256"] != digest or (directory / "SHA256SUMS").read_text(encoding="utf-8") != f"{digest}  {name}\n":
        raise ValueError("APK checksum mismatch")
    if sorted(p.name for p in directory.glob("*.apk")) != [name]:
        raise ValueError("Unexpected additional APK")
    (directory / "RELEASE_NOTES.md").write_text(
        f"DocuMind {VERSION} — bản beta cá nhân, cài trực tiếp bằng APK.\n\n"
        f"- Commit: `{manifest['commit']}`\n- Android versionCode: `{manifest['build_number']}`\n"
        f"- SHA-256: `{digest}`\n- Chữ ký SHA-256: `{manifest['signing_certificate_sha256']}`\n\n"
        "Đã xác nhận nghiệm thu cloud và Android trước khi công bố. AI tiếp tục tạm hoãn.\n"
        "Bản beta dùng mã ứng dụng riêng; các bản beta sau dùng cùng khóa ký để cập nhật.\n",
        encoding="utf-8")


if __name__ == "__main__":
    try:
        if sys.argv[1] == "source": validate_source()
        elif sys.argv[1] == "artifact": validate_artifact(Path("release-artifacts"))
        else: raise ValueError("Unknown command")
    except Exception as exc:
        print(str(exc) if isinstance(exc, ValueError) else f"Publication validation failed ({type(exc).__name__})")
        raise SystemExit(1) from None
