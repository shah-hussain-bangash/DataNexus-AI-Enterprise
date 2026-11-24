"""Create untracked local PostgreSQL settings without printing credentials."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "portal-db.env"


def main():
    if DEST.exists():
        raise SystemExit("portal-db.env already exists; refusing to overwrite credentials.")
    # URL-safe token has no URL reserved characters (avoid DSN escaping issues).
    secret = secrets.token_urlsafe(48)
    if not all(c.isalnum() or c in "-_" for c in secret):
        raise RuntimeError("Generated unexpected password characters")
    text = ("POSTGRES_USER=datanexus_local\n"
            "POSTGRES_DB=datanexus_audit\n"
            "POSTGRES_PASSWORD=" + secret + "\n")
    with DEST.open("x", encoding="utf-8") as stream:
        stream.write(text)
    if os.name != "nt":
        DEST.chmod(0o600)
    print("Created untracked portal-db.env. Keep this file private; do not commit it.")


if __name__ == "__main__":
    main()
