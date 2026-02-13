#!/usr/bin/env python3
"""
Dependency checker for agent workspace.
Ensures all MCP servers and tools referenced by skills exist.
"""

import yaml
import sys
from pathlib import Path
from typing import Set, List, Dict


def get_all_mcp_servers(core_path: Path) -> Set[str]:
    """Get all available MCP server names."""
    servers = set()
    mcp_path = core_path / "mcp-servers"

    if mcp_path.exists():
        for server_file in mcp_path.glob("*.json"):
            servers.add(server_file.stem)

    return servers


def get_all_custom_tools(core_path: Path) -> Set[str]:
    """Get all available custom tool names."""
    tools = set()
    tools_path = core_path / "tools"

    if tools_path.exists():
        for tool_dir in tools_path.iterdir():
            if tool_dir.is_dir() and (tool_dir / "tool.yaml").exists():
                tools.add(tool_dir.name)

    return tools


def get_all_skills(core_path: Path) -> Dict[str, Dict]:
    """Get all skills with their dependencies."""
    skills = {}
    skills_path = core_path / "skills"

    if skills_path.exists():
        for skill_dir in skills_path.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    try:
                        with open(skill_md) as f:
                            content = f.read()

                        # Extract frontmatter
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) >= 3:
                                frontmatter = yaml.safe_load(parts[1])
                                skills[skill_dir.name] = {
                                    "mcp_servers": frontmatter.get("mcp_servers", []),
                                    "custom_tools": frontmatter.get("custom_tools", []),
                                }
                    except Exception as e:
                        print(f"Warning: Could not parse {skill_md}: {e}")

    return skills


def get_all_agents(core_path: Path) -> Dict[str, Dict]:
    """Get all agents with their dependencies."""
    agents = {}
    agents_path = core_path / "agents"

    if agents_path.exists():
        for agent_file in agents_path.glob("*.yaml"):
            try:
                with open(agent_file) as f:
                    data = yaml.safe_load(f)

                agents[agent_file.stem] = {
                    "skills": data.get("skills", []),
                    "mcp_servers": data.get("mcp_servers", []),
                    "rules": data.get("rules", []),
                }
            except Exception as e:
                print(f"Warning: Could not parse {agent_file}: {e}")

    return agents


def get_all_rules(core_path: Path) -> Set[str]:
    """Get all available rule paths (category/name)."""
    rules = set()
    rules_path = core_path / "rules"

    if rules_path.exists():
        for category_dir in rules_path.iterdir():
            if category_dir.is_dir():
                for rule_file in category_dir.glob("*.md"):
                    rules.add(f"{category_dir.name}/{rule_file.stem}")

    return rules


def check_dependencies(core_path: Path) -> bool:
    """Check all dependencies."""
    all_valid = True

    print("🔗 Checking dependencies...\n")

    # Load all available resources
    available_mcp = get_all_mcp_servers(core_path)
    available_tools = get_all_custom_tools(core_path)
    available_rules = get_all_rules(core_path)
    all_skills = get_all_skills(core_path)
    all_agents = get_all_agents(core_path)

    print(f"Available MCP servers: {', '.join(sorted(available_mcp)) or 'none'}")
    print(f"Available custom tools: {', '.join(sorted(available_tools)) or 'none'}")
    print(f"Available rules: {len(available_rules)}")
    print()

    # Check skill dependencies
    print("📋 Checking skill dependencies...")
    for skill_name, deps in all_skills.items():
        missing_mcp = [s for s in deps["mcp_servers"] if s not in available_mcp]
        missing_tools = [t for t in deps["custom_tools"] if t not in available_tools]

        if missing_mcp or missing_tools:
            all_valid = False
            print(f"  ❌ {skill_name}:")
            if missing_mcp:
                print(f"     Missing MCP servers: {', '.join(missing_mcp)}")
            if missing_tools:
                print(f"     Missing custom tools: {', '.join(missing_tools)}")
        else:
            print(f"  ✅ {skill_name}")

    # Check agent dependencies
    print("\n🤖 Checking agent dependencies...")
    for agent_name, deps in all_agents.items():
        missing_skills = [s for s in deps["skills"] if s not in all_skills]
        missing_mcp = [s for s in deps["mcp_servers"] if s not in available_mcp]
        missing_rules = [r for r in deps["rules"] if r not in available_rules]

        if missing_skills or missing_mcp or missing_rules:
            all_valid = False
            print(f"  ❌ {agent_name}:")
            if missing_skills:
                print(f"     Missing skills: {', '.join(missing_skills)}")
            if missing_mcp:
                print(f"     Missing MCP servers: {', '.join(missing_mcp)}")
            if missing_rules:
                print(f"     Missing rules: {', '.join(missing_rules)}")
        else:
            print(f"  ✅ {agent_name}")

    print()
    if all_valid:
        print("✨ All dependencies satisfied!")
        return True
    else:
        print("❌ Some dependencies are missing")
        return False


def main():
    core_path = Path(__file__).parent.parent / "core"
    success = check_dependencies(core_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
