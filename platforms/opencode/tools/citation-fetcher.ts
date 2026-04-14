import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/citation-fetcher/script.py"
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

export const fetch = tool({
  description: "Fetch a citation by DOI, arXiv ID, or PubMed ID.",
  args: {
    identifier: tool.schema.string().describe("DOI, arXiv ID (e.g. 2103.00020), or PubMed ID (e.g. PMID:34385711)."),
    format: tool.schema.string().default("bibtex").describe("Output format — only 'bibtex' is currently supported via API."),
    cite_key: tool.schema.string().optional().describe("Optional custom BibTeX cite key.")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} fetch ${argList}`.text()
    return result.trim()
  }
})