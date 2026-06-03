# aidd-kos — Agentic Knowledge OS

LightRAG knowledge graph + MCP server for AI-driven development.

## What it does

- **Knowledge graph**: Indexes your project documents (Markdown, text) into a LightRAG graph database
- **MCP server**: Exposes the knowledge graph as MCP tools for Claude Code, Claude Desktop, etc.

## Quick start

### 1. Install

```bash
uv sync
cp .env.example .env
# .env に OPENAI_API_KEY を設定
```

### 2. Start LightRAG server

```bash
task server:start
```

### 3. Index your documents

```bash
task index -- /path/to/your/project
```

### 4. Connect MCP server to Claude Code

`.claude/settings.json` に追加:

```json
{
  "mcpServers": {
    "aidd-kos": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_server.server"],
      "cwd": "/path/to/aidd-kos",
      "env": {
        "LIGHTRAG_URL": "http://localhost:9621"
      }
    }
  }
}
```

## MCP tools

| Tool | Description |
|------|-------------|
| `query_documents` | Search project docs with LightRAG |
| `get_status` | Check server and index status |
| `list_documents` | List indexed documents |

## Architecture

```
Claude Code → MCP server → LightRAG REST API → .lightrag/ (graph + vector DB)
```

## License

MIT
