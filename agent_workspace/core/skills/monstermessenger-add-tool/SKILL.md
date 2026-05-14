---
name: monstermessenger-add-tool
description: Guides agents on how to add new tools to the MonsterMessenger LangGraph agent graph
mcp_servers:
  - git
allowed_tools:
  - Read
  - Grep
  - Write
  - Bash
---

# monstermessenger-add-tool Skill

## Overview
This skill guides agents on how to add new tools to the MonsterMessenger LangGraph agent graph. Tools expand the agent's capabilities by enabling it to perform specific tasks and interact with external systems.

## Codebase Layout & Architecture

### Key Components
- **Tools**: `api/agents/service1/tools/` (Python functions decorated with `@tool`)
- **Registry**: `api/agents/service1/core/registry.py` (Maps tool names to Python objects)
- **LLM Compiler**: `api/agents/service1/utils/node_env.py` (Binds the LLM to localized manifests)
- **Graph & Routing**: `api/agents/service1/graph.py` and `api/agents/service1/routers/main_router.py`
- **Translations/i18n**: `api/i18n/` (Contains translation YAMLs for prompts, tools, and UI)

## Workflow for Adding a New Tool

### 1. Tool Implementation
Create a `@tool` decorated function inside `api/agents/service1/tools/`.

```python
from langchain_core.tools import tool

@tool
async def new_tool_name(
    runtime: ToolRuntime, user_type: Literal["teenager", "parent"] | None = None
) -> str:
    """
    Description of the tool.
    """
    # Tool logic here
    return Command(
        update={
            "tool_output": "result",
            "messages": [
                ToolMessage("Tool completed.", tool_call_id=runtime.tool_call_id)
            ],
        }
    )
```

### 2. Registration
Register the tool so `NodeEnv` can map it via `api/agents/service1/core/registry.py` (using `@register_tool("name")` if applicable).

```python
from agents.service1.core.registry import register_tool

@register_tool("new_tool_name")
@tool
async def new_tool_name(...):
    # Tool logic here
```

### 3. i18n Tool Description
Add localized tool descriptions and parameter schemas to `api/i18n/tools/<language>/` to support prompt-injected tool catalogs.

```yaml
# api/i18n/tools/FR/new_tool_name.yaml
name: new_tool_name
description: "Description of the tool in French"
parameters:
  user_type:
    description: "Type of user in French"
```

### 4. Graph Integration
Add the newly created tool to the `tools` array within the `ToolNode` instantiation in `graph.py`.

```python
def create_app(store=None):
    graph = StateGraph(Service1State)
    graph.add_node(
        "research_tools",
        ToolNode(
            tools=[
                research_educational_strategies,
                new_tool_name,  # Add new tool here
            ]
        ),
    )
    return graph
```

### 5. Manifest Binding
Add the tool name to the `tools.catalog` list in any node manifest (`api/agents/service1/nodes/manifests/*.yaml`) that should have access to the tool.

```yaml
name: node_name
system_prompt:
  parts:
    - base_prompt
tools:
  catalog:
    - research_educational_strategies
    - new_tool_name  # Add new tool here
```

## Verification
Ensure the drafted `SKILL.md` correctly covers `NodeEnv` and other architectural specifics.
