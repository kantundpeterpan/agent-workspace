#!/usr/bin/env python3
"""Validate opencode.json against the schema from opencode.ai/config.json"""

import json
import subprocess
import sys
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError, Draft202012Validator


def fetch_schema(url):
    """Fetch schema from URL using curl"""
    print(f"Fetching schema from {url}...")
    result = subprocess.run(["curl", "-L", "-s", url], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to fetch schema: {result.stderr}")
    return json.loads(result.stdout)


def check_extra_keys(config, schema):
    """Check for keys in config that are not in schema"""
    config_keys = set(config.keys())
    schema_keys = set(schema.get("properties", {}).keys())
    extra_keys = config_keys - schema_keys
    return extra_keys


def validate_without_additional_props(config, schema):
    """Validate config against schema, ignoring additionalProperties"""
    # Create a copy of schema with additionalProperties enabled
    schema_copy = schema.copy()
    schema_copy["additionalProperties"] = True

    errors = []
    validator = Draft202012Validator(schema_copy)

    for error in validator.iter_errors(config):
        errors.append(error)

    return errors


def main():
    # Config file path
    config_path = Path("/home/vscode/agent-workspace/platforms/opencode/opencode.json")
    schema_url = "https://opencode.ai/config.json"

    # Load the config file
    print(f"Loading config from {config_path}...")
    with open(config_path, "r") as f:
        config = json.load(f)

    # Fetch the schema
    schema = fetch_schema(schema_url)

    # Check for extra keys
    extra_keys = check_extra_keys(config, schema)
    if extra_keys:
        print(f"\n⚠️  Warning: Found {len(extra_keys)} key(s) not in schema:")
        for key in sorted(extra_keys):
            print(f"    - '{key}'")

    # Validate with strict schema
    print("\n🔍 Strict validation (additionalProperties: false)...")
    try:
        validate(instance=config, schema=schema)
        print("✅ Strict validation passed!")
        return 0
    except ValidationError as e:
        print("❌ Strict validation failed!")
        print(f"\n   Error: {e.message}")
        if e.path:
            print(f"   Path: {' -> '.join(str(p) for p in e.path)}")

    # Validate with relaxed schema (allow additional properties)
    print("\n🔍 Relaxed validation (allowing extra properties)...")
    errors = validate_without_additional_props(config, schema)

    if not errors:
        print("✅ Relaxed validation passed! (Only issue is extra properties)")
        print("\n💡 To fix: Remove these extra keys from opencode.json:")
        for key in sorted(extra_keys):
            print(f"    - '{key}'")
        return 1
    else:
        print(f"❌ Found {len(errors)} validation error(s):")
        for i, error in enumerate(errors[:5], 1):  # Show first 5 errors
            path_str = " -> ".join(str(p) for p in error.path) if error.path else "root"
            print(f"\n   {i}. [{path_str}] {error.message}")
        if len(errors) > 5:
            print(f"\n   ... and {len(errors) - 5} more error(s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
