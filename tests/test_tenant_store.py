import tempfile
from pathlib import Path

from meta_ads_mcp.core.tenant_store import TenantStore


def test_tenant_store_token_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "mcp.db"
        store = TenantStore(db_path=str(db_path), encryption_key="unit-test-key")
        store.store_meta_token("tenant1", "meta-token-abc")
        assert store.get_meta_token("tenant1") == "meta-token-abc"


def test_tenant_api_key_and_account_mapping():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "mcp.db"
        store = TenantStore(db_path=str(db_path), encryption_key="unit-test-key")
        store.register_api_key("tenant1", "secret-key", user_id="u1")
        tenant, user = store.resolve_api_key("secret-key")
        assert tenant == "tenant1"
        assert user == "u1"
        store.grant_account_access("tenant1", "act_123")
        assert store.has_account_access("tenant1", "act_123") is True
