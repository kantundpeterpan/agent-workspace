import { tool } from "@opencode-ai/plugin"
 import path from "path"
 import fs from "fs"

function resolveScriptPath(worktree) {
  const rel = "core/tools/pomodoro-timer/script.py"
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
  description: "Stop the current timer and cleanup the poller.",
  args: {
    // No user-provided arguments - all parameters injected from context
  },
  async execute(args, context) {
    const script = resolveScriptPath(context.worktree)
    const argList = Object.entries(args).flatMap(([k, v]) => [`--${k}=${JSON.stringify(v)}`])
    if (context.sessionID !== undefined) {
      argList.push(`--session_id=${JSON.stringify(context.sessionID)}`)
    }
    const result = await Bun.$`python3 ${script} stop ${argList}`.text()
    return result.trim()
  }
  })