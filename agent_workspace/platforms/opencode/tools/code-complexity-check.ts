import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/code-complexity-check/script.py"
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

export const analyze = tool({
  description: "Calculate cyclomatic complexity and other metrics for code files.",
  args: {
    file_path: tool.schema.string().describe("Path to the code file to analyze"),
    threshold: tool.schema.number().int().default(10).describe("Complexity threshold (functions above this are flagged, default: 10)"),
    language: tool.schema.string().default("auto").describe("Programming language (python, javascript, typescript, auto for auto-detect)")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} analyze ${argList}`.text()
    return result.trim()
  }
})