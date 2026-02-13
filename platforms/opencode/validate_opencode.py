#!/usr/bin/env python3
"""Validate an opencode.json file against its JSON Schema.

Usage:
  python validate_opencode.py [path/to/opencode.json] [optional-schema-url]

The script will by default read the $schema property from the JSON file if
no schema URL is provided.
"""

import sys
import json
from pathlib import Path

try:
    import requests
    import jsonschema
except Exception as e:
    sys.stderr.write(
        "Missing dependency: please install with `pip install requests jsonschema`\n"
    )
    raise


def fetch_json(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "opencode.json"
    if not path.exists():
        sys.stderr.write(f"File not found: {path}\n")
        return 2

    data = json.loads(path.read_text(encoding="utf-8"))

    schema_url = None
    if len(argv) > 2:
        schema_url = argv[2]
    else:
        schema_url = data.get("$schema")

    if not schema_url:
        sys.stderr.write(
            "No schema URL provided and $schema not found in the JSON file.\n"
        )
        return 3

    try:
        schema = fetch_json(schema_url)
    except Exception as e:
        sys.stderr.write(f"Failed to fetch schema {schema_url}: {e}\n")
        return 4

    # Create resolver that can fetch remote refs using requests
    handlers = {
        "http": lambda uri: fetch_json(uri),
        "https": lambda uri: fetch_json(uri),
    }

    try:
        Validator = jsonschema.validators.validator_for(schema)
        Validator.check_schema(schema)
        resolver = jsonschema.RefResolver.from_schema(schema, handlers=handlers)
        validator = Validator(schema, resolver=resolver)
        validator.validate(data)
    except jsonschema.exceptions.ValidationError as ve:
        sys.stderr.write("Validation failed:\n")
        sys.stderr.write(str(ve) + "\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Error during validation: {e}\n")
        return 5

    print("opencode.json is valid according to the schema.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
