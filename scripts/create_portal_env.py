"""Create an untracked local portal.env; no credentials are printed or committed.

Run from the project root: python scripts/create_portal_env.py
"""
import getpass
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from auth import hash_password  # noqa: E402

destination = ROOT / "portal.env"


def main():
    if destination.exists():
        raise SystemExit("portal.env already exists; refusing to overwrite your current credentials.")
    username = input("Local administrator username [admin]: ").strip() or "admin"
    tenant = input("Aviation tenant ID [demo]: ").strip() or "demo"
    if not username.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("Username must use letters, digits, underscores or hyphens.")
    if not tenant.replace("_", "").replace("-", "").isalnum():
        raise SystemExit("Tenant must use letters, digits, underscores or hyphens.")
    password = getpass.getpass("Choose a strong administrator password (12+ characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if password != confirmation:
        raise SystemExit("Passwords did not match; nothing was saved.")
    try:
        digest = hash_password(password)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    lines = [
        "DATANEXUS_ADMIN_USERNAME=" + username,
        "DATANEXUS_ADMIN_TENANT=" + tenant,
        "DATANEXUS_ADMIN_PASSWORD_HASH=" + digest,
        "DATANEXUS_SESSION_SECRET=" + secrets.token_hex(48),
    ]
    with destination.open("x", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
    if os.name != "nt":
        destination.chmod(0o600)
    print("Local credentials configured in portal.env (Git-ignored). Keep the file private.")


if __name__ == "__main__":
    main()
