# Security Policy & Authentication Architecture

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2.0 | :x:                |

## Authentication & Access Control Model (`com.86hc/hongkong-company`)

The **Hong Kong Company MCP Server** (`https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc`) implements a tiered security and rate-limiting architecture designed for both zero-configuration evaluation and authenticated institutional production workloads:

### 1. Public Read-Only Trial Quota (Unauthenticated / Guest IP Mode)
To allow developers and MCP clients to test corporate registry lookups out-of-the-box without pre-provisioning secrets, `tools/list` and read-only statutory lookup tools are accessible under a strict per-IP sliding-window rate limit enforced by Redis:
- **`search_companies`** (`readOnlyHint: true`, `destructiveHint: false`): Capped at **15 searches/day per IP** (8-digit Business Registration Numbers are masked in unauthenticated search lists to prevent bulk harvesting).
- **`batch_get_company_details`** (`readOnlyHint: true`, `destructiveHint: false`): Capped at **3 company detail lookups/day per IP**.
- **`get_company_filings`** & **`assess_bank_account_eligibility`** (`readOnlyHint: true`, `destructiveHint: false`): Read-only inspection of official Companies Registry (ICRIS) filing indexes and bank tariff schedules.

### 2. Authenticated API Key Mode (`X-API-Key: hkq_live_...`)
Authenticated users pass a personal key via the `X-API-Key` HTTP header (or `HK_COMPANY_API_KEY` environment variable in STDIO mode):
- **Free Registered Tier**: **20 company detail lookups/day** and **50 searches/day** (obtained at [https://www.86hc.com/user](https://www.86hc.com/user)).
- **Transactional & Account-Bound Tools**:
  - **`submit_bank_account_application`** and **`check_bank_application_status`** strictly require a valid personal `hkq_live_...` API key and server-side ownership verification.
  - **`create_filing_order`** and **`manage_account_credits`** never execute silent charges; they return an encrypted Stripe Hosted Checkout / 86hc.com Cashier URL requiring explicit human buyer confirmation and payment authentication (3DS / Alipay / Apple Pay).

### 3. Data Integrity & Transport Security
- All communication with `https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc` is encrypted over **TLS 1.3 / HTTPS**.
- All SQL queries execute exclusively via parameterized prepared statements with single-statement atomic compare-and-swap (CAS) credit accounting.
- Only authentic Companies Registry (ICRIS) filing records with verified barcodes are returned.

## Reporting a Vulnerability

If you discover a security issue, please report it privately to the **HC BUSINESS LIMITED** (Licensed TCSP `TC006431`) security and compliance desk via [https://www.86hc.com/en/data-correction](https://www.86hc.com/en/data-correction). We respond to all verified security reports within 24 hours.
