# Architecture

## Overview

The Agent Workspace uses a transpilation architecture where tool-agnostic definitions in `core/` are transformed into platform-specific configurations in `platforms/`.

```
┌─────────────────────────────────────────────────────────┐
│                      CORE/                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐          │
│  │  Skills  │  │  Agents  │  │ MCP Servers  │          │
│  │ SKILL.md │  │  YAML    │  │   JSON       │          │
│  └──────────┘  └──────────┘  └──────────────┘          │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │    Transpilation    │
              │    Engine (Python)   │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│   OpenCode     │ │ Continue │ │    Claude    │
│  opencode.json │ │config.yaml│ │  CLAUDE.md   │
└────────────────┘ └──────────┘ └──────────────┘
```

## Core Concepts

### 1. Skills vs Agents vs MCP Servers

**Skills** (`core/skills/`)
- Following [agentskills.io](https://agentskills.io) specification
- Reusable capabilities with instructions
- Declared dependencies on MCP servers
- Loaded on-demand by agents

**Agents** (`core/agents/`)
- Orchestrators that combine skills, MCP servers, and rules
- Define model configuration and tool permissions
- Map to platform-specific agent configurations

**MCP Servers** (`core/mcp-servers/`)
- Infrastructure for external tool access
- Defined in OpenCode JSON format (canonical)
- Transpiled to platform-specific MCP configurations

**Custom Tools** (`core/tools/`)
- Script-based utilities with validation schemas
- Different from MCP tools (local execution)
- Can be called by agents alongside MCP tools

### 2. Dependency Resolution

```
Skill ──depends on──> MCP Servers
  │
  └── requires ──> Built-in Tools
  |
  └── uses ──> Custom Tools

Agent ──uses──> Skills
  |
  └── configures ──> MCP Servers
  |
  └── applies ──> Rules
```

The build pipeline validates:
1. All MCP servers referenced by skills exist in `core/mcp-servers/`
2. All custom tools referenced by skills exist in `core/tools/`
3. All rules referenced by agents exist in `core/rules/`

### 3. Transpilation Flow

```
Input: core/
  │
  ├── skills/          ──────┐
  │                           │
  ├── agents/          ──────┼──> Parse & Validate ──> Intermediate Model
  │                           │
  ├── mcp-servers/     ──────┤
  │                           │
  ├── tools/           ──────┤
  │                           │
  └── rules/           ──────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │    Intermediate Model         │
              │  (Unified representation)      │
              └───────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ OpenCode │   │ Continue │   │  Claude  │
        │Generator │   │Generator │   │Generator │
        └──────────┘   └──────────┘   └──────────┘
              │               │               │
              ▼               ▼               ▼
        platforms/     platforms/     platforms/
         opencode/      continue/       claude/
```

## Platform-Specific Mapping

### OpenCode (Priority)

**Input** → **Output**
- `core/agents/{name}.yaml` → `agent.{name}` in `opencode.json`
- `core/skills/{name}/` → Copied to `platforms/opencode/skills/{name}/`
- `core/mcp-servers/{name}.json` → `mcp.{name}` in `opencode.json`
- `core/rules/{name}.md` → Referenced in agent configs
- `core/tools/{name}/` → Tool definitions in `opencode.json`

**Key Mappings**:
```yaml
# Agent YAML
model:
  provider: anthropic
  model: claude-3-5-sonnet
```
↓
```json
{
  "agent": {
    "my-agent": {
      "model": "anthropic/claude-3-5-sonnet"
    }
  }
}
```

### Continue.dev

**Input** → **Output**
- `core/agents/{name}.yaml` → `prompts[]` + model config in `config.yaml`
- `core/skills/{name}/` → Copied to `platforms/continue/skills/{name}/`
- `core/mcp-servers/{name}.json` → `mcpServers[]` in `config.yaml`
- `core/rules/{name}.md` → `rules[]` in `config.yaml`

### Claude Code

**Input** → **Output**
- `core/agents/{name}.yaml` → Sections in `CLAUDE.md`
- `core/skills/{name}/` → Referenced in `CLAUDE.md`
- `core/mcp-servers/` → Mentioned as available MCPs
- `core/rules/` → Inline in system prompt

## Schema Validation

All core files are validated against JSON schemas:

- `core/schemas/skill.json` - SKILL.md frontmatter validation
- `core/schemas/agent.json` - Agent YAML validation  
- `core/schemas/mcp-server.json` - MCP server JSON validation
- `core/schemas/tool.json` - Custom tool validation

## Build Pipeline

1. **validate** - Schema validation for all core files
2. **check-deps** - Verify skill MCP/tool dependencies exist
3. **transpile-opencode** - Generate OpenCode configs (priority)
4. **transpile-continue** - Generate Continue configs
5. **transpile-claude** - Generate Claude configs
6. **test** - Validate generated outputs

Each step runs in GitHub Actions on push to main.

## Extending the System

### Adding a New Platform

1. Create generator in `build/src/transpilers/{platform}.py`
2. Add platform folder in `platforms/{platform}/`
3. Update `build.yml` workflow
4. Add platform to `scripts/install.sh`

### Adding Core Features

1. Update relevant schema in `core/schemas/`
2. Update transpilers to handle new feature
3. Update example files
4. Update documentation

## File Organization Principles

1. **Single Source of Truth** - Edit only in `core/`
2. **Generated Code** - `platforms/` is read-only (auto-generated)
3. **Validation** - All changes validated before transpilation
4. **Dependencies** - Explicit declaration in manifests
5. **Progressive Disclosure** - Skills use agentskills.io format for efficiency
