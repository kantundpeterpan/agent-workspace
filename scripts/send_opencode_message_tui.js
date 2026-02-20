#!/usr/bin/env node
/*
 * Send a chat message into the Opencode TUI (or session) — JS script.
 *
 * Behavior:
 *  - If --session-id is provided, send directly to that session (uses session.prompt).
 *  - Otherwise, append the text to the TUI prompt and submit it (uses tui.appendPrompt + tui.submitPrompt).
 *
 * Usage:
 *   node send_opencode_message_tui.js --text "Hello" [--base-url http://127.0.0.1:4096] [--session-id <id>] [--debug]
 */

import { createOpencodeClient } from "@opencode-ai/sdk";
import { URL } from "url";
import dns from "node:dns";
import net from "node:net";
import process from "node:process";

async function diagnoseBaseUrl(baseUrl) {
  try {
    console.error(`Diagnostic: probing ${baseUrl}`);
    const parsed = new URL(baseUrl);
    const host = parsed.hostname || parsed.pathname;
    const port = parsed.port ? Number(parsed.port) : parsed.protocol === "https:" ? 443 : 80;
    console.error(`Resolved host=${host} port=${port} scheme=${parsed.protocol}`);
    try {
      const addrs = await dns.promises.lookup(host, { all: true });
      const uniq = [...new Set(addrs.map((a) => a.address))];
      console.error("Address(es):", uniq.join(", "));
    } catch (e) {
      console.error("dns.lookup failed:", e && e.message ? e.message : e);
    }
    await new Promise((resolve) => {
      const s = new net.Socket();
      let done = false;
      s.setTimeout(3000);
      s.on("connect", () => {
        done = true;
        console.error("TCP connect: ok");
        s.destroy();
        resolve();
      });
      s.on("error", (err) => {
        if (!done) {
          done = true;
          console.error("TCP connect failed:", err && err.message ? err.message : err);
          resolve();
        }
      });
      s.on("timeout", () => {
        if (!done) {
          done = true;
          console.error("TCP connect timed out");
          s.destroy();
          resolve();
        }
      });
      s.connect(port, host);
    });
    const healthUrl = baseUrl.replace(/\/+$/, "") + "/health";
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        console.error(`HTTP probe attempt ${attempt} -> ${healthUrl}`);
        const controller = new AbortController();
        const id = setTimeout(() => controller.abort(), 5000);
        const r = await fetch(healthUrl, { signal: controller.signal });
        clearTimeout(id);
        console.error("HTTP probe status:", r.status);
        break;
      } catch (e) {
        console.error(`Probe attempt ${attempt} failed:`, e && e.message ? e.message : e);
        await new Promise((r) => setTimeout(r, 500));
      }
    }
  } catch (e) {
    console.error("Diagnostic failure:", e && e.message ? e.message : e);
  }
}

function parseArgs(argv) {
  const out = {};
  const args = argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--debug") {
      out.debug = true;
      continue;
    }
    if (a.startsWith("--")) {
      const key = a.replace(/^--+/, "").replace(/-/g, "_");
      const val = args[i + 1];
      if (!val || val.startsWith("--")) {
        out[key] = true;
      } else {
        out[key] = val;
        i++;
      }
    }
  }
  return out;
}

async function getLastMessage(client, sessionId) {
  try {
    const res = await client.session.messages({ path: { id: sessionId } });
    if (Array.isArray(res) && res.length) return res[res.length - 1];
    if (res && Array.isArray(res.data) && res.data.length) return res.data[res.data.length - 1];
  } catch (e) {}
  if (client.message && typeof client.message.list === "function") {
    try {
      const msgs = await client.message.list({ session_id: sessionId });
      if (Array.isArray(msgs) && msgs.length) return msgs[msgs.length - 1];
      if (msgs && Array.isArray(msgs.data) && msgs.data.length) return msgs.data[msgs.data.length - 1];
    } catch (e) {}
  }
  return null;
}

function extractModelProviderFromMessage(msg) {
  if (!msg) return [null, null];
  let data = msg;
  if (msg.info && typeof msg.info === "object") data = { ...msg, ...msg.info };
  const info = data.info || data.metadata || data.meta || data.extras || data;
  if (info && typeof info === "object") {
    const model_id = info.model_id || info.modelId || info.modelID || info.model || null;
    const provider_id = info.provider_id || info.providerId || info.providerID || info.provider || null;
    return [model_id || null, provider_id || null];
  }
  return [null, null];
}

async function sendViaTui(client, text) {
  // Append to TUI prompt and submit; this sends to whatever session the TUI currently targets.
  if (!client.tui || typeof client.tui.appendPrompt !== "function") {
    throw new Error("TUI appendPrompt not available on this server/SDK");
  }
  await client.tui.appendPrompt({ body: { text } });
  if (typeof client.tui.submitPrompt === "function") {
    await client.tui.submitPrompt();
  }
  // Provide a toast to confirm
  if (typeof client.tui.showToast === "function") {
    try {
      await client.tui.showToast({ body: { message: "Message sent via TUI", variant: "success" } });
    } catch (e) {}
  }
}

async function sendMessageTui({ text, baseUrl, sessionId, modelId, providerId }) {
  const client = createOpencodeClient({ baseUrl });
  try {
    if (sessionId) {
      // If session id provided, prefer direct session.prompt for exact targeting.
      // Try to infer model/provider if not given.
      if (!modelId || !providerId) {
        const msg = await getLastMessage(client, sessionId);
        const [im, ip] = extractModelProviderFromMessage(msg);
        if (im && ip) {
          modelId = modelId || im;
          providerId = providerId || ip;
          console.error(`Inferred model_id=${modelId} provider_id=${providerId}`);
        }
      }
      const parts = [{ type: "text", text }];
      const body = { parts };
      if (modelId && providerId) body.model = { providerID: providerId, modelID: modelId };
      await client.session.prompt({ path: { id: sessionId }, body });
      console.log(`Message sent to session ${sessionId} via session.prompt`);
      return 0;
    }

    // No session id — use TUI
    try {
      await sendViaTui(client, text);
      console.log("Message sent via TUI (to the TUI's active session)");
      return 0;
    } catch (e) {
      console.error("TUI send failed:", e && e.message ? e.message : e);
      // Last resort: try creating a new session and send via session.prompt
      try {
        const created = await client.session.create({ body: { title: "temp-notify-session" } });
        const sid = created?.id || created?.session_id || created?.data?.id;
        if (sid) {
          await client.session.prompt({ path: { id: sid }, body: { parts: [{ type: "text", text }] } });
          console.log(`Message sent to new session ${sid}`);
          return 0;
        }
      } catch (e2) {
        console.error("Fallback session send failed:", e2 && e2.message ? e2.message : e2);
      }
      return 5;
    }
  } catch (e) {
    console.error("Error:", e && e.message ? e.message : e);
    if (e && e.stack) console.error(e.stack);
    return 5;
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const text = args.text;
  const baseUrl = args.base_url || process.env.OPENCODE_BASE_URL || "http://127.0.0.1:4096";
  const debug = !!args.debug;
  const modelId = args.model_id || process.env.OPENCODE_MODEL_ID;
  const providerId = args.provider_id || process.env.OPENCODE_PROVIDER_ID;
  const sessionId = args.session_id || null;

  if (!text) {
    console.error("--text is required");
    process.exit(1);
  }
  if (debug) await diagnoseBaseUrl(baseUrl);
  const code = await sendMessageTui({ text, baseUrl, sessionId, modelId, providerId });
  process.exit(code);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
