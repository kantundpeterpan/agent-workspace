import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/stats-formatter/script.py"
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

export const format_result = tool({
  description: "Format a statistical result into APA 7th edition notation.",
  args: {
    test_type: tool.schema.string().describe("Type of test (t_test, f_test, chi_square, correlation, z_test,"),
    statistic: tool.schema.number().optional().describe("Test statistic value."),
    df: tool.schema.string().optional().describe("Degrees of freedom string (e.g. "48" or "2, 45")."),
    p_value: tool.schema.number().optional().describe("p-value (formatted as < .001 if needed)."),
    effect_size: tool.schema.number().optional().describe("Effect size magnitude."),
    effect_size_type: tool.schema.string().optional().describe("Symbol key for the effect size."),
    ci_lower: tool.schema.number().optional().describe("Lower bound of 95% CI."),
    ci_upper: tool.schema.number().optional().describe("Upper bound of 95% CI."),
    n: tool.schema.number().int().optional().describe("Sample size."),
    alpha: tool.schema.number().default(0.05).describe("Significance threshold.")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} format_result ${argList}`.text()
    return result.trim()
  }
})