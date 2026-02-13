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
from typing import Dict, List, Any, Tuple

import requests
import jsonschema
from jsonschema import validators

# Import the opencode tools transpiler
from opencode_tools import generate_opencode_tools


def load_agent(agent_path: Path) -> Dict:
    """Load an agent definition."""
    with open(agent_path) as f:
        return yaml.safe_load(f)


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


def generate_opencode_config(core_path: Path) -> Dict:
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
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent = load_agent(agent_file)
            name = agent.pop("name", agent_file.stem)

            # Convert to OpenCode format
            opencode_agent = {
                "description": agent.get("description", ""),
                "model": f"{agent['model']['provider']}/{agent['model']['model']}",
            }

            # Add tools configuration
            if "tools" in agent:
                tools = {}
                for tool_name, permission in agent["tools"].items():
                    # preserve original semantics in core, we'll coerce later to schema
                    if permission == "allow" or permission is True:
                        tools[tool_name] = True
                    elif permission == "ask":
                        tools[tool_name] = "ask"
                    elif permission == "deny" or permission is False:
                        tools[tool_name] = False
                opencode_agent["tools"] = tools

            # Add system prompt reference
            if "system_prompt" in agent:
                opencode_agent["prompt"] = agent["system_prompt"]

            config["agent"][name] = opencode_agent

    # Note: rules are intentionally not included in opencode.json
    # The OpenCode config schema does not include a top-level "rules" field,
    # so we skip compiling rule files into opencode.json.

    return config


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


def _coerce_agent_tools(tools: Dict) -> Tuple[Dict, List[str]]:
    """Coerce agent tool permissions to schema-compatible booleans.

    Returns the coerced tools dict and a list of warning messages for changes made.
    """
    warnings: List[str] = []
    out: Dict = {}
    for k, v in (tools or {}).items():
        if v is True or v == "allow":
            out[k] = True
        elif v is False or v == "deny":
            out[k] = False
        elif v == "ask":
            # Schema doesn't support 'ask' tri-state; conservatively deny and warn
            out[k] = False
            warnings.append(f"Tool '{k}': 'ask' coerced to false (deny).")
        else:
            # Unknown type: try truthiness
            out[k] = bool(v)
            warnings.append(f"Tool '{k}': coerced value {v!r} -> {out[k]!r}.")
    return out, warnings


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

    # Normalize agents
    agents = config.get("agent", {})
    for name, agent in agents.items():
        if not isinstance(agent, dict):
            continue
        tools = agent.get("tools")
        if tools is not None:
            coerced, w = _coerce_agent_tools(tools)
            if w:
                warnings.extend([f"agent.{name}: {msg}" for msg in w])
            agent["tools"] = coerced

    return warnings


def fetch_json_schema(url: str) -> Dict:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def validate_against_schema(config: Dict) -> List[jsonschema.ValidationError]:
    """Validate config (dict) against its $schema and return list of errors.

    Uses the $schema property on the config to fetch the schema. If no
    $schema is present, returns a single error-like object via exception.
    """
    schema_url = config.get("$schema")
    if not schema_url:
        raise RuntimeError("No $schema property present in generated config")

    schema = fetch_json_schema(schema_url)

    Validator = validators.validator_for(schema)
    Validator.check_schema(schema)
    resolver = jsonschema.RefResolver.from_schema(schema)
    validator = Validator(schema, resolver=resolver)

    errors = sorted(validator.iter_errors(config), key=lambda e: e.path)
    return errors


def generate_continue_config(core_path: Path) -> Dict:
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
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent = load_agent(agent_file)

            config["prompts"].append(
                {
                    "name": agent.get("name", agent_file.stem),
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


def generate_claude_config(core_path: Path) -> str:
    """Generate Claude Code CLAUDE.md."""
    sections = ["# Agent Workspace for Claude Code\n"]

    # Add agent definitions
    agents_path = core_path / "agents"
    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            agent = load_agent(agent_file)

            sections.append(f"## {agent.get('name', agent_file.stem)}\n")
            sections.append(f"**Description:** {agent.get('description', '')}\n")

            if "system_prompt" in agent:
                sections.append(agent["system_prompt"])
                sections.append("\n")

            if "skills" in agent:
                sections.append("### Available Skills\n")
                for skill in agent["skills"]:
                    sections.append(f"- {skill}\n")
                sections.append("\n")

            if "mcp_servers" in agent:
                sections.append("### MCP Servers\n")
                for server in agent["mcp_servers"]:
                    sections.append(f"- {server}\n")
                sections.append("\n")

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


def copy_skills(core_path: Path, output_path: Path) -> None:
    """Copy skills to output directory."""
    import shutil

    skills_src = core_path / "skills"
    skills_dst = output_path / "skills"

    if skills_src.exists():
        if skills_dst.exists():
            shutil.rmtree(skills_dst)
        shutil.copytree(skills_src, skills_dst)
        print(f"  📁 Copied skills to {skills_dst}")


def transpile(target: str, core_path: Path, output_path: Path) -> bool:
    """Transpile core definitions to target platform."""
    print(f"\n🔨 Transpiling to {target}...\n")

    output_path.mkdir(parents=True, exist_ok=True)

    try:
        if target == "opencode":
            config = generate_opencode_config(core_path)

            # Normalize the generated config to avoid embedding non-schema
            # fields (metadata, notes, etc.). Collect warnings for user info.
            warnings = normalize_config_for_schema(config)

            # Validate and provide informative errors before writing output.
            try:
                errors = validate_against_schema(config)
            except Exception as e:
                print(f"  ⚠️  Schema fetch/validation failed: {e}")
                # still write the file so the user can inspect it
                with open(output_path / "opencode.json", "w") as f:
                    json.dump(config, f, indent=2)
                print(f"  ✅ Generated opencode.json (schema fetch failed)")
                if warnings:
                    for w in warnings:
                        print(f"    ⚠ {w}")
                # fail the transpilation step so CI/pipeline can catch it
                raise

            if errors:
                print(f"  ❌ Validation errors ({len(errors)}):")
                for e in errors:
                    # Build a readable location and message
                    location = ".".join([str(p) for p in e.path]) or "<root>"
                    print(f"    - {location}: {e.message}")

                # write the file for inspection
                with open(output_path / "opencode.json", "w") as f:
                    json.dump(config, f, indent=2)
                print(
                    f"  ✅ Wrote opencode.json (invalid according to schema). Fix errors above."
                )
                # fail the transpilation step
                return False

            # No errors: write and report warnings
            with open(output_path / "opencode.json", "w") as f:
                json.dump(config, f, indent=2)
            print(f"  ✅ Generated opencode.json (schema valid)")
            if warnings:
                for w in warnings:
                    print(f"    ⚠ {w}")

            # Generate custom tools
            print(f"  🔧 Generating custom tools...")
            if not generate_opencode_tools(core_path, output_path):
                print(f"  ⚠️  Some tools failed to transpile")

            # Copy skills
            copy_skills(core_path, output_path)

        elif target == "continue":
            config = generate_continue_config(core_path)
            with open(output_path / "config.yaml", "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"  ✅ Generated config.yaml")

            # Copy skills
            copy_skills(core_path, output_path)

        elif target == "claude":
            config = generate_claude_config(core_path)
            with open(output_path / "CLAUDE.md", "w") as f:
                f.write(config)
            print(f"  ✅ Generated CLAUDE.md")

            # Copy skills
            copy_skills(core_path, output_path)

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

    args = parser.parse_args()

    core_path = Path(args.input)
    output_path = Path(args.output)

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

        if not transpile(target, core_path, target_output):
            all_success = False

    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
