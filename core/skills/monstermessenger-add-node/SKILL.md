---
name: monstermessenger-add-node
description: Guides agents on how to add new nodes to the MonsterMessenger LangGraph agent graph
mcp_servers:
  - git
allowed_tools:
  - Read
  - Grep
  - Write
  - Bash
---

# monstermessenger-add-node Skill

## Overview
This skill guides agents on how to add new nodes to the MonsterMessenger LangGraph agent graph. Nodes are the core units of conversational flow and state transitions within the system.

## Codebase Layout & Architecture

### Key Components
- **State**: `api/agents/service1/core/state.py` (`Service1State` dictating allowed `action` routes)
- **Nodes**: `api/agents/service1/nodes/` (Python functions managing state updates)
- **Prompt Manifests**: `api/agents/service1/nodes/manifests/` (YAML configs routing prompts and tools)
- **LLM Compiler**: `api/agents/service1/utils/node_env.py` (Binds the LLM to localized manifests)
- **Graph & Routing**: `api/agents/service1/graph.py` and `api/agents/service1/routers/main_router.py`
- **Registry**: `api/agents/service1/core/registry.py` (Maps tool/schema names to Python objects)
- **Translations/i18n**: `api/i18n/` (Contains translation YAMLs for prompts, tools, and UI)

## Workflow for Adding a New Node

### 1. State Update
Add the new node action to the `action` `Literal` definition in `Service1State` (`state.py`).

```python
class Service1State(TypedDict):
    action: Literal[
        ...,
        "new_node_name",  # Add new node here
    ]
```

### 2. Implementation
Create the `<node_name>.py` function in `api/agents/service1/nodes/`. Use `NodeEnv.compile()` to handle prompts if an LLM call is required.

```python
from agents.service1.core.state import Service1State
from agents.service1.utils.node_env import NodeEnv

def new_node_name(state: Service1State, config: RunnableConfig):
    """Node logic here."""
    prompt, llm = NodeEnv.compile("new_node_name", state, response_schema="ResponseSchema")
    messages = [prompt, *state["messages"]]
    response = llm.invoke(messages, config)
    return {"action": response["action"], "messages": [AIMessage(response["action"])]}
```

### 3. Manifest Creation
Create a `<node_name>.yaml` file in `api/agents/service1/nodes/manifests/` dictating the layout of system prompts and allowed tools.

```yaml
name: new_node_name
system_prompt:
  parts:
    - base_prompt
    - context_injection
tools:
  catalog:
    - research_educational_strategies
```

### 4. i18n Localization
Provide translation strings across languages in `api/i18n/prompts/`.

```yaml
# api/i18n/prompts/FR/new_node_name.yaml
base_prompt: "Prompt text in French"
context_injection: "Context injection text in French"
```

### 5. Graph Wiring
Add `graph.add_node()` and wire the edges (e.g., `add_edge`, `add_conditional_edges`) in `graph.py`.

```python
def create_app(store=None):
    graph = StateGraph(Service1State)
    graph.add_node("new_node_name", new_node_name)
    graph.add_edge("previous_node", "new_node_name")
    graph.add_edge("new_node_name", "next_node")
    return graph
```

### 6. Routing Logic
Update logic in `api/agents/service1/routers/main_router.py` to ensure the conversational flow reaches and progresses past the new node.

```python
def router(state: Service1State):
    if state["action"] == "new_node_name":
        return "new_node_name"
    return state["action"]
```
