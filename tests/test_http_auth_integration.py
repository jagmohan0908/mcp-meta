from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient
from starlette.routing import Route

from meta_ads_mcp.core.auth import get_tenant_context
from meta_ads_mcp.core.http_auth_integration import setup_starlette_middleware


def test_bearer_header_sets_tenant_context_without_tenant_id():
    async def check(request):
        ctx = get_tenant_context()
        return JSONResponse(
            {
                "tenant_id": ctx.tenant_id if ctx else None,
                "access_token": ctx.access_token if ctx else None,
            }
        )

    app = Starlette(routes=[Route("/check", check)])

    setup_starlette_middleware(app)

    client = TestClient(app)
    response = client.get(
        "/check",
        headers={
            "Authorization": "Bearer test-token-123",
            "X-META-APP-LABEL": "SIYA_App",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "__header_bearer__"
    assert payload["access_token"] == "test-token-123"
