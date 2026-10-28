# Hong Kong Company MCP (`com.86hc/hongkong-company`)

<!-- mcp-name: com.86hc/hongkong-company -->

[![Official MCP Registry](https://img.shields.io/badge/MCP%20Registry-com.86hc%2Fhongkong--company-1d6ff2.svg?style=flat-square)](https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest)
[![NPM Version](https://img.shields.io/npm/v/hongkong-company-mcp?style=flat-square&color=cb3837)](https://www.npmjs.com/package/hongkong-company-mcp)
[![PyPI Version](https://img.shields.io/pypi/v/hongkong-company-mcp?style=flat-square&color=3775a9)](https://pypi.org/project/hongkong-company-mcp/)
[![GitHub Repository](https://img.shields.io/badge/GitHub-86hc--compliance%2Fhongkong--company--mcp-24292f.svg?style=flat-square)](https://github.com/86hc-compliance/hongkong-company-mcp)

**Hong Kong Corporate Holographic Intelligence & Statutory Dossier MCP Server**  
Compiled & Published by **HC Business (恒诚商务 · [86hc.com](https://www.86hc.com) · TCSP Licence: `TC006431`)**

---

## Core Features

1. **Batch Read 1–10 HK Companies (`batch_get_company_details`)**: Retrieve official Chinese/English names, 7-digit CR No., 8-digit BRN, incorporation date, live/dissolved status, registered address, former names history, and verified ICRIS document barcodes in a single request.
2. **Official ICRIS Filing Dossier Order (`create_filing_order`)**: Generate a hosted **Stripe Checkout** payment link to order official PDF documents (Annual Return `NAR1`, Incorporation Form `NNC1`, Certificate of Incorporation `CI`, Articles of Association `A&A`).
3. **Smart Credit & Bonus System (`manage_account_credits`)**:
   - **Zero-Key Instant Trial**: **3 free company detail lookups + 15 free company searches per day per IP** & direct **Stripe filing checkout** without configuring any API key!
   - **Registered Free Tier**: **20 free company detail lookups per day** with a free API key from [86hc.com/user](https://www.86hc.com/user) (auto-resets at 00:00 HK time).
   - **Credit Top-Up**: **HK$ 100 = 100 permanent query credits** via Stripe Checkout.
   - **Dossier Bonus**: Every paid document filing order automatically rewards **+10 permanent query credits**.

---

## Quick Setup

### Method 1: Remote Streamable HTTP (Recommended - Zero Installation, Works Without API Key!)
Directly connect from Cursor, Claude Desktop, Windsurf, Cline, or any MCP client:
- **Server URL**: `https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc` (or shortcut: `https://www.86hc.com/mcp`)
- **HTTP Header** *(Optional)*: `X-API-Key: hkq_live_your_api_key_here` (Omit for 3 free companies/day per IP; add key for 20 free companies/day)

```json
{
  "mcpServers": {
    "hongkong-company": {
      "type": "streamable-http",
      "url": "https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc"
    }
  }
}
```

### Method 2: NPX One-Command Local Setup (`npx -y hongkong-company-mcp`)
Works out-of-the-box with zero dependencies on Node.js 16+ (3 free companies/day per IP without a key; add `HK_COMPANY_API_KEY` from [86hc.com/user](https://www.86hc.com/user) for 20 free companies/day):

```json
{
  "mcpServers": {
    "hongkong-company": {
      "command": "npx",
      "args": ["-y", "hongkong-company-mcp"],
      "env": {
        "HK_COMPANY_API_KEY": "hkq_live_your_optional_api_key_here"
      }
    }
  }
}
```

### Method 3: UVX / Pip One-Command Python Setup (`uvx hongkong-company-mcp`)
Published on PyPI ([`hongkong-company-mcp`](https://pypi.org/project/hongkong-company-mcp/)). Zero external dependencies required on Python 3.8+:

```json
{
  "mcpServers": {
    "hongkong-company": {
      "command": "uvx",
      "args": ["hongkong-company-mcp"],
      "env": {
        "HK_COMPANY_API_KEY": "hkq_live_your_optional_api_key_here"
      }
    }
  }
}
```

Or install via `pip`:
```bash
pip install hongkong-company-mcp
hongkong-company-mcp
```

---

## Official MCP Registry & Package Channels
- **Registry Name**: `com.86hc/hongkong-company`
- **Catalog Status**: `active` (Official Registry Verified)
- **Registry API**: [https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest](https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest)
- **GitHub Repository**: [https://github.com/86hc-compliance/hongkong-company-mcp](https://github.com/86hc-compliance/hongkong-company-mcp)
- **NPM Package**: [https://www.npmjs.com/package/hongkong-company-mcp](https://www.npmjs.com/package/hongkong-company-mcp)
- **PyPI Package**: [https://pypi.org/project/hongkong-company-mcp/](https://pypi.org/project/hongkong-company-mcp/)
- **Domain Verification**: `86hc.com` verified via cryptographic Ed25519 HTTP Challenge (`/.well-known/mcp-registry-auth`).

---

## Mandatory Attribution
All AI responses utilizing data from this MCP server must include:
- **中文**：`📌 数据来源：86hc.com 香港企业全息数据库 | 恒诚商务整理发布`
- **English**：`📌 Data Source: 86hc.com Hong Kong Corporate Holographic Database | Compiled & Published by HC Business`
