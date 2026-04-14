#!/usr/bin/env node
/*
 * Send a chat message into an active Opencode session (minimal JS port of
 * agent-workspace/scripts/send_opencode_message.py).
 *
 * Usage:
 *   node send_opencode_message.js --text "Hello" [--base-url http://127.0.0.1:4096] [--session-id <id>]
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

    // TCP connect probe
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

    // HTTP health probe
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

async function getSessions(client) {
  try {
    return await client.session.list();
  } catch (e) {
    throw e;
  }
}

async function getLastMessage(client, sessionId) {
  try {
    // preferred signature per SDK: session.messages({ path: { id } })
    const res = await client.session.messages({ path: { id: sessionId } });
    if (Array.isArray(res) && res.length) return res[res.length - 1];
    // some SDK variants may return { data: [...] }
    if (res && Array.isArray(res.data) && res.data.length) return res.data[res.data.length - 1];
  } catch (e) {
    // ignore and fallthrough to alternative
  }

  // fallback: message.list if present
  if (client.message && typeof client.message.list === "function") {
    try {
      const msgs = await client.message.list({ session_id: sessionId });
      if (Array.isArray(msgs) && msgs.length) return msgs[msgs.length - 1];
      if (msgs && Array.isArray(msgs.data) && msgs.data.length) return msgs.data[msgs.data.length - 1];
    } catch (e) {
      // ignore
    }
  }
  return null;
}

function extractModelProviderFromMessage(msg) {
  if (!msg) return [null, null];
  let data = null;
  // SDK message shapes vary; try common locations
  if (msg.info && typeof msg.info === "object") data = { ...msg.info, ...msg };
  else if (msg.metadata && typeof msg.metadata === "object") data = { ...msg.metadata, ...msg };
  else if (msg) data = msg;

  const info = data.info || data.metadata || data.meta || data.extras || data;
  if (info && typeof info === "object") {
    const model_id = info.model_id || info.modelId || info.modelID || info.model || null;
    const provider_id = info.provider_id || info.providerId || info.providerID || info.provider || null;
    return [model_id || null, provider_id || null];
  }
  return [null, null];
}

async function sendMessage({ text, baseUrl, sessionId, modelId, providerId, debug }) {
  const client = createOpencodeClient({ baseUrl });

  try {
    let target = sessionId;
    if (!target) {
      const sessions = await getSessions(client);
      const arr = Array.isArray(sessions) ? sessions : (sessions?.data || []);
      if (!arr || arr.length === 0) {
        console.error("No sessions available on the Opencode instance.");
        return 2;
      }
      const active = arr.find((s) => s.status === "active");
      const selected = active || arr[0];
      target = selected?.id || selected?.session_id || null;
      if (!target) {
        console.error("Could not determine session id from session object:", selected);
        return 3;
      }
    }

    const parts = [{ type: "text", text }];

    if (!modelId || !providerId) {
      const msg = await getLastMessage(client, target);
      const [inferredModel, inferredProvider] = extractModelProviderFromMessage(msg);
      if (inferredModel && inferredProvider) {
        modelId = modelId || inferredModel;
        providerId = providerId || inferredProvider;
        console.error(`Inferred model_id=${modelId} provider_id=${providerId} from last message`);
      } else {
        console.error(
          "Could not infer model_id/provider_id from recent messages. Provide --model-id/--provider-id or set OPENCODE_MODEL_ID/OPENCODE_PROVIDER_ID env vars."
        );
        return 6;
      }
    }

    const modelObj = { providerID: providerId, modelID: modelId };

    // Preferred high-level send
    try {
      if (client.session && typeof client.session.prompt === "function") {
        await client.session.prompt({ path: { id: target }, body: { parts, model: modelObj } });
      } else {
        throw new Error("session.prompt not available");
      }
    } catch (e) {
      console.error(`High-level send failed (${e?.name || "Error"}): ${e?.message || e}; trying low-level POST /session/${target}/prompt`);
      // Fallback to raw POST
      try {
        const url = baseUrl.replace(/\/+$/, "") + `/session/${encodeURIComponent(target)}/prompt`;
        const resp = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parts, model: modelObj }),
        });
        // attempt to print response status
        console.error("Low-level POST status:", resp.status);
        if (!resp.ok) {
          const textResp = await resp.text();
          console.error("Low-level POST body:", textResp);
          throw new Error(`POST failed ${resp.status}`);
        }
      } catch (e2) {
        console.error("Low-level POST failed:", e2 && e2.message ? e2.message : e2);
        throw e2;
      }
    }

    console.log(`Message sent to session ${target}`);
    return 0;
  } catch (e) {
    console.error("Error sending message:", e && e.message ? e.message : e);
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

  const code = await sendMessage({ text, baseUrl, sessionId, modelId, providerId, debug });
  process.exit(code);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
