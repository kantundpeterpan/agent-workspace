#!/usr/bin/env python3
"""
Validation script for core agent workspace definitions.
Validates skills, agents, MCP servers, and tools against their schemas.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_schema(schema_path: str) -> Dict:
    """Load a JSON schema."""
    with open(schema_path) as f:
        return json.load(f)


def validate_yaml_file(file_path: Path, schema: Dict) -> List[str]:
    """Validate a YAML file against a schema."""
    errors = []

    try:
        with open(file_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error: {e}")
        return errors

    # Basic validation (full JSON schema validation would require jsonschema library)
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check type constraints
    properties = schema.get("properties", {})
    for field, value in data.items():
        if field in properties:
            prop_schema = properties[field]
            expected_type = prop_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' should be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' should be an integer")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' should be a number")
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Field '{field}' should be a boolean")
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(f"Field '{field}' should be an array")
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(f"Field '{field}' should be an object")

    return errors


def validate_skill(skill_path: Path) -> List[str]:
    """Validate a skill directory."""
    errors = []

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"Missing SKILL.md in {skill_path}")
        return errors

    # Parse SKILL.md frontmatter
    try:
        with open(skill_md) as f:
            content = f.read()

        # Extract frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
            else:
                errors.append("Invalid frontmatter format")
                return errors
        else:
            errors.append("Missing YAML frontmatter")
            return errors

        # Validate required fields
        if "name" not in frontmatter:
            errors.append("Missing required field: name")
        elif not isinstance(frontmatter["name"], str):
            errors.append("Field 'name' should be a string")

        if "description" not in frontmatter:
            errors.append("Missing required field: description")
        elif not isinstance(frontmatter["description"], str):
            errors.append("Field 'description' should be a string")

        # Validate arrays
        for field in ["mcp_servers", "custom_tools", "allowed_tools"]:
            if field in frontmatter and not isinstance(frontmatter[field], list):
                errors.append(f"Field '{field}' should be an array")

    except Exception as e:
        errors.append(f"Error parsing SKILL.md: {e}")

    return errors


def validate_agent(agent_path: Path) -> List[str]:
    """Validate an agent YAML file."""
    schema_path = Path(__file__).parent.parent / "core" / "schemas" / "agent.json"
    schema = load_schema(str(schema_path))
    return validate_yaml_file(agent_path, schema)


def validate_mcp_server(server_path: Path) -> List[str]:
    """Validate an MCP server JSON file."""
    errors = []

    try:
        with open(server_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")
        return errors

    # Basic validation
    if "name" not in data:
        errors.append("Missing required field: name")

    if "type" not in data:
        errors.append("Missing required field: type")
    elif data["type"] not in ["local", "remote"]:
        errors.append("Field 'type' must be 'local' or 'remote'")

    if data.get("type") == "local" and "command" not in data:
        errors.append("Local servers require 'command' field")

    if data.get("type") == "remote" and "url" not in data:
        errors.append("Remote servers require 'url' field")

    return errors


def validate_tool(tool_path: Path) -> List[str]:
    """Validate a tool directory."""
    errors = []

    tool_yaml = tool_path / "tool.yaml"
    if not tool_yaml.exists():
        errors.append(f"Missing tool.yaml in {tool_path}")
        return errors

    # Load schema
    schema_path = Path(__file__).parent.parent / "core" / "schemas" / "tool.json"
    schema = load_schema(str(schema_path))

    # Validate tool.yaml
    errors.extend(validate_yaml_file(tool_yaml, schema))

    # Check for implementation file
    try:
        with open(tool_yaml) as f:
            data = yaml.safe_load(f)

        impl = data.get("implementation", {})
        entry = impl.get("entry")
        if entry:
            entry_file = tool_path / entry
            if not entry_file.exists():
                errors.append(f"Missing implementation file: {entry}")
    except Exception as e:
        errors.append(f"Error checking implementation: {e}")

    return errors


def validate_all(core_path: Path) -> bool:
    """Validate all core definitions."""
    all_valid = True

    print("🔍 Validating core definitions...\n")

    # Validate skills
    print("📋 Validating skills...")
    skills_path = core_path / "skills"
    if skills_path.exists():
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                errors = validate_skill(skill_dir)
                if errors:
                    all_valid = False
                    print(f"  ❌ {skill_dir.name}:")
                    for error in errors:
                        print(f"     - {error}")
                else:
                    print(f"  ✅ {skill_dir.name}")

    # Validate agents
    print("\n🤖 Validating agents...")
    agents_path = core_path / "agents"
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            errors = validate_agent(agent_file)
            if errors:
                all_valid = False
                print(f"  ❌ {agent_file.stem}:")
                for error in errors:
                    print(f"     - {error}")
            else:
                print(f"  ✅ {agent_file.stem}")

    # Validate MCP servers
    print("\n🔌 Validating MCP servers...")
    mcp_path = core_path / "mcp-servers"
    if mcp_path.exists():
        for server_file in mcp_path.glob("*.json"):
            errors = validate_mcp_server(server_file)
            if errors:
                all_valid = False
                print(f"  ❌ {server_file.stem}:")
                for error in errors:
                    print(f"     - {error}")
            else:
                print(f"  ✅ {server_file.stem}")

    # Validate tools
    print("\n🛠️  Validating custom tools...")
    tools_path = core_path / "tools"
    if tools_path.exists():
        for tool_dir in tools_path.iterdir():
            if tool_dir.is_dir():
                errors = validate_tool(tool_dir)
                if errors:
                    all_valid = False
                    print(f"  ❌ {tool_dir.name}:")
                    for error in errors:
                        print(f"     - {error}")
                else:
                    print(f"  ✅ {tool_dir.name}")

    print()
    if all_valid:
        print("✨ All validations passed!")
        return True
    else:
        print("❌ Some validations failed")
        return False


def main():
    if len(sys.argv) < 2:
        core_path = Path(__file__).parent.parent / "core"
    else:
        core_path = Path(sys.argv[1])

    success = validate_all(core_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
