"""Authentication tools for self-hosted native Meta OAuth."""

import json
from typing import Optional

import httpx

from .auth import auth_manager, get_current_app_label, meta_config, tenant_store
from .server import mcp_server
from .utils import logger


async def get_login_link(tenant_id: str, state: Optional[str] = None, app_label: Optional[str] = None) -> str:
    """Generate a Meta OAuth URL for a specific tenant."""
    effective_label = app_label or get_current_app_label()
    profile = meta_config.get_app_profile(effective_label)
    if not (profile.app_id and profile.oauth_redirect_uri):
        return json.dumps(
            {
                "error": "META_APP_ID and OAUTH_REDIRECT_URI must be configured for OAuth.",
            },
            indent=2,
        )
    tenant_store.ensure_tenant(tenant_id)
    login_url = auth_manager.get_auth_url(tenant_id=tenant_id, state=state, app_label=effective_label)
    return json.dumps(
        {
            "tenant_id": tenant_id,
            "app_label": profile.label,
            "login_url": login_url,
            "markdown_link": f"[Authenticate tenant {tenant_id}]({login_url})",
            "instructions": "After granting access, exchange the code with mcp_meta_ads_complete_oauth.",
        },
        indent=2,
    )


async def complete_oauth(tenant_id: str, code: str, app_label: Optional[str] = None) -> str:
    """Exchange OAuth authorization code and persist tenant token."""
    effective_label = app_label or get_current_app_label()
    profile = meta_config.get_app_profile(effective_label)
    app_id = profile.app_id
    app_secret = profile.app_secret
    redirect_uri = profile.oauth_redirect_uri
    if not (app_id and app_secret and redirect_uri):
        return json.dumps(
            {"error": "META_APP_ID, META_APP_SECRET and OAUTH_REDIRECT_URI are required."},
            indent=2,
        )

    token_url = "https://graph.facebook.com/v24.0/oauth/access_token"
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(token_url, params=params)
        response.raise_for_status()
        token_data = response.json()

    access_token = token_data.get("access_token")
    if not access_token:
        return json.dumps({"error": "OAuth exchange did not return access_token."}, indent=2)

    tenant_store.store_meta_token(
        tenant_id=tenant_id,
        access_token=access_token,
        expires_at=token_data.get("expires_in"),
        app_label=profile.label,
    )
    logger.info("Stored OAuth token for tenant %s", tenant_id)
    return json.dumps(
        {"status": "ok", "tenant_id": tenant_id, "app_label": profile.label, "expires_in": token_data.get("expires_in")},
        indent=2,
    )


async def refresh_tenant_token(tenant_id: str, app_label: Optional[str] = None) -> str:
    """Refresh token lifecycle using Meta long-lived token exchange."""
    effective_label = app_label or get_current_app_label()
    profile = meta_config.get_app_profile(effective_label)
    app_id = profile.app_id
    app_secret = profile.app_secret
    current_token = tenant_store.get_meta_token(tenant_id)
    if not (app_id and app_secret and current_token):
        return json.dumps(
            {"error": "Missing tenant token or META_APP_ID/META_APP_SECRET configuration."},
            indent=2,
        )

    token_url = "https://graph.facebook.com/v24.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": current_token,
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(token_url, params=params)
        response.raise_for_status()
        token_data = response.json()

    new_token = token_data.get("access_token")
    if not new_token:
        return json.dumps({"error": "Meta did not return refreshed token."}, indent=2)
    tenant_store.store_meta_token(
        tenant_id=tenant_id,
        access_token=new_token,
        expires_at=token_data.get("expires_in"),
    )
    return json.dumps(
        {"status": "ok", "tenant_id": tenant_id, "refreshed": True, "expires_in": token_data.get("expires_in")},
        indent=2,
    )


async def register_tenant_api_key(tenant_id: str, api_key: str, user_id: Optional[str] = None) -> str:
    """Register/rotate tenant API key used by HTTP middleware."""
    tenant_store.register_api_key(tenant_id=tenant_id, api_key=api_key, user_id=user_id)
    return json.dumps({"status": "ok", "tenant_id": tenant_id, "api_key_registered": True}, indent=2)


async def grant_tenant_account_access(tenant_id: str, account_id: str) -> str:
    """Whitelist ad account for tenant-scoped authorization."""
    normalized_id = account_id if account_id.startswith("act_") else f"act_{account_id}"
    tenant_store.grant_account_access(tenant_id=tenant_id, account_id=normalized_id)
    return json.dumps({"status": "ok", "tenant_id": tenant_id, "account_id": normalized_id}, indent=2)


get_login_link = mcp_server.tool(name="mcp_meta_ads_get_login_link")(get_login_link)
complete_oauth = mcp_server.tool(name="mcp_meta_ads_complete_oauth")(complete_oauth)
refresh_tenant_token = mcp_server.tool(name="mcp_meta_ads_refresh_tenant_token")(refresh_tenant_token)
register_tenant_api_key = mcp_server.tool(name="mcp_meta_ads_register_tenant_api_key")(register_tenant_api_key)
grant_tenant_account_access = mcp_server.tool(name="mcp_meta_ads_grant_tenant_account_access")(grant_tenant_account_access)