"""FastMCP HTTP auth middleware for tenant-scoped self-hosted auth."""

from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .auth import (
    clear_current_app_label,
    clear_tenant_context,
    set_current_app_label,
    set_tenant_context,
    tenant_store,
)
from .tenant_store import TenantAuthContext
from .utils import logger


class FastMCPAuthIntegration:
    @staticmethod
    def extract_bearer(headers: dict) -> Optional[str]:
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
        return None

def patch_fastmcp_server(mcp_server):
    logger.info("Patching FastMCP server for HTTP authentication")
    
    # Store the original run method
    original_run = mcp_server.run
    
    def patched_run(transport="stdio", **kwargs):
        """Enhanced run method that sets up HTTP auth integration"""
        logger.debug(f"Starting FastMCP with transport: {transport}")
        
        if transport == "streamable-http":
            setup_http_auth_patching()
        return original_run(transport=transport, **kwargs)
    
    # Replace the run method
    mcp_server.run = patched_run
    logger.info("FastMCP server patching complete")

def setup_http_auth_patching():
    from . import auth
    from . import api
    from . import authentication
    original = auth.get_current_access_token

    async def get_current_access_token_with_http_support() -> Optional[str]:
        ctx = auth.get_tenant_context()
        if ctx:
            return ctx.access_token
        return await original()

    auth.get_current_access_token = get_current_access_token_with_http_support
    api.get_current_access_token = get_current_access_token_with_http_support
    authentication.get_current_access_token = get_current_access_token_with_http_support

fastmcp_auth = FastMCPAuthIntegration()

def setup_fastmcp_http_auth(mcp_server):
    logger.info("Setting up FastMCP HTTP authentication integration")
    patch_fastmcp_server(mcp_server)

    app_provider_methods: list[str] = []
    if mcp_server.settings.json_response:
        if hasattr(mcp_server, "streamable_http_app") and callable(mcp_server.streamable_http_app):
            app_provider_methods.append("streamable_http_app")
        else:
            logger.warning("mcp_server.streamable_http_app not found or not callable, cannot patch for JSON responses.")
    else: # SSE
        if hasattr(mcp_server, "sse_app") and callable(mcp_server.sse_app):
            app_provider_methods.append("sse_app")
        else:
            logger.warning("mcp_server.sse_app not found or not callable, cannot patch for SSE responses.")

    for method_name in app_provider_methods:
        original_app_provider_method = getattr(mcp_server, method_name)

        def new_patched_app_provider_method(*args, **kwargs):
            app = original_app_provider_method(*args, **kwargs)
            if app:
                setup_starlette_middleware(app)
            return app

        setattr(mcp_server, method_name, new_patched_app_provider_method)
    logger.info("FastMCP HTTP authentication integration setup complete.")

class AuthInjectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        headers = dict(request.headers)
        bearer = FastMCPAuthIntegration.extract_bearer(headers)
        tenant_id = headers.get("x-tenant-id") or headers.get("X-TENANT-ID")
        api_key = headers.get("x-tenant-api-key") or headers.get("X-TENANT-API-KEY")
        app_label = headers.get("x-meta-app-label") or headers.get("X-META-APP-LABEL")
        user_id: Optional[str] = None

        if app_label:
            set_current_app_label(app_label.strip())

        if api_key:
            resolved = tenant_store.resolve_api_key(api_key)
            if resolved:
                tenant_id, user_id = resolved

        if not bearer and tenant_id:
            bearer = tenant_store.get_meta_token(tenant_id)

        if bearer:
            effective_tenant_id = tenant_id or "__header_bearer__"
            set_tenant_context(
                TenantAuthContext(
                    tenant_id=effective_tenant_id,
                    user_id=user_id,
                    access_token=bearer,
                    source="http",
                )
            )

        try:
            response = await call_next(request)
            return response
        finally:
            clear_tenant_context()
            clear_current_app_label()

def setup_starlette_middleware(app):
    if not app:
        return

    already_added = False
    for middleware_item in app.user_middleware:
        if middleware_item.cls == AuthInjectionMiddleware:
            already_added = True
            break

    if not already_added:
        app.add_middleware(AuthInjectionMiddleware)