"""Local-only single-user auth for DataNexus Phase 3A.2.

Uses PBKDF2-HMAC SHA256 credential verification and short-lived HMAC-signed
tokens. NOT enterprise SSO, multi-user RBAC, MFA or identity federation.
"""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Header, HTTPException

ITERATIONS = 260_000
TTL_SECONDS = 8 * 60 * 60


def encode64(raw):
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode64(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    if len(password) < 12:
        raise ValueError("Local administrator password must be at least 12 characters")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2_sha256:{ITERATIONS}:{encode64(salt)}:{encode64(digest)}"


def verify_password(password, stored):
    try:
        algorithm, iterations, salt, expected = stored.split(":")
        rounds = int(iterations)
        if algorithm != "pbkdf2_sha256" or rounds < 200_000 or rounds > 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), decode64(salt), rounds)
        return hmac.compare_digest(actual, decode64(expected))
    except (ValueError, TypeError):
        return False


def settings():
    secret = os.getenv("DATANEXUS_SESSION_SECRET", "")
    username = os.getenv("DATANEXUS_ADMIN_USERNAME", "")
    digest = os.getenv("DATANEXUS_ADMIN_PASSWORD_HASH", "")
    tenant = os.getenv("DATANEXUS_ADMIN_TENANT", "demo")
    if len(secret) < 64 or not username or not digest or not tenant:
        raise RuntimeError("Portal authentication is not configured. Run scripts/create_portal_env.py.")
    return secret.encode("utf-8"), username, digest, tenant


def issue_token(username, role, tenant, secret, now=None):
    timestamp = int(time.time() if now is None else now)
    payload = {"sub": username, "role": role, "tenant_id": tenant,
               "iat": timestamp, "exp": timestamp + TTL_SECONDS, "aud": "datanexus-portal"}
    encoded = encode64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = encode64(hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).digest())
    return encoded + "." + signature


def verify_token(token, secret, now=None):
    try:
        encoded, supplied = token.split(".", 1)
        correct = encode64(hmac.new(secret, encoded.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied, correct):
            return None
        payload = json.loads(decode64(encoded))
        timestamp = int(time.time() if now is None else now)
        if (payload.get("aud") != "datanexus-portal"
                or not isinstance(payload.get("exp"), int)
                or payload["exp"] <= timestamp
                or not isinstance(payload.get("iat"), int)
                or payload["iat"] > timestamp + 30
                or not all(isinstance(payload.get(key), str) and payload[key]
                           for key in ("sub", "role", "tenant_id"))):
            return None
        return payload
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None


def authenticate(username, password):
    secret, configured_username, digest, tenant = settings()
    # Verify password even if username differs to reduce timing differences.
    valid_password = verify_password(password, digest)
    if not hmac.compare_digest(username.encode("utf-8"), configured_username.encode("utf-8")) or not valid_password:
        return None
    return issue_token(configured_username, "admin", tenant, secret)


def require_user(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    secret, configured_username, _, tenant = settings()
    payload = verify_token(authorization[7:], secret)
    if (payload is None or payload["sub"] != configured_username or payload["tenant_id"] != tenant
            or payload["role"] != "admin"):
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return {"username": configured_username, "role": "admin", "tenant_id": tenant}
