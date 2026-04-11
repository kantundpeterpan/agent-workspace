#!/usr/bin/env python3
"""
Transpilation engine for agent workspace.
Transforms core definitions to platform-specific formats.
"""

import yaml
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set

import requests
import jsonschema
from jsonschema import validators

# Import the opencode tools transpiler
from opencode_tools import generate_opencode_tools


# OpenCode built-in tool name mapping
OPENCODE_TOOL_NAME_MAP = {
    "Read": "read",
    "Write": "edit",
    "Edit": "edit",
    "Grep": "grep",
    "Bash": "bash",
    "Glob": "glob",
    "List": "list",
}


def load_agent(agent_path: Path) -> Dict:
    """Load an agent definition."""
    with open(agent_path) as f:
        return yaml.safe_load(f)


def load_language_overlay(languages_dir: Path, language: str, agent_name: str) -> Optional[Dict]:
    """Load a language-specific overlay for an agent (returns None if not found)."""
    if not language or language == "python":
        return None
    overlay_path = languages_dir / language / f"{agent_name}.yaml"
    if not overlay_path.exists():
        return None
    with open(overlay_path) as f:
        return yaml.safe_load(f)


def apply_language_overlay(agent_data: Dict, overlay: Optional[Dict]) -> Dict:
    """Merge a language overlay into agent data (system_prompt + custom_tools)."""
    if not overlay:
        return agent_data
    merged = dict(agent_data)
    if "system_prompt" in overlay:
        merged["system_prompt"] = overlay["system_prompt"]
    if "custom_tools" in overlay:
        merged["custom_tools"] = overlay["custom_tools"]
    return merged


def load_mcp_server(server_path: Path) -> Dict:
    """Load an MCP server definition."""
    with open(server_path) as f:
        return json.load(f)


def load_skill(skill_path: Path) -> Dict:
    """Load a skill definition."""
    skill_md = skill_path / "SKILL.md"
    with open(skill_md) as f:
        content = f.read()

    # Extract frontmatter and body
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
            return {
                "name": frontmatter.get("name", skill_path.name),
                "description": frontmatter.get("description", ""),
                "mcp_servers": frontmatter.get("mcp_servers", []),
                "custom_tools": frontmatter.get("custom_tools", []),
                "allowed_tools": frontmatter.get("allowed_tools", []),
                "body": body,
            }

    return {"name": skill_path.name, "description": "", "body": content}


def load_rule(rule_path: Path) -> str:
    """Load a rule file."""
    with open(rule_path) as f:
        return f.read()


def load_command(command_path: Path) -> Dict:
    """Load a command definition."""
    with open(command_path) as f:
        return yaml.safe_load(f)


def generate_opencode_config(
    core_path: Path,
    output_path: Path,
    agent_filter: Optional[Set[str]] = None,
    command_filter: Optional[Set[str]] = None,
    skill_filter: Optional[Set[str]] = None,
    language: str = "python",
) -> Dict:
    """Generate OpenCode configuration."""
    config = {
        "$schema": "https://opencode.ai/config.json",
        "mcp": {},
        "agent": {},
        "tools": {},
    }

    # Load MCP servers
    mcp_path = core_path / "mcp-servers"
    if mcp_path.exists():
        for server_file in mcp_path.glob("*.json"):
            server = load_mcp_server(server_file)
            name = server.pop("name", server_file.stem)
            # keep the raw server definition for now; we'll normalize to schema
            config["mcp"][name] = server

    # Load agents
    agents_path = core_path / "agents"
    languages_dir = core_path / "languages"
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent_data = load_agent(agent_file)
            name = agent_data.get("name", agent_file.stem)

            # Apply scope filter
            if agent_filter is not None and name not in agent_filter:
                continue

            # Apply language overlay
            overlay = load_language_overlay(languages_dir, language, name)
            agent_data = apply_language_overlay(agent_data, overlay)

            # Generate Markdown file
            _generate_opencode_agent_markdown(agent_data, name, output_path)
            # Agents are now standalone Markdown files and NOT included in opencode.json

    # Load commands
    commands_path = core_path / "commands"
    if commands_path.exists():
        generate_opencode_commands(core_path, output_path, command_filter=command_filter)

    return config


def generate_opencode_commands(
    core_path: Path,
    output_path: Path,
    command_filter: Optional[Set[str]] = None,
) -> None:
    """Generate OpenCode modular command files."""
    commands_dir = output_path / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    commands_path = core_path / "commands"
    for command_file in commands_path.glob("*.yaml"):
        command_data = load_command(command_file)
        name = command_data.get("name", command_file.stem)

        # Apply command filter
        if command_filter is not None and name not in command_filter:
            continue
        frontmatter = {
            "description": command_data.get("description", ""),
        }

        # Generate content with YAML frontmatter
        fm_str = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
        content = f"---\n{fm_str}---\n\n{command_data.get('prompt', '')}"

        output_file = commands_dir / f"{name}.md"
        with open(output_file, "w") as f:
            f.write(content)
        print(f"    ✅ Generated command: {name}")


def _normalize_mcp_server(server: Dict) -> Dict:
    """Return a schema-compliant subset of an MCP server definition.

    Keeps only allowed keys depending on the server type. This prevents
    metadata or other implementation details from ending up in the
    generated opencode.json and failing schema validation.
    """
    if not isinstance(server, dict):
        return server

    stype = server.get("type")
    if stype == "local":
        allowed = {"type", "command", "environment", "enabled", "timeout"}
    elif stype == "remote":
        allowed = {"type", "url", "enabled", "headers", "oauth", "timeout"}
    else:
        # Unknown -- fall back to the minimal allowed shape (enabled)
        allowed = {"enabled"}

    return {k: v for k, v in server.items() if k in allowed}


def _normalize_permission_value(v: Any) -> Any:
    """Normalize a permission value to 'allow', 'ask', or 'deny'."""
    if isinstance(v, dict):
        return {ik: _normalize_permission_value(iv) for ik, iv in v.items()}
    if v is True or v == "allow":
        return "allow"
    if v is False or v == "deny":
        return "deny"
    if v == "ask":
        return "ask"
    return "allow" if bool(v) else "deny"


def _map_to_opencode_permissions(agent_data: Dict) -> Dict:
    """Consolidate tools, skills, and MCP servers into OpenCode permissions."""
    out = {}

    # 1. Map Tools
    tools = agent_data.get("tools", {})
    for k, v in (tools or {}).items():
        mapped_key = OPENCODE_TOOL_NAME_MAP.get(k, k)
        out[mapped_key] = _normalize_permission_value(v)

    # 2. Map Skills
    skills = agent_data.get("skills", [])
    if isinstance(skills, list):
        for skill in skills:
            out[skill] = "allow"
    elif isinstance(skills, dict):
        for skill, val in skills.items():
            out[skill] = _normalize_permission_value(val)

    # 3. Map MCP Servers
    mcp_servers = agent_data.get("mcp_servers", [])
    if isinstance(mcp_servers, list):
        for server in mcp_servers:
            out[f"{server}_*"] = "allow"
    elif isinstance(mcp_servers, dict):
        for server, val in mcp_servers.items():
            if isinstance(val, (str, bool)):
                out[f"{server}_*"] = _normalize_permission_value(val)
            elif isinstance(val, dict):
                # Specific tool overrides for the MCP server
                # The keys in 'val' are expected to be tool names or patterns
                for tool_pattern, tool_val in val.items():
                    key = tool_pattern
                    if key == "*":
                        key = f"{server}_*"
                    elif not key.startswith(f"{server}_") and "*" not in key:
                        # Prepend server name if it's a specific tool name without wildcard
                        key = f"{server}_{key}"
                    out[key] = _normalize_permission_value(tool_val)

    return out


def _generate_opencode_agent_markdown(
    agent_data: Dict, name: str, output_path: Path
) -> str:
    """Generate a Markdown file for an OpenCode agent with frontmatter."""
    agents_dir = output_path / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Consolidate permissions
    permissions = _map_to_opencode_permissions(agent_data)

    # Build frontmatter
    frontmatter = {
        "description": agent_data.get("description", ""),
        "model": f"{agent_data['model']['provider']}/{agent_data['model']['model']}",
        "permission": permissions,
    }

    # Generate content with YAML frontmatter
    fm_str = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
    content = f"---\n{fm_str}---\n\n{agent_data.get('system_prompt', '')}"

    agent_file = agents_dir / f"{name}.md"
    with open(agent_file, "w") as f:
        f.write(content)

    return f"agents/{name}.md"


def normalize_config_for_schema(config: Dict) -> List[str]:
    """Mutate config in-place to remove non-schema fields and coerce values.

    Returns a list of warning messages describing changed fields.
    """
    warnings: List[str] = []

    # Normalize MCP servers
    mcp = config.get("mcp", {})
    for name, server in list(mcp.items()):
        normalized = _normalize_mcp_server(server)
        if normalized != server:
            warnings.append(
                f"mcp.{name}: removed unsupported keys for schema compliance."
            )
        config["mcp"][name] = normalized

    # Normalize agents (agents are now relative paths to Markdown files)
    # The OpenCode schema allows both objects and strings for agents.
    # No extra normalization needed for the strings.

    return warnings


def fetch_json_schema(url: str) -> Dict:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def generate_continue_config(
    core_path: Path,
    agent_filter: Optional[Set[str]] = None,
    command_filter: Optional[Set[str]] = None,
    mcp_filter: Optional[Set[str]] = None,
    language: str = "python",
) -> Dict:
    """Generate Continue.dev configuration."""
    config = {
        "name": "Agent Workspace",
        "version": "1.0.0",
        "schema": "v1",
        "models": [],
        "mcpServers": [],
        "rules": [],
        "prompts": [],
    }

    # Load MCP servers
    mcp_path = core_path / "mcp-servers"
    if mcp_path.exists():
        for server_file in mcp_path.glob("*.json"):
            server = load_mcp_server(server_file)
            name = server.pop("name", server_file.stem)
            if mcp_filter is not None and name not in mcp_filter:
                continue
            server_type = server.pop("type", "local")

            if server_type == "local":
                continue_server = {
                    "name": name,
                    "command": server.get("command", ["echo", "no command"])[0],
                    "args": server.get("command", ["echo", "no command"])[1:],
                }
            else:  # remote
                continue_server = {
                    "name": name,
                    "command": "curl",
                    "args": ["-s", server.get("url", "")],
                }

            config["mcpServers"].append(continue_server)

    # Load agents as prompts
    agents_path = core_path / "agents"
    languages_dir = core_path / "languages"
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent = load_agent(agent_file)
            name = agent.get("name", agent_file.stem)

            if agent_filter is not None and name not in agent_filter:
                continue

            overlay = load_language_overlay(languages_dir, language, name)
            agent = apply_language_overlay(agent, overlay)

            config["prompts"].append(
                {
                    "name": name,
                    "description": agent.get("description", ""),
                    "prompt": agent.get("system_prompt", ""),
                }
            )

    # Load rules
    rules_path = core_path / "rules"
    if rules_path.exists():
        for category_dir in rules_path.iterdir():
            if category_dir.is_dir():
                for rule_file in category_dir.glob("*.md"):
                    rule_path = f"file://rules/{category_dir.name}/{rule_file.name}"
                    config["rules"].append({"uses": rule_path})

    return config


def generate_claude_config(
    core_path: Path,
    output_path: Path,
    agent_filter: Optional[Set[str]] = None,
    command_filter: Optional[Set[str]] = None,
    language: str = "python",
) -> str:
    """Generate Claude Code CLAUDE.md."""
    sections = ["# Agent Workspace for Claude Code\n"]

    # Add agent definitions
    agents_path = core_path / "agents"
    languages_dir = core_path / "languages"
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent = load_agent(agent_file)
            name = agent.get("name", agent_file.stem)

            if agent_filter is not None and name not in agent_filter:
                continue

            overlay = load_language_overlay(languages_dir, language, name)
            agent = apply_language_overlay(agent, overlay)

            sections.append(f"## {name}\n")
            sections.append(f"**Description:** {agent.get('description', '')}\n")

            if "system_prompt" in agent:
                sections.append(agent["system_prompt"])
                sections.append("\n")

            if "skills" in agent:
                sections.append("### Available Skills\n")
                skills = agent["skills"]
                skill_list = skills if isinstance(skills, list) else list(skills.keys())
                for skill in skill_list:
                    sections.append(f"- {skill}\n")
                sections.append("\n")

            if "mcp_servers" in agent:
                sections.append("### MCP Servers\n")
                mcp_servers = agent["mcp_servers"]
                server_list = (
                    mcp_servers
                    if isinstance(mcp_servers, list)
                    else list(mcp_servers.keys())
                )
                for server in server_list:
                    sections.append(f"- {server}\n")
                sections.append("\n")

    # Add slash commands summary
    commands_path = core_path / "commands"
    if commands_path.exists():
        sections.append("## Slash Commands\n")
        for command_file in sorted(commands_path.glob("*.yaml")):
            command = load_command(command_file)
            name = command.get("name", command_file.stem)
            if command_filter is not None and name not in command_filter:
                continue
            desc = command.get("description", "")
            sections.append(f"- `/{name}`: {desc}\n")
        sections.append("\n")

        # Also generate modular command files
        generate_claude_commands(core_path, output_path, command_filter=command_filter)

    # Add rules
    rules_path = core_path / "rules"
    if rules_path.exists():
        sections.append("## Rules\n")
        for category_dir in rules_path.iterdir():
            if category_dir.is_dir():
                for rule_file in category_dir.glob("*.md"):
                    rule_content = load_rule(rule_file)
                    # Extract content after frontmatter
                    if rule_content.startswith("---"):
                        parts = rule_content.split("---", 2)
                        if len(parts) >= 3:
                            sections.append(
                                f"### {category_dir.name}/{rule_file.stem}\n"
                            )
                            sections.append(parts[2])
                            sections.append("\n")

    return "\n".join(sections)


def generate_claude_commands(
    core_path: Path,
    output_path: Path,
    command_filter: Optional[Set[str]] = None,
) -> None:
    """Generate Claude Code modular command files."""
    commands_dir = output_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    commands_path = core_path / "commands"
    for command_file in commands_path.glob("*.yaml"):
        command_data = load_command(command_file)
        name = command_data.get("name", command_file.stem)

        if command_filter is not None and name not in command_filter:
            continue

        # Build frontmatter
        frontmatter = {
            "description": command_data.get("description", ""),
            "argument-hint": "$ARGUMENTS",
        }

        # Generate content with YAML frontmatter
        fm_str = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)
        content = f"---\n{fm_str}---\n\n{command_data.get('prompt', '')}"

        output_file = commands_dir / f"{name}.md"
        with open(output_file, "w") as f:
            f.write(content)
        print(f"    ✅ Generated Claude command: {name}")


def copy_skills(
    core_path: Path,
    output_path: Path,
    skill_filter: Optional[Set[str]] = None,
) -> None:
    """Copy skills to output directory."""
    import shutil

    skills_src = core_path / "skills"
    skills_dst = output_path / "skills"

    if skills_src.exists():
        if skills_dst.exists():
            shutil.rmtree(skills_dst)
        if skill_filter is None:
            shutil.copytree(skills_src, skills_dst)
        else:
            skills_dst.mkdir(parents=True, exist_ok=True)
            for skill_dir in skills_src.iterdir():
                if skill_dir.is_dir() and skill_dir.name in skill_filter:
                    shutil.copytree(skill_dir, skills_dst / skill_dir.name)
        print(f"  📁 Copied skills to {skills_dst}")


def validate_agent_frontmatter(
    frontmatter: Dict, schema_config: Dict
) -> List[jsonschema.ValidationError]:
    """Validate agent frontmatter against the AgentConfig schema.

    Since the frontmatter is part of the AgentConfig (minus the 'prompt' which is the body),
    we try to extract the AgentConfig from the main schema.
    """
    # The main schema's 'agent' property has 'additionalProperties' which
    # defines the structure of each agent (AgentConfig).
    # We find it by looking for the 'agent' property in the root properties.
    agent_schema = schema_config.get("properties", {}).get("agent", {})
    if not agent_schema:
        return []

    # In opencode schema, 'agent' itself is an object of agents.
    # The definition of a single agent is in additionalProperties.
    # But wait, looking at the schema we fetched, 'agent' has 'properties' like 'plan'
    # AND 'additionalProperties'.
    agent_definition = agent_schema.get("additionalProperties")
    if not agent_definition:
        return []

    # If it's a list (anyOf/oneOf), we'd need to handle that, but let's assume
    # it's the object definition for now.
    if isinstance(agent_definition, bool):
        return []

    Validator = validators.validator_for(schema_config)
    # We use a Resolver to handle internal $refs if any
    resolver = jsonschema.RefResolver.from_schema(schema_config)
    validator = Validator(agent_definition, resolver=resolver)

    errors = sorted(validator.iter_errors(frontmatter), key=lambda e: e.path)
    return errors


def transpile(
    target: str,
    core_path: Path,
    output_path: Path,
    agent_filter: Optional[Set[str]] = None,
    command_filter: Optional[Set[str]] = None,
    skill_filter: Optional[Set[str]] = None,
    mcp_filter: Optional[Set[str]] = None,
    language: str = "python",
) -> bool:
    """Transpile core definitions to target platform."""
    print(f"\n🔨 Transpiling to {target}...\n")

    output_path.mkdir(parents=True, exist_ok=True)

    try:
        if target == "opencode":
            config = generate_opencode_config(
                core_path, output_path,
                agent_filter=agent_filter,
                command_filter=command_filter,
                skill_filter=skill_filter,
                language=language,
            )

            # Normalize the generated config to avoid embedding non-schema
            # fields (metadata, notes, etc.). Collect warnings for user info.
            warnings = normalize_config_for_schema(config)

            # Validate opencode.json and agent markdown frontmatter
            schema_url = config.get("$schema")
            schema_config = {}
            if schema_url:
                try:
                    schema_config = fetch_json_schema(schema_url)
                except Exception as e:
                    print(f"  ⚠️  Schema fetch failed: {e}")

            # Validate main config
            errors = []
            if schema_config:
                Validator = validators.validator_for(schema_config)
                resolver = jsonschema.RefResolver.from_schema(schema_config)
                validator = Validator(schema_config, resolver=resolver)
                errors = sorted(validator.iter_errors(config), key=lambda e: e.path)

                if errors:
                    print(f"  ❌ Validation errors in opencode.json ({len(errors)}):")
                    for e in errors:
                        location = ".".join([str(p) for p in e.path]) or "<root>"
                        print(f"    - {location}: {e.message}")

            # Validate agent frontmatter
            if schema_config:
                agents_path = core_path / "agents"
                if agents_path.exists():
                    for agent_file in agents_path.glob("*.yaml"):
                        agent_data = load_agent(agent_file)
                        name = agent_data.get("name", agent_file.stem)

                        # Re-calculate permissions to match what was written to frontmatter
                        permissions = _map_to_opencode_permissions(agent_data)
                        frontmatter = {
                            "description": agent_data.get("description", ""),
                            "model": f"{agent_data['model']['provider']}/{agent_data['model']['model']}",
                            "permission": permissions,
                        }

                        agent_errors = validate_agent_frontmatter(
                            frontmatter, schema_config
                        )
                        if agent_errors:
                            print(
                                f"  ❌ Validation errors in agent {name} frontmatter ({len(agent_errors)}):"
                            )
                            for e in agent_errors:
                                location = (
                                    ".".join([str(p) for p in e.path]) or "<root>"
                                )
                                print(f"    - {location}: {e.message}")
                            errors.extend(agent_errors)

            # Write opencode.json regardless of errors for inspection
            with open(output_path / "opencode.json", "w") as f:
                json.dump(config, f, indent=2)

            if errors:
                return False

            print(f"  ✅ Generated opencode.json (schema valid)")
            if warnings:
                for w in warnings:
                    print(f"    ⚠ {w}")

            # Generate custom tools
            print(f"  🔧 Generating custom tools...")
            if not generate_opencode_tools(core_path, output_path):
                print(f"  ⚠️  Some tools failed to transpile")

            # Copy skills
            copy_skills(core_path, output_path, skill_filter=skill_filter)

        elif target == "continue":
            config = generate_continue_config(
                core_path,
                agent_filter=agent_filter,
                command_filter=command_filter,
                mcp_filter=mcp_filter,
                language=language,
            )
            with open(output_path / "config.yaml", "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"  ✅ Generated config.yaml")

            # Copy skills
            copy_skills(core_path, output_path, skill_filter=skill_filter)

        elif target == "claude":
            config = generate_claude_config(
                core_path, output_path,
                agent_filter=agent_filter,
                command_filter=command_filter,
                language=language,
            )
            with open(output_path / "CLAUDE.md", "w") as f:
                f.write(config)
            print(f"  ✅ Generated CLAUDE.md")

            # Copy skills
            copy_skills(core_path, output_path, skill_filter=skill_filter)

        else:
            print(f"  ❌ Unknown target: {target}")
            return False

        print(f"\n✅ Transpilation to {target} complete!")
        return True

    except Exception as e:
        print(f"  ❌ Error during transpilation: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Transpile agent workspace definitions"
    )
    parser.add_argument(
        "--target", required=True, choices=["opencode", "continue", "claude", "all"]
    )
    parser.add_argument("--input", default="core/", help="Input directory")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--language", default="python", choices=["python", "r", "both"],
        help="Language variant for stats/DS agent system prompts (default: python)"
    )
    parser.add_argument(
        "--agents", nargs="*", metavar="AGENT",
        help="Restrict to specific agent names (default: all)"
    )
    parser.add_argument(
        "--commands", nargs="*", metavar="COMMAND",
        help="Restrict to specific command names (default: all)"
    )
    parser.add_argument(
        "--skills", nargs="*", metavar="SKILL",
        help="Restrict to specific skill names (default: all)"
    )
    parser.add_argument(
        "--mcp-servers", nargs="*", metavar="MCP",
        help="Restrict to specific MCP server names (default: all)"
    )

    args = parser.parse_args()

    core_path = Path(args.input)
    output_path = Path(args.output)

    agent_filter = set(args.agents) if args.agents else None
    command_filter = set(args.commands) if args.commands else None
    skill_filter = set(args.skills) if args.skills else None
    mcp_filter = set(args.mcp_servers) if args.mcp_servers else None

    if args.target == "all":
        targets = ["opencode", "continue", "claude"]
    else:
        targets = [args.target]

    all_success = True
    for target in targets:
        # Avoid creating a redundant nested directory when the provided
        # output path already points to the target folder (e.g. --output platforms/opencode/).
        if output_path.name == target:
            target_output = output_path
        else:
            target_output = output_path / target

        if not transpile(
            target, core_path, target_output,
            agent_filter=agent_filter,
            command_filter=command_filter,
            skill_filter=skill_filter,
            mcp_filter=mcp_filter,
            language=args.language,
        ):
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
