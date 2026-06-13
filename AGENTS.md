# AGENTS.md

## Project Overview

Agent Workspace is a central hub for AI agent configurations that transpiles to multiple platforms (OpenCode, Continue.dev, Claude Code). The `core/` directory is the **source of truth** — all edits go there. The `platforms/` directory is **generated output**.

## Common Commands

```bash
# Validate all core definitions against schemas
python build/validate.py core/

# Check that all skill/agent dependencies resolve
python build/check-dependencies.py

# Transpile core/ to all platforms
python build/transpile.py --target all --input core/ --output platforms/

# Transpile to a single platform
python build/transpile.py --target opencode --input core/ --output platforms/

# Run tests (pomodoro-timer only, at present)
pytest agent_workspace/core/tools/pomodoro-timer/tests/

# Run the full CI pipeline locally
python build/validate.py core/ && python build/check-dependencies.py && python build/transpile.py --target all --input core/ --output platforms/
```

## Adding a New Component

### Skill

1. Create `core/skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`, `mcp_servers`, `custom_tools`, `allowed_tools`), then Markdown instructions.
2. Run `python build/validate.py core/skills/<name>/`

### Agent

1. Create `core/agents/<name>.yaml` with `name`, `description`, `model`, `skills`, `mcp_servers`, `rules`, `tools`, `system_prompt`.
2. Ensure all referenced skills/MCP servers/rules already exist in `core/`.
3. Run `python build/validate.py core/agents/<name>.yaml`

### MCP Server

1. Create `core/mcp-servers/<name>.json` with `name`, `type` (local/remote), `command` or `url`, optional `metadata`.
2. Run `python build/validate.py core/mcp-servers/<name>.json`

### Custom Tool

1. Create `core/tools/<name>/` with `tool.yaml` (metadata + schema), `script.py` (implementation), `schema.json` (JSON Schema).
2. Run `python build/validate.py core/tools/<name>/`

### Slash Command

1. Create `core/commands/<name>.yaml` with `name`, `description`, `prompt`.
2. Run `python build/validate.py core/commands/<name>.yaml`

### Rule

1. Create `core/rules/<category>/<name>.md` with YAML frontmatter (`name`, `description`), then Markdown instructions.
2. Run `python build/validate.py core/rules/<category>/<name>.md`

## Architecture

```
core/                        # SOURCE OF TRUTH — edit here
  agents/       *.yaml       # Agent definitions (model + skills + rules + tools)
  skills/       */SKILL.md   # Reusable agent capabilities (agentskills.io spec)
  mcp-servers/  *.json       # MCP server configs (OpenCode canonical format)
  tools/        */           # Custom local tools (tool.yaml + script.py + schema.json)
  commands/     *.yaml       # Slash-command prompt templates
  rules/        */*.md       # Coding standards and constraints
  scopes/       *.yaml       # Pre-packaged bundles of components
  schemas/      *.json       # JSON Schema definitions for validation

build/                       # Transpilation engine
  transpile.py               # core/ → platforms/ conversion
  validate.py                # Schema validation of core files
  check-dependencies.py      # Resolves skill/agent/MCP/tool references
  opencode_tools.py          # Python→TypeScript tool transpilation (AST-based)

platforms/                   # GENERATED OUTPUT — do not edit
  opencode/                  # opencode.json + agents/ + commands/ + skills/
  continue/                  # config.yaml
  claude/                    # CLAUDE.md + .claude/commands/
```

## Conventions

- **kebab-case** for all filenames and directory names
- **YAML frontmatter** (`---` delimited) for SKILL.md and rule `.md` files
- **OpenCode JSON format** is the canonical source for MCP server configs
- Always run `python build/validate.py` before committing changes to `core/`
- When adding an agent, ensure all referenced skills, MCP servers, and rules exist
- Transpiled output in `platforms/` is committed — run transpilation after any `core/` change
