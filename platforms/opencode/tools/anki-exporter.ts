import { tool } from "@opencode-ai/plugin"
import path from "path"
import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/anki-exporter/script.py"
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

export const export_deck = tool({
  description: "Export flashcard data to an Anki-compatible import file.",
  args: {
    deck_name: tool.schema.string().describe("Name for the Anki deck."),
    cards: tool.schema.array(tool.schema.any()).describe("List of dicts with 'front', 'back', and optional 'tags' keys."),
    output_format: tool.schema.string().default("txt").describe("'txt' for Anki plain-text import, 'csv' for spreadsheet review."),
    output_path: tool.schema.string().optional().describe("File path to write (auto-named if omitted)."),
    tag_all: tool.schema.any().optional().describe("Tags to apply to every card.")
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    // No context-injected parameters
    const result = await Bun.$`python3 ${script} export_deck ${argList}`.text()
    return result.trim()
  }
})