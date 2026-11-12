"""Authorize one sender via Google's OAuth library; save only outside the repo."""
import argparse
import json
import logging
import os
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-file", required=True, type=Path)
    parser.add_argument("--sender", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    repo = Path(__file__).resolve().parents[1]
    if output.is_relative_to(repo) or output.exists():
        raise ValueError("Output must be a new file outside the repository")
    if "@" not in args.sender or any(char in args.sender for char in "\r\n"):
        raise ValueError("A sender email is required")
    client = json.loads(args.client_file.read_text(encoding="utf-8"))
    if "installed" not in client:
        raise ValueError("Use a Google OAuth Desktop app client JSON file")
    google = client["installed"]
    if (google.get("auth_uri") not in ("https://accounts.google.com/o/oauth2/auth", "https://accounts.google.com/o/oauth2/v2/auth")
            or google.get("token_uri") != "https://oauth2.googleapis.com/token"):
        raise ValueError("OAuth client endpoints must be Google's official HTTPS endpoints")
    output.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        identity = subprocess.run(["whoami"], capture_output=True, text=True, check=True).stdout.strip()
        result = subprocess.run(["icacls", str(output.parent), "/inheritance:r", "/grant:r",
                                 identity + ":(OI)(CI)F", "SYSTEM:(OI)(CI)F"], capture_output=True)
        if result.returncode:
            raise ValueError("Could not restrict credential directory permissions")
    else:
        output.parent.chmod(0o700)
    from google_auth_oauthlib.flow import InstalledAppFlow
    # The loopback callback contains an authorization code; never log its URL.
    logging.getLogger("google_auth_oauthlib.flow").setLevel(logging.CRITICAL)
    flow = InstalledAppFlow.from_client_config(client, scopes=["https://www.googleapis.com/auth/gmail.send"],
                                              autogenerate_code_verifier=True)
    credentials = flow.run_local_server(host="127.0.0.1", port=0, open_browser=True,
        authorization_prompt_message="", success_message="Gmail connected. You can close this tab.",
        timeout_seconds=300, login_hint=args.sender, prompt="consent", access_type="offline")
    if not credentials.refresh_token:
        raise ValueError("Google did not grant offline access; authorize the sender again")
    values = {"EMAIL_PROVIDER": "gmail_api", "GMAIL_SENDER_EMAIL": args.sender,
              "GMAIL_CLIENT_ID": credentials.client_id, "GMAIL_CLIENT_SECRET": credentials.client_secret,
              "GMAIL_REFRESH_TOKEN": credentials.refresh_token}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(values, stream, indent=2)
    if os.name != "nt":
        output.chmod(0o600)
    print("Gmail authorized. Configuration saved outside the repository; no secret values printed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc) if isinstance(exc, ValueError) else f"Gmail authorization failed ({type(exc).__name__})")
        raise SystemExit(1) from None
