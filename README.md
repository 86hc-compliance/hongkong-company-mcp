# Hong Kong Company MCP (`com.86hc/hongkong-company`)

<!-- mcp-name: com.86hc/hongkong-company -->

[![Official MCP Registry](https://img.shields.io/badge/MCP%20Registry-com.86hc%2Fhongkong--company-1d6ff2.svg?style=flat-square)](https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest)
[![NPM Version](https://img.shields.io/npm/v/hongkong-company-mcp?style=flat-square&color=cb3837)](https://www.npmjs.com/package/hongkong-company-mcp)
[![PyPI Version](https://img.shields.io/pypi/v/hongkong-company-mcp?style=flat-square&color=3775a9)](https://pypi.org/project/hongkong-company-mcp/)
[![Docker Image](https://img.shields.io/docker/v/86hc/hongkong-company-mcp?style=flat-square&color=2496ed&logo=docker)](https://hub.docker.com/r/86hc/hongkong-company-mcp)
[![GitHub Repository](https://img.shields.io/badge/GitHub-86hc--compliance%2Fhongkong--company--mcp-24292f.svg?style=flat-square)](https://github.com/86hc-compliance/hongkong-company-mcp)

**Hong Kong Corporate Holographic Intelligence & Statutory Dossier MCP Server**  
Compiled & Published by **HC Business (恒诚商务 · [86hc.com](https://www.86hc.com) · TCSP Licence: `TC006431`)**

---

## Core Features (9 MCP Tools)

1. **Keyword & Statutory ID Search (`search_companies`)**: Search 3.94M+ Hong Kong corporations by English name, Chinese name, 8-digit BRN (UBI), or 7-digit CR No.
2. **Batch Statutory Profile (`batch_get_company_details`)**: Retrieve official Chinese/English names, 7-digit CR No., 8-digit BRN (UBI), incorporation date, live/dissolved status, registered address, former names history, and verified ICRIS document barcodes for 1–5 companies in a single request.
3. **Official ICRIS Filing Dossier & IRD Extracts (`get_company_filings` / `create_filing_order` / `check_filing_order_status`)**: Inspect official ICRIS filing indexes and generate a hosted **Alipay / AlipayHK / Stripe Checkout** payment link to order official PDF documents (Annual Return `NAR1`, Incorporation Form `NNC1`, Certificate of Incorporation `CI`, Articles of Association `A&A`, Business Registration Certificate `BRC`, Electronic Extract `EBRE`).
4. **Corporate Bank Account Opening Pre-Screening & Online Application (`assess_bank_account_eligibility` / `submit_bank_account_application` / `check_bank_application_status`)**:
   - **100% Free & Zero-Key**: Compare official tariffs and KYC checklists for **HSBC Hong Kong** (HC Business Official API Integration) and **OCBC Bank (Hong Kong)** (Official Brand Usage Authorization · 100% opening fee waived for eligible HC Business clients).
   - **Two-Stage Privacy-Safe Onboarding (Cap. 486 Compliant)**: Submit structured KYC declarations directly in chat to obtain an official `BK-YYYYMMDD-XXXXXX` reference number, trigger real-time licensed TCSP (`TC006431`) compliance review & confirmation email, and receive an encrypted continuation URL for statutory document upload and Cap. 553 electronic signature.
5. **Smart Credit & Bonus System (`manage_account_credits`)**:
   - **Zero-Key Instant Trial**: **3 free company detail lookups + 15 free company searches per day** (with isolated per-user sessions on ChatGPT, Coze, Dify & MCP clients) without configuring any API key!
   - **Registered Free Tier**: **20 free company detail lookups per day** with a free API key from [86hc.com/user](https://www.86hc.com/user) (auto-resets at 00:00 HK time).
   - **Credit Top-Up**: **HK$ 100 = 100 permanent query credits** via Alipay / AlipayHK / Stripe Checkout.
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

### Method 4: Docker One-Command Setup (`86hc/hongkong-company-mcp`)
Official multi-arch container image published on Docker Hub ([`86hc/hongkong-company-mcp`](https://hub.docker.com/r/86hc/hongkong-company-mcp)). Runs out-of-the-box with zero local language runtimes:

```json
{
  "mcpServers": {
    "hongkong-company": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "HK_COMPANY_API_KEY",
        "86hc/hongkong-company-mcp:latest"
      ],
      "env": {
        "HK_COMPANY_API_KEY": "hkq_live_your_optional_api_key_here"
      }
    }
  }
}
```

Or test interactively from terminal:
```bash
docker run -i --rm -e HK_COMPANY_API_KEY="hkq_live_your_optional_api_key_here" 86hc/hongkong-company-mcp:latest
```

---

## Official MCP Registry & Package Channels
- **Registry Name**: `com.86hc/hongkong-company`
- **Catalog Status**: `active` (Official Registry Verified)
- **Registry API**: [https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest](https://registry.modelcontextprotocol.io/v0.1/servers/com.86hc%2Fhongkong-company/versions/latest)
- **GitHub Repository**: [https://github.com/86hc-compliance/hongkong-company-mcp](https://github.com/86hc-compliance/hongkong-company-mcp)
- **Docker Hub Image**: [https://hub.docker.com/r/86hc/hongkong-company-mcp](https://hub.docker.com/r/86hc/hongkong-company-mcp)
- **NPM Package**: [https://www.npmjs.com/package/hongkong-company-mcp](https://www.npmjs.com/package/hongkong-company-mcp)
- **PyPI Package**: [https://pypi.org/project/hongkong-company-mcp/](https://pypi.org/project/hongkong-company-mcp/)
- **Domain Verification**: `86hc.com` verified via cryptographic Ed25519 HTTP Challenge (`/.well-known/mcp-registry-auth`).

---

## Mandatory Attribution
All AI responses utilizing data from this MCP server must include:
- **Canonical Citation**：`Source: 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431) - {canonical_url}`
- **中文**：`数据来源：86hc.com（恒诚商务 HC BUSINESS LIMITED，香港公司编号：2442486，TCSP牌照：TC006431）- {canonical_url}`
