"""Native multi-tenant authentication and OAuth helpers for Meta Ads MCP."""

from __future__ import annotations

import contextvars
import os
from dataclasses import dataclass
from typing import Optional

from .utils import logger
from .tenant_store import TenantAuthContext, TenantStore

AUTH_SCOPE = "business_management,public_profile,pages_show_list,pages_read_engagement,ads_read,ads_management"
AUTH_RESPONSE_TYPE = "code"
needs_authentication = False

_current_tenant_context: contextvars.ContextVar[Optional[TenantAuthContext]] = contextvars.ContextVar(
    "current_tenant_context", default=None
)


class MetaConfig:
    def __init__(self):
        self.app_id = os.environ.get("META_APP_ID", "")
        self.app_secret = os.environ.get("META_APP_SECRET", "")
        self.redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8888/callback")

    def set_app_id(self, app_id: str) -> None:
        self.app_id = app_id
        os.environ["META_APP_ID"] = app_id

    def get_app_id(self) -> str:
        return self.app_id

    def is_configured(self) -> bool:
        return bool(self.app_id and self.redirect_uri)


@dataclass
class AuthManager:
    app_id: str
    redirect_uri: str

    @property
    def use_pipeboard(self) -> bool:
        return False

    def get_auth_url(self, tenant_id: str, state: Optional[str] = None) -> str:
        state_value = state or tenant_id
        return (
            "https://www.facebook.com/v24.0/dialog/oauth?"
            f"client_id={self.app_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope={AUTH_SCOPE}&"
            f"response_type={AUTH_RESPONSE_TYPE}&"
            f"state={state_value}"
        )

    def get_access_token(self) -> Optional[str]:
        ctx = get_tenant_context()
        if ctx and ctx.access_token:
            return ctx.access_token
        env_token = os.environ.get("META_ACCESS_TOKEN")
        return env_token or None

    def invalidate_token(self) -> None:
        logger.warning("invalidate_token called for tenant-scoped auth; clear via tenant storage rotation.")

    def clear_token(self) -> None:
        self.invalidate_token()


meta_config = MetaConfig()
auth_manager = AuthManager(app_id=meta_config.get_app_id(), redirect_uri=meta_config.redirect_uri)
_default_key = os.environ.get("META_MCP_ENCRYPTION_KEY")
if not _default_key:
    _default_key = "dev-only-change-me"
    logger.warning("META_MCP_ENCRYPTION_KEY not set; using insecure development key.")
tenant_store = TenantStore(encryption_key=_default_key)


def set_tenant_context(context: TenantAuthContext) -> None:
    _current_tenant_context.set(context)


def clear_tenant_context() -> None:
    _current_tenant_context.set(None)


def get_tenant_context() -> Optional[TenantAuthContext]:
    return _current_tenant_context.get()


async def get_current_access_token() -> Optional[str]:
    ctx = get_tenant_context()
    if ctx and ctx.access_token:
        return ctx.access_token

    env_token = os.environ.get("META_ACCESS_TOKEN")
    if env_token:
        return env_token
    return None


def login() -> None:
    print("Use `mcp_meta_ads_get_login_link` with your tenant_id to complete OAuth.")