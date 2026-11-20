#!/usr/bin/env node
/**
 * Cursor-only stdio bridge for the existing 86hc.com MCP endpoint.
 *
 * Cursor 3.31 sends initialize protocolVersion 2025-11-25. On 2026-11-20 the
 * live endpoint answered that request with 2026-07-28, which Cursor's bundled
 * MCP SDK rejects. The same endpoint echoes 2025-06-18. This bridge rewrites
 * only that handshake version and forwards every JSON-RPC message, including
 * tools/list, to the existing service. It does not implement a search API.
 */

const readline = require("readline");

const RPC_URL = process.env.HK_COMPANY_RPC_URL || "https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc";
const ECHOED_BY_SERVER = new Set(["2024-11-05", "2025-03-26", "2025-06-18"]);
const FALLBACK_PROTOCOL = "2025-06-18";

function apiKeyFromEnv(env) {
  const raw = String((env || process.env).HK_COMPANY_API_KEY || "").trim();
  if (!raw || raw.startsWith("${")) return "";
  return raw;
}

function prepareMessage(msg) {
  if (!msg || msg.method !== "initialize" || !msg.params || typeof msg.params !== "object") return msg;
  if (!ECHOED_BY_SERVER.has(msg.params.protocolVersion)) {
    msg.params.protocolVersion = FALLBACK_PROTOCOL;
  }
  return msg;
}

async function forwardLine(line, apiKey) {
  const trimmed = line.trim();
  if (!trimmed) return;
  let msg;
  try {
    msg = JSON.parse(trimmed);
  } catch (err) {
    return;
  }
  prepareMessage(msg);
  const headers = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
    "User-Agent": "HongKongCompany-MCP-CursorPlugin/1.3.2 (+https://www.86hc.com)",
  };
  if (apiKey) headers["X-API-Key"] = apiKey;
  try {
    const res = await fetch(RPC_URL, { method: "POST", headers, body: JSON.stringify(msg) });
    if (res.status === 204 || String(msg.method || "").startsWith("notifications/")) return;
    const text = await res.text();
    if (!text || !text.trim()) return;
    process.stdout.write(JSON.stringify(JSON.parse(text)) + "\n");
  } catch (err) {
    if (msg && msg.id !== undefined && msg.id !== null) {
      process.stdout.write(JSON.stringify({
        jsonrpc: "2.0",
        id: msg.id,
        error: { code: -32603, message: `86hc.com MCP gateway connection error: ${err.message || String(err)}` },
      }) + "\n");
    }
  }
}

function start() {
  const apiKey = apiKeyFromEnv(process.env);
  const rl = readline.createInterface({ input: process.stdin, terminal: false });
  let chain = Promise.resolve();
  rl.on("line", (line) => {
    chain = chain.then(() => forwardLine(line, apiKey)).catch(() => {});
  });
}

if (require.main === module) start();
else module.exports = { prepareMessage, apiKeyFromEnv, FALLBACK_PROTOCOL, ECHOED_BY_SERVER };
