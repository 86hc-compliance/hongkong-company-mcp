#!/usr/bin/env node
/**
 * Hong Kong Company MCP Server (com.86hc/hongkong-company)
 * Official Node.js Stdio MCP Client Bridge for 86hc.com (HC Business / 恒诚商务)
 * Zero external dependencies — runs out-of-the-box via `npx -y hongkong-company-mcp` on Node.js 18+.
 */

const readline = require('readline');

const API_RPC_URL = process.env.HK_COMPANY_RPC_URL || 'https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc';
const API_KEY = (process.env.HK_COMPANY_API_KEY || process.env.HKQUERY_API_KEY || '').trim();

const rl = readline.createInterface({
  input: process.stdin,
  terminal: false
});

rl.on('line', async (line) => {
  const trimmed = line.trim();
  if (!trimmed) return;

  let msg;
  try {
    msg = JSON.parse(trimmed);
  } catch (err) {
    return;
  }

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'HongKongCompany-MCP-Node/1.2.1 (+https://www.86hc.com)'
  };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
    headers['X-86HC-API-Key'] = API_KEY;
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }

  try {
    const res = await fetch(API_RPC_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(msg)
    });

    if (res.status === 204 || String(msg.method || '').startsWith('notifications/')) {
      return;
    }

    const text = await res.text();
    if (text && text.trim()) {
      const parsed = JSON.parse(text);
      process.stdout.write(JSON.stringify(parsed) + '\n');
    }
  } catch (err) {
    if (msg && msg.id !== undefined && msg.id !== null) {
      const errResp = {
        jsonrpc: '2.0',
        id: msg.id,
        error: {
          code: -32603,
          message: `86hc.com MCP gateway connection error: ${err.message || String(err)}`
        }
      };
      process.stdout.write(JSON.stringify(errResp) + '\n');
    }
  }
});
