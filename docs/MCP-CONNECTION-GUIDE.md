# MCP Connection Guide — Ascend Gateway

> **Last updated:** 2026-03-12  
> **MCP Server:** `https://mmurawala.app.n8n.cloud/mcp/ai-gateway/sse`  
> **API Key:** `mcp_gateway_master_2026`  
> **Actions:** 281 across 36 domains

---

## Platform 1: Claude.ai ✅ Done

Already connected via first-party connector. No action needed.

---

## Platform 2: ChatGPT (web → auto-syncs to macOS + iOS)

1. Go to [chat.openai.com](https://chat.openai.com)
2. Click **Profile icon → Settings → Connectors → Create**
   - If "Connectors" is missing: **Settings → Beta features → turn on Developer Mode**
3. Fill in:

| Field | Value |
|---|---|
| **Server URL** | `https://mmurawala.app.n8n.cloud/mcp-server/http` |
| **Name** | `Ascend Gateway` |
| **Description** | `n8n Universal API Gateway — 281 actions across 36 domains` |

4. Click **Save**
5. ChatGPT will auto-discover n8n Cloud's OAuth → browser login to your n8n instance → Approve
6. ✅ Tools appear in chat. macOS Desktop + iOS sync automatically.

---

## Platform 3: Perplexity (web)

1. Go to [perplexity.ai](https://perplexity.ai)
2. **Profile → Settings → Connectors → + Custom connector → Remote**
3. Fill in:

| Field | Value |
|---|---|
| **Name** | `Ascend Gateway` |
| **MCP Server URL** | `https://mmurawala.app.n8n.cloud/mcp/ai-gateway/sse` |
| **Description** | `n8n Universal API Gateway` |
| **Authentication** | `API Key` |
| **API Key** | `mcp_gateway_master_2026` |
| **Transport** | `SSE` |

4. Check the acknowledgement box → **Add**
5. Click the connector card to **Enable**
6. In queries, toggle it on under **Sources**

---

## Platform 4: Claude Desktop (macOS)

### Step 1 — Create config directory
```bash
mkdir -p "$HOME/Library/Application Support/Claude"
```

### Step 2 — Open config file
```bash
open -a TextEdit "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
```

### Step 3 — Paste this JSON
```json
{
  "mcpServers": {
    "ascend-gateway": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote",
        "https://mmurawala.app.n8n.cloud/mcp/ai-gateway/sse",
        "--header",
        "Authorization: Bearer mcp_gateway_master_2026"
      ]
    }
  }
}
```

### Step 4 — Restart
- **Save** the file → **Cmd+Q** Claude Desktop → **Reopen**
- Tools appear within 10–15 seconds ✅

---

## Platform 5: Gemini (CLI only — web/iOS not supported)

### Install Gemini CLI
```bash
npm install -g @google/gemini-cli
```

### Create config
```bash
mkdir -p ~/.gemini
```

Edit `~/.gemini/settings.json`:
```json
{
  "mcpServers": {
    "ascend-gateway": {
      "uri": "https://mmurawala.app.n8n.cloud/mcp/ai-gateway/sse",
      "headers": {
        "Authorization": "Bearer mcp_gateway_master_2026"
      }
    }
  }
}
```

### Verify
```bash
gemini
# then type:
/mcp
```

---

## iOS Summary

| App | Works? | Action Required |
|---|---|---|
| Claude iOS | ✅ | Synced from claude.ai — nothing |
| ChatGPT iOS | ✅ | Syncs after web setup — nothing |
| Perplexity iOS | ❌ | No MCP on mobile yet |
| Gemini iOS | ❌ | No MCP on mobile |

---

## Quick Reference

| Platform | Transport | Auth | Status |
|---|---|---|---|
| Claude.ai | Native | First-party | ✅ Live |
| ChatGPT | HTTP (OAuth) | n8n Cloud OAuth | Needs web setup |
| Perplexity | SSE | API Key | Needs web setup |
| Claude Desktop | SSE via npx | Bearer token | Needs JSON config |
| Gemini | SSE | Bearer token | CLI only |
