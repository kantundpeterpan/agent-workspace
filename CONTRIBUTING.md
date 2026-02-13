# Contributing to Agent Workspace

Thank you for contributing! This guide covers how to add agents, skills, MCP servers, and tools.

## Development Setup

```bash
git clone git@github.com:yourname/agent-workspace.git
cd agent-workspace
pip install -r build/requirements.txt
```

## Adding a Skill

Skills follow the [agentskills.io](https://agentskills.io) specification.

### 1. Create Directory Structure

```bash
mkdir -p core/skills/{skill-name}/{scripts,references,assets}
```

### 2. Write SKILL.md

```yaml
---
name: {skill-name}
description: Clear description of what this skill does and when to use it
mcp_servers:
  - github    # Optional: list required MCP servers
  - git
custom_tools:
  - complexity-analyzer   # Optional: list required custom tools
allowed_tools:
  - github_*   # Optional: constrain which tools can be used
  - git_*
---

# Instructions

Write clear, step-by-step instructions for the agent.

## When to Use

Describe scenarios where this skill applies.

## Steps

1. First step
2. Second step
3. Third step

## Examples

Provide concrete examples of inputs and outputs.
```

### 3. Add Optional Resources

- `scripts/` - Executable scripts the agent can run
- `references/` - Documentation files the agent can read
- `assets/` - Templates, data files, etc.

### 4. Validate

```bash
python build/validate.py core/skills/{skill-name}/
```

### 5. Test Transpilation

```bash
python build/transpile.py --target opencode --input core/ --output test-output/
```

## Adding an Agent

### 1. Create Agent YAML

```bash
touch core/agents/{agent-name}.yaml
```

```yaml
name: {agent-name}
description: What this agent does and when to use it

model:
  provider: anthropic|openai|ollama|...
  model: claude-3-5-sonnet|gpt-4|...
  temperature: 0.7    # Optional

skills:
  - skill-name-1
  - skill-name-2

mcp_servers:
  - github
  - git

rules:
  - security/no-secrets
  - style/typescript

tools:
  github_*: allow
  git_*: allow
  bash: ask
  write: deny

system_prompt: |
  You are a specialized agent for...
```

### 2. Ensure Dependencies Exist

All skills, MCP servers, and rules referenced must exist in `core/`.

### 3. Validate and Test

```bash
python build/validate.py core/agents/{agent-name}.yaml
python build/transpile.py --target opencode --input core/ --output test-output/
```

## Adding an MCP Server

### 1. Create MCP Server JSON

OpenCode format is the canonical source:

```bash
touch core/mcp-servers/{server-name}.json
```

```json
{
  "name": "{server-name}",
  "type": "local|remote",
  "command": ["npx", "-y", "{package-name}"],
  "enabled": true,
  "environment": {
    "ENV_VAR": "{env:ENV_VAR}"
  }
}
```

For remote servers:
```json
{
  "name": "{server-name}",
  "type": "remote",
  "url": "https://example.com/mcp",
  "enabled": true,
  "headers": {
    "Authorization": "Bearer {env:API_KEY}"
  },
  "oauth": {
    "scope": "read write"
  }
}
```

### 2. Add Metadata

Include a `metadata` section for documentation:

```json
{
  "name": "github",
  "type": "remote",
  "url": "https://api.githubcopilot.com/mcp/",
  "metadata": {
    "description": "GitHub API integration",
    "required_env": ["GITHUB_TOKEN"],
    "optional_env": ["GITHUB_ORG"],
    "tools": ["github_issue_*", "github_pr_*", "github_repo_*"]
  }
}
```

### 3. Test

```bash
python build/validate.py core/mcp-servers/{server-name}.json
```

## Adding a Custom Tool

Custom tools are different from MCP tools - they're scripts that run locally.

### 1. Create Tool Directory

```bash
mkdir -p core/tools/{tool-name}
touch core/tools/{tool-name}/{tool.yaml,script.py,schema.json}
```

### 2. Define Tool Metadata

```yaml
# core/tools/{tool-name}/tool.yaml
name: {tool-name}
description: What this tool does

schema:
  input:
    type: object
    required: [param1]
    properties:
      param1:
        type: string
        description: Description of param1
      param2:
        type: number
        default: 10
        description: Description of param2
  
  output:
    type: object
    properties:
      result:
        type: string
      status:
        type: string
        enum: [success, error]

implementation:
  language: python
  entry: script.py
```

### 3. Write Implementation

```python
#!/usr/bin/env python3
# core/tools/{tool-name}/script.py

import json
import sys

def main():
    # Read input from stdin
    input_data = json.load(sys.stdin)
    
    # Process
    result = process(input_data)
    
    # Output JSON to stdout
    print(json.dumps(result))

def process(data):
    # Implementation
    return {
        "result": "...",
        "status": "success"
    }

if __name__ == "__main__":
    main()
```

### 4. Add JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["param1"],
  "properties": {
    "param1": {
      "type": "string",
      "description": "Description of param1"
    },
    "param2": {
      "type": "number",
      "default": 10,
      "description": "Description of param2"
    }
  }
}
```

## Adding Rules

Rules are simple markdown files:

```bash
touch core/rules/{category}/{rule-name}.md
```

```markdown
---
name: {rule-name}
description: What this rule enforces
---

# Rule: {Rule Name}

Specific instructions for the agent to follow...

## Examples

Good:
```typescript
// Good example
```

Bad:
```typescript
// Bad example
```
```

## Pull Request Guidelines

1. **Validate First** - Run `python build/validate.py` before committing
2. **Test Transpilation** - Ensure your changes transpile correctly
3. **Update Docs** - If adding new concepts, update ARCHITECTURE.md
4. **Follow Naming** - Use kebab-case for all file names
5. **Clear Descriptions** - Write clear descriptions for skills and agents

## Testing

```bash
# Validate all core files
python build/validate.py core/

# Check dependencies
python build/check-dependencies.py

# Test transpilation to all platforms
python build/transpile.py --target all --input core/ --output test-output/

# Run specific platform tests
python build/test-opencode.py test-output/opencode/
```

## Questions?

Open an issue or discussion on GitHub!
