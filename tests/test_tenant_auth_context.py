import pytest

from meta_ads_mcp.core.auth import clear_tenant_context, get_current_access_token, set_tenant_context
from meta_ads_mcp.core.tenant_store import TenantAuthContext


@pytest.mark.asyncio
async def test_get_current_access_token_from_context():
    set_tenant_context(
        TenantAuthContext(
            tenant_id="tenant1",
            user_id="u1",
            access_token="token-from-context",
            source="test",
        )
    )
    token = await get_current_access_token()
    clear_tenant_context()
    assert token == "token-from-context"
