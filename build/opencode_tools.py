#!/usr/bin/env python3
"""
Transpiles Python tools with Fire to OpenCode TypeScript format.
Uses AST-based type extraction and generates Zod schemas.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class Parameter:
    name: str
    type_hint: Optional[str]
    default: Any
    description: str


@dataclass
class FunctionSignature:
    name: str
    parameters: List[Parameter]
    return_type: Optional[str]
    docstring: str
    description: str


@dataclass
class ExportDefinition:
    name: str
    export_type: str  # 'function' or 'class'
    object_name: str
    methods: List[str] = field(default_factory=list)


class PythonTypeExtractor:
    """Extracts types and signatures from Python code using AST."""

    def parse_script(self, script_path: Path) -> Dict[str, FunctionSignature]:
        """Parse Python script and extract all function/class signatures."""
        with open(script_path, "r") as f:
            tree = ast.parse(f.read())

        exports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                sig = self._extract_function(node)
                exports[node.name] = sig
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name not in (
                        "__init__",
                        "__repr__",
                    ):
                        sig = self._extract_method(node, item)
                        exports[f"{node.name}.{item.name}"] = sig

        return exports

    def _extract_function(self, node: ast.FunctionDef) -> FunctionSignature:
        """Extract function signature with types."""
        params = []

        # Get docstring
        docstring = ast.get_docstring(node) or ""
        description = docstring.split("\n")[0] if docstring else ""

        # Parse args
        args = node.args
        defaults_start = len(args.args) - len(args.defaults)

        for i, arg in enumerate(args.args):
            if arg.arg in ("self", "cls"):
                continue

            default = None
            if i >= defaults_start:
                default = self._ast_to_literal(args.defaults[i - defaults_start])

            type_hint = None
            if arg.annotation:
                type_hint = self._annotation_to_string(arg.annotation)

            param_desc = self._extract_param_doc(docstring, arg.arg)

            params.append(Parameter(arg.arg, type_hint, default, param_desc))

        # Parse return type
        return_type = None
        if node.returns:
            return_type = self._annotation_to_string(node.returns)

        return FunctionSignature(
            name=node.name,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            description=description,
        )

    def _extract_method(
        self, class_node: ast.ClassDef, method_node: ast.FunctionDef
    ) -> FunctionSignature:
        """Extract method signature from class."""
        sig = self._extract_function(method_node)
        sig.name = f"{class_node.name}.{method_node.name}"
        return sig

    def _annotation_to_string(self, annotation: ast.AST) -> str:
        """Convert AST annotation to string."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return repr(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            base = self._annotation_to_string(annotation.value)
            slice_val = self._annotation_to_string(annotation.slice)
            return f"{base}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            elements = [self._annotation_to_string(e) for e in annotation.elts]
            return ", ".join(elements)
        elif isinstance(annotation, ast.Attribute):
            return f"{self._annotation_to_string(annotation.value)}.{annotation.attr}"
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            # Handle Union types using | syntax (Python 3.10+)
            left = self._annotation_to_string(annotation.left)
            right = self._annotation_to_string(annotation.right)
            return f"Union[{left}, {right}]"
        else:
            return "Any"

    def _ast_to_literal(self, node: Optional[ast.AST]) -> Any:
        """Convert AST node to Python literal."""
        if node is None:
            return None
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.NameConstant):
            return node.value
        elif isinstance(node, ast.List):
            return [self._ast_to_literal(e) for e in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._ast_to_literal(k): self._ast_to_literal(v)
                for k, v in zip(node.keys, node.values)
            }
        return None

    def _extract_param_doc(self, docstring: str, param_name: str) -> str:
        """Extract parameter description from docstring Args section."""
        if not docstring:
            return ""

        # Look for Args section
        args_match = re.search(
            r"Args:\s*\n((?:\s+\w+[^\n]*\n?)*)", docstring, re.MULTILINE
        )
        if not args_match:
            return ""

        args_section = args_match.group(1)

        # Find specific parameter
        param_pattern = rf"{param_name}:\s*([^\n]+)"
        param_match = re.search(param_pattern, args_section, re.IGNORECASE)
        if param_match:
            return param_match.group(1).strip()

        return ""


class ZodSchemaConverter:
    """Converts Python type hints to Zod schemas."""

    def convert(self, type_hint: Optional[str], default: Any) -> str:
        """Convert Python type hint to Zod schema string."""
        if not type_hint:
            return "tool.schema.any()"

        # Handle Optional[T] and Union[..., None]
        optional_match = re.match(r"Optional\[(.+)\]", type_hint)
        if optional_match:
            inner = optional_match.group(1).strip()
            # Check if None is already in the union
            if "None" not in inner:
                zod_inner = self._convert_basic_type(inner)
                return f"{zod_inner}.optional()"

        # Handle Union types
        if "Union[" in type_hint:
            inner = type_hint[type_hint.find("[") + 1 : type_hint.rfind("]")]
            types = [t.strip() for t in inner.split(",") if t.strip() != "None"]
            if types:
                zod_types = [self._convert_basic_type(t) for t in types]
                return f"tool.schema.union([{', '.join(zod_types)}])"
            return "tool.schema.any()"

        # Handle List[T]
        list_match = re.match(r"List\[(.+)\]", type_hint, re.IGNORECASE)
        if list_match:
            inner = list_match.group(1).strip()
            zod_inner = self._convert_basic_type(inner)
            return f"tool.schema.array({zod_inner})"

        # Handle Dict[K, V]
        dict_match = re.match(r"Dict\[(.+),\s*(.+)\]", type_hint, re.IGNORECASE)
        if dict_match:
            value_type = dict_match.group(2).strip()
            return "tool.schema.object()"  # Zod object for dict

        # Basic types
        return self._convert_basic_type(type_hint, default)

    def _convert_basic_type(self, type_hint: str, default: Any = None) -> str:
        """Convert basic Python types to Zod."""
        type_hint = type_hint.strip()

        mapping = {
            "str": "tool.schema.string()",
            "int": "tool.schema.number().int()",
            "float": "tool.schema.number()",
            "bool": "tool.schema.boolean()",
            "Any": "tool.schema.any()",
            "dict": "tool.schema.object()",
            "list": "tool.schema.array(tool.schema.any())",
            "Dict": "tool.schema.object()",
            "List": "tool.schema.array(tool.schema.any())",
        }

        zod = mapping.get(type_hint, "tool.schema.any()")

        # Add default if provided
        if default is not None:
            if isinstance(default, str):
                zod += f'.default("{default}")'
            elif isinstance(default, bool):
                zod += f".default({str(default).lower()})"
            else:
                zod += f".default({default})"

        return zod


class OpenCodeToolTranspiler:
    """Transpiles Python tools to OpenCode TypeScript format."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.type_extractor = PythonTypeExtractor()
        self.zod_converter = ZodSchemaConverter()

    def transpile_tool(self, tool_dir: Path, tool_yaml: Dict) -> Dict[str, str]:
        """
        Transpile a tool directory to TypeScript files.
        Returns: {filename: content}
        """
        script_path = tool_dir / tool_yaml["implementation"]["entry"]
        tool_name = tool_yaml["name"]

        # Extract all signatures from Python script
        signatures = self.type_extractor.parse_script(script_path)

        # Get exports from tool.yaml
        exports = tool_yaml.get("exports", [])

        # If no exports defined, auto-discover top-level functions
        if not exports:
            exports = self._auto_discover_exports(signatures)

        # Generate TypeScript for each export
        ts_files = {}

        for export in exports:
            if export["type"] == "function":
                sig = signatures.get(export["object"])
                if sig:
                    ts_content = self._generate_function_tool(
                        tool_name, export["name"], sig, script_path, tool_dir
                    )
                    filename = f"{export['name']}.ts"
                    ts_files[filename] = ts_content

            elif export["type"] == "class":
                class_name = export["object"]
                for method in export.get("methods", []):
                    sig = signatures.get(f"{class_name}.{method}")
                    if sig:
                        ts_content = self._generate_method_tool(
                            tool_name,
                            export["name"],
                            method,
                            sig,
                            script_path,
                            tool_dir,
                        )
                        filename = f"{export['name']}_{method}.ts"
                        ts_files[filename] = ts_content

        return ts_files

    def _auto_discover_exports(
        self, signatures: Dict[str, FunctionSignature]
    ) -> List[Dict]:
        """Auto-discover exports from top-level functions."""
        exports = []
        for name, sig in signatures.items():
            if "." not in name:  # Top-level function, not method
                exports.append({"name": name, "type": "function", "object": name})
        return exports

    def _generate_function_tool(
        self,
        tool_name: str,
        export_name: str,
        sig: FunctionSignature,
        script_path: Path,
        tool_dir: Path,
    ) -> str:
        """Generate TypeScript tool for a function export."""

        # Build args dict
        args_lines = []
        for param in sig.parameters:
            zod_type = self.zod_converter.convert(param.type_hint, param.default)
            line = f"    {param.name}: {zod_type}"
            if param.description:
                line += f'.describe("{param.description}")'
            args_lines.append(line)

        args_str = ",\n".join(args_lines)

        # Calculate relative path from workspace root to output location
        # Output goes to platforms/opencode/tools/{tool_name}/
        script_name = script_path.name
        rel_script_path = f"platforms/opencode/tools/{tool_name}/{script_name}"

        return f'''import {{ tool }} from "@opencode-ai/plugin"
import path from "path"

export default tool({{
  description: "{sig.description}",
  args: {{
{args_str}
  }},
  async execute(args, context) {{
    const script = path.join(context.worktree, "{rel_script_path}")
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${{k}}=${{JSON.stringify(v)}}`])
    const result = await Bun.$`python3 ${{script}} {export_name} ${{argList}}`.text()
    return JSON.parse(result.trim())
  }}
}})'''

    def _generate_method_tool(
        self,
        tool_name: str,
        class_name: str,
        method_name: str,
        sig: FunctionSignature,
        script_path: Path,
        tool_dir: Path,
    ) -> str:
        """Generate TypeScript tool for a class method."""

        # Build args dict
        args_lines = []
        for param in sig.parameters:
            zod_type = self.zod_converter.convert(param.type_hint, param.default)
            line = f"    {param.name}: {zod_type}"
            if param.description:
                line += f'.describe("{param.description}")'
            args_lines.append(line)

        args_str = ",\n".join(args_lines)

        # Calculate relative path from workspace root to output location
        # Output goes to platforms/opencode/tools/{tool_name}/
        script_name = script_path.name
        rel_script_path = f"platforms/opencode/tools/{tool_name}/{script_name}"

        return f'''import {{ tool }} from "@opencode-ai/plugin"
import path from "path"

export default tool({{
  description: "{sig.description}",
  args: {{
{args_str}
  }},
  async execute(args, context) {{
    const script = path.join(context.worktree, "{rel_script_path}")
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${{k}}=${{JSON.stringify(v)}}`])
    const result = await Bun.$`python3 ${{script}} {class_name} {method_name} ${{argList}}`.text()
    return JSON.parse(result.trim())
  }}
}})'''


def generate_opencode_tools(core_path: Path, output_path: Path) -> bool:
    """Generate OpenCode custom tools from Python implementations."""
    workspace_root = core_path.parent  # agent-workspace root
    tools_path = core_path / "tools"

    if not tools_path.exists():
        print("  No tools directory found")
        return True

    output_tools_path = output_path / "tools"
    output_tools_path.mkdir(parents=True, exist_ok=True)

    transpiler = OpenCodeToolTranspiler(workspace_root)

    import yaml

    success = True
    for tool_dir in tools_path.iterdir():
        if not tool_dir.is_dir():
            continue

        tool_yaml_path = tool_dir / "tool.yaml"
        if not tool_yaml_path.exists():
            print(f"  ⚠️  Skipping {tool_dir.name}: No tool.yaml found")
            continue

        try:
            with open(tool_yaml_path, "r") as f:
                tool_yaml = yaml.safe_load(f)

            tool_name = tool_yaml.get("name", tool_dir.name)
            print(f"  🔧 Transpiling tool: {tool_name}")

            # Create subdirectory for this tool
            tool_output_path = output_tools_path / tool_name
            tool_output_path.mkdir(parents=True, exist_ok=True)

            ts_files = transpiler.transpile_tool(tool_dir, tool_yaml)

            for filename, content in ts_files.items():
                output_file = tool_output_path / filename
                with open(output_file, "w") as f:
                    f.write(content)
                print(f"    ✅ Generated {tool_name}/{filename}")

            # Copy Python script to output
            script_name = tool_yaml["implementation"]["entry"]
            script_src = tool_dir / script_name
            if script_src.exists():
                import shutil

                script_dst = tool_output_path / script_name
                shutil.copy2(script_src, script_dst)
                print(f"    ✅ Copied {tool_name}/{script_name}")

        except Exception as e:
            print(f"  ❌ Error transpiling {tool_dir.name}: {e}")
            import traceback

            traceback.print_exc()
            success = False

    return success


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python opencode_tools.py <core_path> <output_path>")
        sys.exit(1)

    core_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    success = generate_opencode_tools(core_path, output_path)
    sys.exit(0 if success else 1)
