# Streamable HTTP Setup (Self-Hosted Native Meta OAuth)

## Overview

This server now supports fully self-hosted multi-tenant authentication, without Pipeboard.  
Use Meta OAuth + tenant-scoped API keys and store tokens in encrypted SQLite.

## Quick Start

### 1) Configure environment

```bash
cp .env.example .env
```

Required variables:

- `META_APP_ID`
- `META_APP_SECRET`
- `OAUTH_REDIRECT_URI`
- `META_MCP_ENCRYPTION_KEY`

### 2) Start HTTP transport

```bash
python -m meta_ads_mcp --transport streamable-http --host 0.0.0.0 --port 8080
```

### 3) Bootstrap tenant authentication

1. Call `mcp_meta_ads_get_login_link` with `tenant_id`
2. Complete Meta OAuth in browser
3. Call `mcp_meta_ads_complete_oauth` with `tenant_id` and authorization `code`
4. Register API key with `mcp_meta_ads_register_tenant_api_key`
5. Grant account access with `mcp_meta_ads_grant_tenant_account_access`

### 4) Make MCP requests

For stateless HTTP requests, include:

- `Authorization: Bearer <meta_access_token>` OR allow server to load token from tenant store
- `X-TENANT-ID: <tenant_id>`
- `X-TENANT-API-KEY: <tenant_api_key>` (recommended)

Example:

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "X-TENANT-ID: tenant-a" \
  -H "X-TENANT-API-KEY: tenant_a_secret_key" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Available Endpoints

### Server URL Structure

**Base URL**: `http://localhost:8080`  
**MCP Endpoint**: `/mcp`

### MCP Protocol Methods

| Method | Description |
|--------|-------------|
| `initialize` | Initialize MCP session and exchange capabilities |
| `tools/list` | Get list of all available Meta Ads tools |
| `tools/call` | Execute a specific tool with parameters |

### Response Format

All responses follow JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    // Tool response data
  }
}
```

## Example Usage

### 1. Initialize Session

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {"roots": {"listChanged": true}},
      "clientInfo": {"name": "my-app", "version": "1.0.0"}
    }
  }'
```

### 2. List Available Tools

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
  }'
```

### 3. Get Ad Accounts

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 3,
    "params": {
      "name": "get_ad_accounts",
      "arguments": {"limit": 10}
    }
  }'
```

### 4. Get Campaign Performance

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "id": 4,
    "params": {
      "name": "get_insights",
      "arguments": {
        "object_id": "act_701351919139047",
        "time_range": "last_30d",
        "level": "campaign"
      }
    }
  }'
```

## Client Examples

### Python Client

```python
import requests
import json

class MetaAdsMCPClient:
    def __init__(self, base_url="http://localhost:8080", token=None):
        self.base_url = base_url
        self.endpoint = f"{base_url}/mcp"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def call_tool(self, tool_name, arguments=None):
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {"name": tool_name}
        }
        if arguments:
            payload["params"]["arguments"] = arguments
        
        response = requests.post(self.endpoint, headers=self.headers, json=payload)
        return response.json()

# Usage
client = MetaAdsMCPClient(token="your_pipeboard_token")
result = client.call_tool("get_ad_accounts", {"limit": 5})
print(json.dumps(result, indent=2))
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class MetaAdsMCPClient {
    constructor(baseUrl = 'http://localhost:8080', token = null) {
        this.baseUrl = baseUrl;
        this.endpoint = `${baseUrl}/mcp`;
        this.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        };
        if (token) {
            this.headers['Authorization'] = `Bearer ${token}`;
        }
    }

    async callTool(toolName, arguments = null) {
        const payload = {
            jsonrpc: '2.0',
            method: 'tools/call',
            id: 1,
            params: { name: toolName }
        };
        if (arguments) {
            payload.params.arguments = arguments;
        }

        try {
            const response = await axios.post(this.endpoint, payload, { headers: this.headers });
            return response.data;
        } catch (error) {
            return { error: error.message };
        }
    }
}

// Usage
const client = new MetaAdsMCPClient('http://localhost:8080', 'your_pipeboard_token');
client.callTool('get_ad_accounts', { limit: 5 })
    .then(result => console.log(JSON.stringify(result, null, 2)));
```

## Production Deployment

### Security Checklist

1. Use HTTPS and terminate TLS at reverse proxy.
2. Rotate `META_MCP_ENCRYPTION_KEY` with controlled migration.
3. Use strong tenant API keys; store only hashes.
4. Restrict network ingress to trusted clients.
5. Monitor audit logs for write operations.

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8080

CMD ["python", "-m", "meta_ads_mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
```

### Environment Variables

```bash
export META_APP_ID=your_app_id
export META_APP_SECRET=your_app_secret
export OAUTH_REDIRECT_URI=https://your-domain.com/callback
export META_MCP_ENCRYPTION_KEY=replace-with-random-secret
export META_MCP_DB_PATH=/data/meta_ads_mcp.db
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure the server is running and accessible on the specified port.
2. **Authentication Failed**: Verify your Bearer token is valid and included in the `Authorization` header.
3. **404 Not Found**: Make sure you're using the correct endpoint (`/mcp`).
4. **JSON-RPC Errors**: Check that your request follows the JSON-RPC 2.0 format.

### Debug Mode

Enable verbose logging by setting the log level in your environment if the application supports it, or check the application's logging configuration. The current implementation logs to a file.

### Health Check

Test if the server is running by sending a `tools/list` request:

```bash
curl -X POST http://localhost:8080/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer your_token" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## Migration from stdio

If you're currently using stdio transport with MCP clients, you can support both stdio for local clients and HTTP for web applications. The application can only run in one mode at a time, so you may need to run two separate instances if you need both simultaneously.

1. **Keep existing MCP client setup** (Claude Desktop, Cursor, etc.) using stdio.
2. **Add HTTP transport** for web applications and custom integrations by running a separate server instance with the `--transport streamable-http` flag.
3. **Use the same authentication method**:
    - For stdio, the `PIPEBOARD_API_TOKEN` environment variable is used.
    - For HTTP, pass the token in the `Authorization: Bearer <token>` header.

Both transports access the same Meta Ads functionality and use the same underlying authentication system. 