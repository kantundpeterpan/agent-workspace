import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Analyze a single file for complexity.",
  args: {
    file_path: tool.schema.string().describe("Path to the source file to analyze"),
    threshold: tool.schema.number().int().default(10).describe("Cyclomatic complexity threshold for warnings"),
    include_cognitive: tool.schema.boolean().default(true).describe("Whether to include cognitive complexity analysis")
  },
  async execute(args, context) {
    const script = path.join(context.worktree, "platforms/opencode/tools/complexity-analyzer/script.py")
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    const result = await Bun.$`python3 ${script} analyze_file ${argList}`.text()
    return JSON.parse(result.trim())
  }
})