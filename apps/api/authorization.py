"""P0.3 local API authorization policy.

This is a fail-closed authorization layer for a single local administrator,
NOT enterprise multi-user RBAC, MFA, SSO, or an organization identity provider.
Permissions are checked on the API, never inferred from frontend navigation.
"""
from fastapi import Depends, HTTPException
from auth import require_user

PERMISSIONS = {
    "admin": frozenset({
        "aviation:read", "quality:read", "overview:read", "audit:read"
    }),
}

def permitted(user, permission):
    """Deny missing, unknown or inconsistent claims."""
    if not isinstance(user, dict):
        return False
    role = user.get("role")
    tenant = user.get("tenant_id")
    username = user.get("username")
    return (isinstance(role, str) and
            isinstance(tenant, str) and bool(tenant.strip()) and
            isinstance(username, str) and bool(username.strip()) and
            isinstance(permission, str) and
            permission in PERMISSIONS.get(role, frozenset()))

def require_permission(permission):
    """Return a FastAPI dependency enforcing a named permission."""
    if not isinstance(permission, str) or not any(
        permission in allowed for allowed in PERMISSIONS.values()
    ):
        raise ValueError("Undefined API permission")

    def check(user: dict = Depends(require_user)):
        if not permitted(user, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check

def require_tenant(user, requested_tenant=None):
    """Prevent clients selecting or overriding a different tenant.

    For now, every request is tied to the verified token's tenant.
    No user-controlled tenant switching is supported.
    """
    if not isinstance(user, dict):
        raise HTTPException(status_code=403, detail="Tenant access denied")
    tenant = user.get("tenant_id")
    if not isinstance(tenant, str) or not tenant.strip():
        raise HTTPException(status_code=403, detail="Tenant access denied")
    if requested_tenant is not None and requested_tenant != tenant:
        raise HTTPException(status_code=403, detail="Tenant access denied")
    return tenant
