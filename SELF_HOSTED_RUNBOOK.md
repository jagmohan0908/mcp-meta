# Self-Hosted Multi-Tenant Runbook

## 1) Environment

Set required values:

- `META_APP_ID`
- `META_APP_SECRET`
- `OAUTH_REDIRECT_URI`
- `META_MCP_ENCRYPTION_KEY`
- `META_MCP_DB_PATH` (optional; defaults under user home)

## 2) Start server

```bash
python -m meta_ads_mcp --transport streamable-http --host 0.0.0.0 --port 8080
```

## 3) Tenant bootstrap

1. Call `mcp_meta_ads_get_login_link(tenant_id)`
2. Complete Meta OAuth and copy authorization `code`
3. Call `mcp_meta_ads_complete_oauth(tenant_id, code)`
4. Call `mcp_meta_ads_register_tenant_api_key(tenant_id, api_key)`
5. Call `mcp_meta_ads_grant_tenant_account_access(tenant_id, account_id)`

## 4) Antigravity HTTP request headers

Include:

- `X-TENANT-ID: <tenant_id>`
- `X-TENANT-API-KEY: <tenant_api_key>`
- Optional: `Authorization: Bearer <meta_access_token>`

If `Authorization` is omitted, middleware loads token from tenant store.

## 5) Validation checklist

- `tools/list` succeeds with tenant headers
- `mcp_meta_ads_get_ad_accounts` succeeds
- `mcp_meta_ads_get_campaigns(account_id)` works only for granted accounts
- Cross-tenant request with wrong API key fails
- Token lifecycle: `mcp_meta_ads_refresh_tenant_token(tenant_id)` succeeds
