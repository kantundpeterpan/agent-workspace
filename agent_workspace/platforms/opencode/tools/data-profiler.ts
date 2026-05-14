import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/data-profiler/script.py"
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

export const profile = tool({
  description: "Profile a dataset and return shape, column stats, and quality warnings.",
  args: {
    file_path: tool.schema.string().describe("Path to the CSV, TSV, Parquet, or Excel file."),
    sample_rows: tool.schema.number().int().default(5).describe("Number of example rows to include per column."),
    max_categories: tool.schema.number().int().default(20).describe("Max unique values to list for categorical columns.")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} profile ${argList}`.text()
    return result.trim()
  }
})