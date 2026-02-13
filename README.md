# Agent Workspace

A centralized, tool-agnostic repository for AI agent configurations that transpiles to multiple platforms (OpenCode, Continue, Claude Code, etc.).

## Overview

This repository provides a single source of truth for:
- **Agents** - AI personas with workflows and capabilities
- **Skills** - Reusable capabilities following [agentskills.io](https://agentskills.io) specification
- **MCP Servers** - Model Context Protocol server configurations
- **Custom Tools** - Script-based tools with validation schemas
- **Rules** - Reusable coding standards and constraints

## Quick Start

### As a Submodule in Your Project

```bash
# Add as submodule
git submodule add git@github.com:yourname/agent-workspace.git .agent-workspace

# Run setup script
./.agent-workspace/scripts/install.sh
```

This creates symlinks:
- `.continue/` → `.agent-workspace/platforms/continue/`
- `.opencode/` → `.agent-workspace/platforms/opencode/`
- `CLAUDE.md` → `.agent-workspace/platforms/claude/CLAUDE.md`

### Direct Usage

Copy files from `platforms/{platform}/` to your project's tool-specific directories.

## Repository Structure

```
agent-workspace/
├── core/                  # SOURCE OF TRUTH (edit here)
│   ├── skills/           # SKILL.md files (agentskills.io)
│   ├── agents/           # Agent definitions
│   ├── mcp-servers/      # MCP server configs (OpenCode format)
│   ├── tools/            # Custom tools with schemas
│   └── rules/            # Reusable rule sets
│
├── platforms/            # GENERATED OUTPUT (read-only)
│   ├── opencode/         # OpenCode config
│   ├── continue/         # Continue.dev config
│   └── claude/           # Claude Code config
│
└── build/                # Transpilation engine
```

## Adding Content

### Adding a Skill

Create a new folder in `core/skills/{skill-name}/` with:
- `SKILL.md` - Main skill definition with YAML frontmatter
- `scripts/` - Optional executables (optional)
- `references/` - Optional documentation (optional)
- `assets/` - Optional templates/data (optional)

Example `SKILL.md`:
```yaml
---
name: my-skill
description: What this skill does
mcp_servers:
  - github
allowed_tools:
  - github_*
---

# Instructions for the agent...
```

### Adding an Agent

Create `core/agents/{agent-name}.yaml`:
```yaml
name: my-agent
description: What this agent does

model:
  provider: anthropic
  model: claude-3-5-sonnet

skills:
  - my-skill
  
mcp_servers:
  - github

rules:
  - security/no-secrets
```

### Adding an MCP Server

Create `core/mcp-servers/{server-name}.json` (OpenCode format):
```json
{
  "name": "my-server",
  "type": "remote",
  "url": "https://example.com/mcp",
  "enabled": true
}
```

## Transpilation

The GitHub Actions workflow automatically transpiles core definitions to platform-specific formats:

1. **Validation** - Schemas are validated
2. **Dependency Check** - Ensures all MCP servers referenced by skills exist
3. **Transpile** - Core → OpenCode → Continue → Claude
4. **Test** - Generated outputs are validated against platform schemas

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed transpilation documentation.

## License

MIT

