import { tool } from "@opencode-ai/plugin"
 import path from "path"
 import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/dependency-checker/script.py"
  const direct = path.join(worktree, rel)
  if (fs.existsSync(direct)) return direct
  // If this repo is a submodule, the agent-workspace may be in a subdirectory.
  // Look one level deep for a matching rel path (fast heuristic).
  try {
    for (const entry of fs.readdirSync(worktree)) {
      const candidate = path.join(worktree, entry, rel)
      if (fs.existsSync(candidate)) return candidate
    }
  } catch (e) {}
  return direct
}

export default tool({
  description: "Analyze project dependencies.",
  args: {
    project_path: tool.schema.string().describe("Path to the project root directory"),
    check_security: tool.schema.boolean().default(true).describe("Whether to check for security vulnerabilities"),
    check_outdated: tool.schema.boolean().default(true).describe("Whether to check for outdated packages"),
    severity_threshold: tool.schema.string().default("moderate").describe("Minimum severity level to report (low, moderate, high, critical)")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} analyze_dependencies ${argList}`.text()
    return result.trim()
  }
  })