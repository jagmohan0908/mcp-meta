"""Native multi-tenant authentication and OAuth helpers for Meta Ads MCP."""

from __future__ import annotations

import contextvars
import json
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
_current_app_label: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_app_label", default=None
)


@dataclass
class AppProfile:
    label: str
    app_id: str
    app_secret: str
    oauth_redirect_uri: str


class MetaConfig:
    def __init__(self):
        self.default_redirect_uri = os.environ.get("OAUTH_REDIRECT_URI", "http://localhost:8888/callback")
        self._profiles = self._load_profiles()
        default = self.get_app_profile()
        self.app_id = default.app_id
        self.app_secret = default.app_secret
        self.redirect_uri = default.oauth_redirect_uri

    def _load_profiles(self) -> dict[str, AppProfile]:
        profiles: dict[str, AppProfile] = {}
        profiles_json = os.environ.get("META_APP_CREDENTIALS_JSON", "").strip()
        if profiles_json:
            try:
                raw = json.loads(profiles_json)
                if isinstance(raw, dict):
                    for label, cfg in raw.items():
                        if not isinstance(cfg, dict):
                            continue
                        app_id = str(cfg.get("app_id", "")).strip()
                        app_secret = str(cfg.get("app_secret", "")).strip()
                        oauth_redirect_uri = str(cfg.get("oauth_redirect_uri", self.default_redirect_uri)).strip()
                        if app_id and app_secret:
                            profiles[label] = AppProfile(
                                label=label,
                                app_id=app_id,
                                app_secret=app_secret,
                                oauth_redirect_uri=oauth_redirect_uri or self.default_redirect_uri,
                            )
            except json.JSONDecodeError:
                logger.warning("Invalid META_APP_CREDENTIALS_JSON; falling back to single-app env vars.")

        if "default" not in profiles:
            single_app_id = os.environ.get("META_APP_ID", "").strip()
            single_app_secret = os.environ.get("META_APP_SECRET", "").strip()
            profiles["default"] = AppProfile(
                label="default",
                app_id=single_app_id,
                app_secret=single_app_secret,
                oauth_redirect_uri=self.default_redirect_uri,
            )
        return profiles

    def set_app_id(self, app_id: str) -> None:
        self.app_id = app_id
        os.environ["META_APP_ID"] = app_id
        default_profile = self._profiles.get("default")
        if default_profile:
            default_profile.app_id = app_id

    def get_app_id(self) -> str:
        return self.get_app_profile().app_id

    def get_app_profile(self, label: Optional[str] = None) -> AppProfile:
        if label and label in self._profiles:
            return self._profiles[label]
        if "default" in self._profiles:
            return self._profiles["default"]
        first_key = next(iter(self._profiles))
        return self._profiles[first_key]

    def is_configured(self) -> bool:
        profile = self.get_app_profile(get_current_app_label())
        return bool(profile.app_id and profile.oauth_redirect_uri)


@dataclass
class AuthManager:
    app_id: str
    redirect_uri: str

    @property
    def use_pipeboard(self) -> bool:
        return False

    def get_auth_url(self, tenant_id: str, state: Optional[str] = None, app_label: Optional[str] = None) -> str:
        state_value = state or tenant_id
        profile = meta_config.get_app_profile(app_label or get_current_app_label())
        return (
            "https://www.facebook.com/v24.0/dialog/oauth?"
            f"client_id={profile.app_id}&"
            f"redirect_uri={profile.oauth_redirect_uri}&"
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


def set_current_app_label(label: Optional[str]) -> None:
    _current_app_label.set(label)


def get_current_app_label() -> Optional[str]:
    return _current_app_label.get()


def clear_current_app_label() -> None:
    _current_app_label.set(None)


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