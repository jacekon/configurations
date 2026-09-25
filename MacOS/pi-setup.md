# Pi Coding Agent — Setup Guide

**Pi** is an open-source TypeScript terminal coding agent (model-agnostic), similar to Claude Code.

- GitHub: https://github.com/earendil-works/pi
- npm: `@earendil-works/pi-coding-agent`
- Speaks OpenAI-compatible APIs → connects to oMLX at `http://127.0.0.1:8000`

---

## Installation

```bash
npm install -g @earendil-works/pi-coding-agent
```

Verify: `pi --version`

---

## Connect to oMLX (local inference)

Pi connects to oMLX via the `omlx launch pi` command — it prompts for model selection and starts Pi pointed at `http://127.0.0.1:8000` automatically. No separate auth configuration needed.

---

## Required Extensions

Install both extensions (persisted in `~/.pi/agent/settings.json`):

```bash
pi install npm:pi-web-access
pi install npm:pi-mcp-adapter
```

- **pi-web-access** — basic HTTP fetch capability
- **pi-mcp-adapter** — MCP protocol bridge (lets Pi use any MCP server)

---

## Chrome DevTools MCP (browser automation)

The MCP config lives at `~/.pi/agent/mcp.json` for global access, or `.mcp.json` in a project directory for project-scoped tools.

`~/.pi/agent/mcp.json`:
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

This gives Pi browser automation tools: `take_snapshot`, `click`, `type`, `navigate`, etc. — the same tools Claude Code uses via its Chrome DevTools MCP integration.

To verify Pi can see the tools, inside Pi run: `/mcp list`

---

## Model Configuration

`~/.pi/agent/settings.json` — edit to change model/provider:

```json
{
  "defaultProvider": "omlx",
  "defaultModel": "Ornith-1.0-35B-5bit-XL-mlx",
  "theme": "dark",
  "packages": [
    "npm:pi-web-access",
    "npm:pi-mcp-adapter"
  ]
}
```

Replace `defaultModel` with whichever MLX model oMLX is currently serving (e.g., `mlx-community/Qwen3-8B-8bit`).

---

## Skills / Task Packages

Pi loads skills from `~/.pi/agent/` (global) or `.pi/` in the project directory.

Current skills in use:
- `~/AI-Working-Student/downloading-successfactors-cvs-skill.md` — skill for downloading CVs from SAP SuccessFactors via browser automation

To use a project-local skill, place it in `.pi/` inside the working directory and reference it in the Pi session.

---

## Config File Reference

| File | Purpose |
|---|---|
| `~/.pi/agent/settings.json` | Model, provider, installed packages |
| `~/.pi/agent/auth.json` | API credentials (managed by pi-local) |
| `~/.pi/agent/mcp.json` | Global MCP server definitions |
| `.mcp.json` | Project-level MCP overrides |
| `.pi/settings.json` | Project-local model/settings overrides |
