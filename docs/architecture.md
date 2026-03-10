# n8n Infrastructure Architecture

## System Overview

The Ascend GTM n8n Cloud instance (`mmurawala.app.n8n.cloud`) is a Universal API Gateway routing requests across 228 actions and 45+ APIs for multiple clients.

## Core Components

### V2 Gateway (PRIMARY)
- **Workflow**: Orchestrate Gateway v2
- **Endpoint**: POST /webhook/orchestrate-v2
- **Request format**: `{domain, action, client, params: {}}`
- **Flow**: Auth Check → Rate Limit → Input Validation → Registry Lookup → Action Lookup → Schema Validation → Route Decision → Handler/Passthrough → Response

### MCP Gateway
- **Workflow**: Universal AI Access Layer
- **Endpoint**: /mcp/ai-gateway/sse (Server-Sent Events)
- **Auth**: Bearer token
- **Connected platforms**: Claude.ai, ChatGPT, Claude Desktop, Perplexity

### Handler Workflows
Domain-specific handlers with credentialed API calls:
- **Google Suite**: Gmail, Calendar, Drive, Docs, Slides, Sheets
- **CRM**: HubSpot, Salesforce
- **Analytics**: GA4, GSC, SEMrush
- **Marketing Ads**: Google Ads, Meta, LinkedIn
- **Internal routing**: Via `x-internal-secret` header

### DataTables
- **Registry** (`s4QNOZysL8K5QAEK`): API registry — domain, base_url, auth_type, credential IDs
- **Actions** (`bnM3EQXYdjZhJwt4`): Action definitions — api_name, action, method, endpoint, body_mode
- **MCP Schemas** (`fSmVnP9qbbqQFAeI`): Input schemas for MCP tool definitions

### Support Workflows
- **E2E Test Suite**: Tests all registered actions, emails HTML report
- **System Audit**: Weekly infrastructure health check (7 categories)
- **Health Monitor**: On-demand health endpoint
- **Rate Limiter**: Per-client budget enforcement
- **GitHub Backups**: Daily workflow + DataTable exports to GitHub
- **Error Handler**: Slack alerts on workflow failures
- **AI Cost Tracker**: Logs AI API spend per request

## Design Principles

1. **Zero hardcoding** — All config via n8n variables and DataTables
2. **Frontend-agnostic** — Works from any AI platform (Claude, ChatGPT, Gemini, Cursor)
3. **Multi-tenant** — Per-client keys, budgets, and permissions
4. **Fail-open on infrastructure, fail-closed on auth** — Rate limits degrade gracefully, auth failures block
5. **Portable** — Change N8N_HOST variable = entire instance relocates

## API Pagination

n8n Cloud DataTable API:
- Max 250 rows per request (NOT 200)
- Uses cursor-based pagination (`nextCursor` in response)
- Variables API: max 100 per page, also cursor-paginated
- Always paginate — never assume single-page results
