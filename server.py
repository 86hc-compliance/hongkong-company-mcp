#!/usr/bin/env python3
"""
Hong Kong Company MCP Server (com.86hc/hongkong-company)
========================================================
Official Model Context Protocol (MCP) server for 86hc.com (HC Business / 恒诚商务).

Supports both:
- Official `mcp` SDK (FastMCP) when installed
- Zero-dependency Python Standard Library MCP JSON-RPC 2.0 stdio transport (runs out-of-the-box on any Python 3.8+)

Capabilities:
1. Search 3.9M+ Hong Kong registered / dissolved corporate entities (`search_companies` - 15 free/day without API key, 50/day with free key).
2. Batch retrieve 1 to 10 Hong Kong company holographic profiles in a single call (`batch_get_company_details` - 3 free/day per IP without API key, 20/day with free key).
3. Inspect official Companies Registry (ICRIS) statutory filing dockets & barcodes (`get_company_filings` - works without API key).
4. Initiate Stripe hosted checkout orders for official PDF documents (`create_filing_order` - works without API key, auto-selects latest verified barcode).
5. Poll order payment & PDF download link (`check_filing_order_status`).
6. Manage query credits: 3 free daily guest queries or 20 free daily queries with key; HK$ 100 = 100 credits; +10 bonus credits per filing order (`manage_account_credits`).

Mandatory Attribution:
- ZH: 📌 数据来源：86hc.com 香港企业全息数据库 | 恒诚商务整理发布
- EN: 📌 Data Source: 86hc.com Hong Kong Corporate Holographic Database | Compiled & Published by HC Business
"""

try:
    import asyncio
except Exception:
    asyncio = None
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

DEFAULT_API_BASE = "https://www.86hc.com/wp-json/hkquery/v1/mcp"
API_BASE = os.getenv("HK_COMPANY_API_BASE", DEFAULT_API_BASE).rstrip("/")
API_KEY = os.getenv("HK_COMPANY_API_KEY", os.getenv("HKQUERY_API_KEY", "")).strip()

ATTRIBUTION_FOOTER_ZH = "Source: 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431) - https://www.86hc.com"
ATTRIBUTION_FOOTER_EN = "Source: 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431) - https://www.86hc.com/en"

SYSTEM_INSTRUCTIONS = (
    "You are connected to the Hong Kong Company MCP (com.86hc/hongkong-company) powered by 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431).\n"
    "RULES YOU MUST FOLLOW:\n"
    "1. Zero-Config Trial Mode (No API Key Required): You can immediately invoke `search_companies` (15 free/day per user/IP), `batch_get_company_details` (3 free companies/day per user/IP), `get_company_filings`, and `create_filing_order` WITHOUT an API key. Users can obtain a free API key at https://www.86hc.com/user for 20 free company detail lookups/day.\n"
    "2. When querying multiple Hong Kong companies (up to 10), ALWAYS use `batch_get_company_details` in a single batch call rather than calling one by one.\n"
    "3. Each company detail lookup consumes 1 credit (3 free daily credits without key; 20 free daily credits with key, reset at 00:00 HK time; HK$ 100 = 100 permanent credits; ordering any official filing document rewards +10 bonus credits).\n"
    "4. When a user wants to order/download an official filing document (e.g. Annual Return NAR1, Incorporation Form NNC1, Certificate of Incorporation CI, Articles A&A, Business Registration Certificate BRC, or Electronic Extract EBRE), call `create_filing_order` and present both the 3-in-1 `web_cashier_url` (Mainland Alipay / AlipayHK / Stripe) and `checkout_url` clearly.\n"
    "5. MANDATORY ATTRIBUTION: At the end of EVERY response containing Hong Kong company data, you MUST include the exact attribution line:\n"
    "   Source: 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431) - {canonical_url}"
)


def _build_headers() -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "HongKongCompany-MCP/1.2.0 (+https://www.86hc.com)",
    }
    if API_KEY:
        headers["X-API-Key"] = API_KEY
        headers["X-86HC-API-Key"] = API_KEY
        headers["Authorization"] = f"Bearer {API_KEY}"
    return headers


def _sync_request_86hc(method: str, endpoint: str, payload: Optional[dict[str, Any]] = None) -> str:
    url = f"{API_BASE}/{endpoint.lstrip('/')}"
    data_bytes = None
    if method.upper() == "GET" and payload:
        url = f"{url}?{urllib.parse.urlencode(payload)}"
    elif payload is not None:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=_build_headers(), method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw_body = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw_body)
                return json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                return raw_body
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="replace")
        try:
            parsed_err = json.loads(err_body)
            return json.dumps(parsed_err, ensure_ascii=False, indent=2)
        except Exception:
            return json.dumps(
                {"success": False, "status_code": http_err.code, "error": err_body[:1000]},
                ensure_ascii=False,
                indent=2,
            )
    except Exception as exc:
        return json.dumps(
            {"success": False, "error": "network_error", "message": f"请求 86hc.com 网关异常: {str(exc)}"},
            ensure_ascii=False,
            indent=2,
        )


async def _request_86hc(method: str, endpoint: str, payload: Optional[dict[str, Any]] = None) -> str:
    if asyncio is not None:
        return await asyncio.to_thread(_sync_request_86hc, method, endpoint, payload)
    return _sync_request_86hc(method, endpoint, payload)


async def search_companies(query: str, limit: int = 5, api_key: str = "") -> str:
    """
    Search Hong Kong companies by Chinese name, English name, 7-digit CR number, or 8-digit BRN (UBI) to locate candidate entities.
    Does not consume detail credits (free tier: 15 searches/day without key, 50/day with free key), but masks 8-digit BRN in list view.
    """
    payload: dict[str, Any] = {"query": query, "limit": min(20, max(1, int(limit)))}
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "search", payload)


async def batch_get_company_details(
    companies: Optional[List[str]] = None,
    identifiers: Optional[List[str]] = None,
    api_key: str = "",
) -> str:
    """
    Batch retrieve comprehensive holographic profiles for 1 to 10 Hong Kong companies in a single request.
    Consumes 1 credit per matched company (3 free/day without key; 20 free/day with key; HK$ 100 = 100 permanent credits).
    """
    target_list = companies if companies else identifiers
    if not target_list:
        return json.dumps({"success": False, "message": "companies 或 identifiers 不能为空"}, ensure_ascii=False)
    if len(target_list) > 10:
        target_list = target_list[:10]
    payload: dict[str, Any] = {"companies": target_list, "identifiers": target_list}
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "batch-company-detail", payload)


async def get_company_filings(identifier: str, form_code: str = "", api_key: str = "") -> str:
    """
    Retrieve the official Companies Registry (ICRIS) statutory filing dossier catalog for a Hong Kong company.
    """
    payload: dict[str, Any] = {"identifier": identifier, "form_code": form_code}
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "company-filings", payload)


async def create_filing_order(
    identifier: str = "",
    doc_code: str = "NAR1",
    barcode: str = "",
    pay_method: str = "stripe",
    email: str = "",
    client_email: str = "",
    api_key: str = "",
) -> str:
    """
    Initiate a paid statutory document filing order (NAR1, NNC1, CI, A&A, ND2A, BRC, EBRE) for a Hong Kong company and generate a 3-in-1 Web Cashier (Mainland Alipay / AlipayHK / Stripe) & Stripe Checkout link.
    Rewards +10 bonus company query credits upon payment completion.
    """
    final_email = email or client_email
    final_method = pay_method if pay_method in ("alipay", "alipay_hk", "stripe") else "stripe"
    payload: dict[str, Any] = {
        "identifier": identifier,
        "doc_code": doc_code,
        "barcode": barcode,
        "email": final_email,
        "client_email": final_email,
        "pay_method": final_method,
    }
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "create-filing-order", payload)


async def check_filing_order_status(order_sn: str, api_key: str = "") -> str:
    """
    Check the payment and fulfillment status of a filing order or credit top-up order.
    """
    payload: dict[str, Any] = {"order_sn": order_sn}
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "order-status", payload)


async def manage_account_credits(
    action: str = "check_balance",
    pay_method: str = "stripe",
    api_key: str = "",
) -> str:
    """
    Check current API credit balance ("check_balance") OR generate a payment link (Alipay / AlipayHK / Stripe) to buy 100 credits for HK$ 100 ("buy_100_credits").
    """
    final_method = pay_method if pay_method in ("alipay", "alipay_hk", "stripe") else "stripe"
    payload: dict[str, Any] = {"action": action, "pay_method": final_method}
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "credits", payload)


async def assess_bank_account_eligibility(
    identifier: str = "",
    bank_target: str = "both",
    industry: str = "EXPORT_TRADE",
    has_mainland_entity: bool = True,
    annual_turnover_usd: str = "1M_TO_3M",
    api_key: str = "",
) -> str:
    """
    Assess HK corporate bank account opening eligibility, official bank tariff schedules (Tariff Guide), and tailored statutory KYC document checklists for HSBC Hong Kong and OCBC Bank Hong Kong. Unlogged-in users are subject to the 3 free queries/day per IP limit; logged-in users with an API Key from https://www.86hc.com/user enjoy 20 free queries/day.
    """
    payload = {
        "identifier": identifier,
        "bank_target": bank_target,
        "industry": industry,
        "has_mainland_entity": has_mainland_entity,
        "annual_turnover_usd": annual_turnover_usd,
    }
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "bank-eligibility", payload)


async def submit_bank_account_application(
    identifier: str,
    contact_name: str,
    contact_phone: str,
    bank_target: str = "hsbc",
    contact_email: str = "",
    contact_wechat: str = "",
    industry: str = "EXPORT_TRADE",
    products_services: str = "",
    turnover: str = "1M_TO_3M",
    has_mainland_company: bool = True,
    mainland_company_name: str = "",
    signing_location: str = "",
    user_note: str = "",
    api_key: str = "",
) -> str:
    """
    Submit an online Hong Kong corporate bank account opening pre-screening application (Stage 1 KYC dossier) for HSBC Hong Kong ('hsbc') or OCBC Bank Hong Kong ('ocbc'). Requires user login (personal API Key hkq_live_... obtained at https://www.86hc.com/user). Returns an official BK-YYYYMMDD-XXXXXX reference ID and a Stage 2 continuation URL.
    """
    payload = {
        "identifier": identifier,
        "bank_target": bank_target,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
        "contact_wechat": contact_wechat,
        "industry": industry,
        "products_services": products_services,
        "turnover": turnover,
        "has_mainland_company": has_mainland_company,
        "mainland_company_name": mainland_company_name,
        "signing_location": signing_location,
        "user_note": user_note,
    }
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "bank-apply", payload)


async def check_bank_application_status(
    order_id: str,
    contact_phone: str = "",
    contact_email: str = "",
    api_key: str = "",
) -> str:
    """
    Check the live compliance pre-screening status, uploaded document count, officer remarks, and Stage 2 upload link for a submitted bank account application (BK-YYYYMMDD-XXXXXX). Requires user login (personal API Key hkq_live_... from https://www.86hc.com/user).
    """
    payload = {
        "order_id": order_id,
        "contact_phone": contact_phone,
        "contact_email": contact_email,
    }
    if api_key:
        payload["api_key"] = api_key
    return await _request_86hc("POST", "bank-status", payload)


# ==============================================================================
# Transport Layer: FastMCP (if installed) OR Built-in Stdlib JSON-RPC 2.0 Server
# ==============================================================================
try:
    if asyncio is None:
        raise ImportError("asyncio unavailable")
    from mcp.server.fastmcp import FastMCP  # type: ignore

    mcp = FastMCP("Hong Kong Company", instructions=SYSTEM_INSTRUCTIONS)
    mcp.tool()(search_companies)
    mcp.tool()(batch_get_company_details)
    mcp.tool()(get_company_filings)
    mcp.tool()(create_filing_order)
    mcp.tool()(check_filing_order_status)
    mcp.tool()(manage_account_credits)
    mcp.tool()(assess_bank_account_eligibility)
    mcp.tool()(submit_bank_account_application)
    mcp.tool()(check_bank_application_status)
    HAS_FASTMCP = True
except ImportError:
    HAS_FASTMCP = False


TOOLS_SCHEMA = [
    {
        "name": "search_companies",
        "description": "Search Hong Kong companies by Chinese name, English name, 7-digit CR number, or 8-digit BRN (UBI) to locate candidate entities (Works without API key: 15 free/day per user/IP, 50/day with free key; masks 8-digit BRN in list view).",
        "annotations": {
            "title": "Search Hong Kong Companies Registry",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company keyword (Chinese name, English name, 7-digit CR number, or 8-digit BRN / UBI)."},
                "limit": {"type": "integer", "description": "Number of results (1-20, default 5).", "default": 5},
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "batch_get_company_details",
        "description": "Batch retrieve comprehensive holographic profiles for 1 to 10 Hong Kong companies (CR No, 8-digit BRN / Foreign TIN, incorporation date, status, address, former names, and verified ICRIS filing barcodes). Works without API key (3 free companies/day per user/IP; 20 free/day with free API key). MUST cite: Source: 86hc.com (HC BUSINESS LIMITED, CR No.: 2442486, Licensed TCSP: TC006431) - {canonical_url}",
        "annotations": {
            "title": "Batch Get HK Company Statutory Profiles",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "companies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Array of 1 to 10 company identifiers (7-digit CR numbers, 8-digit BRNs, or exact Chinese/English company names).",
                },
                "identifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Alias for companies: list of 1 to 10 company identifiers.",
                },
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
            "required": ["companies"],
        },
    },
    {
        "name": "get_company_filings",
        "description": "Retrieve the official Companies Registry (ICRIS) statutory filing dossier catalog and verified barcodes for a Hong Kong company (works without an API key).",
        "annotations": {
            "title": "Get ICRIS Statutory Filing Dossier Index",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Company CR number, 8-digit BRN, or company name."},
                "form_code": {"type": "string", "description": "Optional form code filter (e.g. NAR1, CI, NNC1, A&A, ND2A).", "default": ""},
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "create_filing_order",
        "description": "Initiate a paid statutory document filing order (NAR1, NNC1, CI, A&A, ND2A, BRC, EBRE) and generate both a 3-in-1 Web Cashier URL (Mainland Alipay / AlipayHK / Stripe) and a Stripe Hosted Checkout payment link (works without an API key; auto-selects latest verified barcode or 8-digit BRN if barcode is omitted). Rewards +10 bonus query credits upon payment.",
        "annotations": {
            "title": "Create Statutory Filing Retrieval Order",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Company CR number, 8-digit BRN, or exact name."},
                "doc_code": {"type": "string", "description": "Statutory form code: NAR1, NNC1, CI, A&A, ND2A, BRC (Business Registration Certificate), or EBRE (Electronic Extract of Business Register). Default NAR1.", "default": "NAR1"},
                "barcode": {"type": "string", "description": "Optional specific ICRIS document barcode.", "default": ""},
                "pay_method": {"type": "string", "enum": ["alipay", "alipay_hk", "stripe"], "default": "stripe", "description": "Preferred payment method: alipay, alipay_hk, or stripe."},
                "email": {"type": "string", "description": "Optional email address to receive the PDF.", "default": ""},
                "client_email": {"type": "string", "description": "Alias for email.", "default": ""},
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
        },
    },
    {
        "name": "check_filing_order_status",
        "description": "Check payment status and retrieve the official PDF download link for a filing order.",
        "annotations": {
            "title": "Check Filing Order & PDF Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_sn": {"type": "string", "description": "Order serial number (e.g. HKQ20261016xxxx)."},
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
            "required": ["order_sn"],
        },
    },
    {
        "name": "manage_account_credits",
        "description": "Check API credit balance ('check_balance') or generate a payment link (Mainland Alipay / AlipayHK / Stripe) to buy 100 permanent query credits for HK$ 100 ('buy_100_credits').",
        "annotations": {
            "title": "Check or Top Up MCP Account Credits",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_balance", "buy_100_credits"],
                    "default": "check_balance",
                },
                "pay_method": {
                    "type": "string",
                    "enum": ["alipay", "alipay_hk", "stripe"],
                    "default": "stripe",
                },
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
        },
    },
    {
        "name": "assess_bank_account_eligibility",
        "description": "Assess HK corporate bank account opening eligibility, official bank tariff schedules (Tariff Guide), and tailored statutory KYC document checklists for HSBC Hong Kong and OCBC Bank Hong Kong (unlogged-in users are subject to the 3 free queries/day per IP limit; 20 free/day with API key from https://www.86hc.com/user).",
        "annotations": {
            "title": "Assess HK Corporate Bank Account Eligibility",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Optional Hong Kong company name, 7-digit CR No., or 8-digit BRN."},
                "bank_target": {"type": "string", "enum": ["hsbc", "ocbc", "both"], "default": "both"},
                "industry": {"type": "string", "default": "EXPORT_TRADE"},
                "has_mainland_entity": {"type": "boolean", "default": True},
                "annual_turnover_usd": {"type": "string", "default": "1M_TO_3M"},
                "api_key": {"type": "string", "description": "Optional 86hc.com API Key (hkq_live_xxxx)."},
            },
        },
    },
    {
        "name": "submit_bank_account_application",
        "description": "Submit an online Hong Kong corporate bank account opening pre-screening application (Stage 1 KYC dossier) for HSBC Hong Kong ('hsbc') or OCBC Bank Hong Kong ('ocbc'). Requires user login (personal API Key hkq_live_... obtained at https://www.86hc.com/user). Returns an official BK-YYYYMMDD-XXXXXX reference ID and a Stage 2 continuation URL.",
        "annotations": {
            "title": "Submit HK Bank Account Pre-Screening Application",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Hong Kong company name, 7-digit CR number, or 8-digit BRN."},
                "bank_target": {"type": "string", "enum": ["hsbc", "ocbc", "both"], "default": "hsbc"},
                "contact_name": {"type": "string", "description": "Full name of applicant / director."},
                "contact_phone": {"type": "string", "description": "Contact mobile phone with country code (e.g. +86 138... or +852 ...)."},
                "contact_email": {"type": "string", "description": "Applicant email address for official confirmation receipt."},
                "contact_wechat": {"type": "string", "description": "Optional WeChat ID or WhatsApp."},
                "industry": {"type": "string", "default": "EXPORT_TRADE"},
                "products_services": {"type": "string", "default": ""},
                "turnover": {"type": "string", "default": "1M_TO_3M"},
                "has_mainland_company": {"type": "boolean", "default": True},
                "mainland_company_name": {"type": "string", "default": ""},
                "signing_location": {"type": "string", "default": ""},
                "user_note": {"type": "string", "default": ""},
                "api_key": {"type": "string", "description": "Personal 86hc.com API Key (hkq_live_xxxx) obtained after signing in at https://www.86hc.com/user."},
            },
            "required": ["identifier", "contact_name", "contact_phone"],
        },
    },
    {
        "name": "check_bank_application_status",
        "description": "Check live compliance review status and Stage 2 upload link for a submitted bank account application (BK-YYYYMMDD-XXXXXX). Requires user login (personal API Key hkq_live_... obtained at https://www.86hc.com/user).",
        "annotations": {
            "title": "Check Bank Application Review Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Bank application reference ID (e.g. BK-20261028-XXXXXX)."},
                "contact_phone": {"type": "string", "description": "Applicant phone number (or last 4+ digits) for verification."},
                "contact_email": {"type": "string", "description": "Applicant email address for verification."},
                "api_key": {"type": "string", "description": "Personal 86hc.com API Key (hkq_live_xxxx) obtained after signing in at https://www.86hc.com/user."},
            },
            "required": ["order_id"],
        },
    },
]


def _run_stdlib_stdio_server() -> None:
    """Zero-dependency MCP JSON-RPC 2.0 stdio transport loop."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params") or {}

        if method == "server/discover":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "supportedVersions": ["2026-07-28", "2025-06-18", "2025-03-26", "2024-11-05"],
                    "capabilities": {"tools": {"listChanged": False}},
                    "instructions": SYSTEM_INSTRUCTIONS,
                    "ttlMs": 3600000,
                    "cacheScope": "public",
                },
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        elif method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion", "2026-07-28"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "Hong Kong Company", "version": "1.2.4"},
                    "instructions": SYSTEM_INSTRUCTIONS,
                },
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        elif method == "tools/list":
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS_SCHEMA}}
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            t_name = params.get("name", "")
            t_args = params.get("arguments") or {}
            try:
                if t_name == "search_companies":
                    out = _sync_request_86hc(
                        "POST",
                        "search",
                        {
                            "query": t_args.get("query", ""),
                            "limit": t_args.get("limit", 5),
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "batch_get_company_details":
                    comp_list = t_args.get("companies") or t_args.get("identifiers") or []
                    if isinstance(comp_list, str):
                        comp_list = [comp_list]
                    out = _sync_request_86hc(
                        "POST",
                        "batch-company-detail",
                        {
                            "companies": comp_list[:10],
                            "identifiers": comp_list[:10],
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "get_company_filings":
                    out = _sync_request_86hc(
                        "POST",
                        "company-filings",
                        {
                            "identifier": t_args.get("identifier", ""),
                            "form_code": t_args.get("form_code", ""),
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "create_filing_order":
                    pay_m = t_args.get("pay_method", "stripe")
                    if pay_m not in ("alipay", "alipay_hk", "stripe"):
                        pay_m = "stripe"
                    email_val = t_args.get("email") or t_args.get("client_email", "")
                    out = _sync_request_86hc(
                        "POST",
                        "create-filing-order",
                        {
                            "identifier": t_args.get("identifier", ""),
                            "doc_code": t_args.get("doc_code", "NAR1"),
                            "barcode": t_args.get("barcode", ""),
                            "email": email_val,
                            "client_email": email_val,
                            "pay_method": pay_m,
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "check_filing_order_status":
                    out = _sync_request_86hc(
                        "POST",
                        "order-status",
                        {
                            "order_sn": t_args.get("order_sn", ""),
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "manage_account_credits":
                    pay_m = t_args.get("pay_method", "stripe")
                    if pay_m not in ("alipay", "alipay_hk", "stripe"):
                        pay_m = "stripe"
                    out = _sync_request_86hc(
                        "POST",
                        "credits",
                        {
                            "action": t_args.get("action", "check_balance"),
                            "pay_method": pay_m,
                            "api_key": t_args.get("api_key", ""),
                        },
                    )
                elif t_name == "assess_bank_account_eligibility":
                    out = _sync_request_86hc("POST", "bank-eligibility", t_args)
                elif t_name == "submit_bank_account_application":
                    out = _sync_request_86hc("POST", "bank-apply", t_args)
                elif t_name == "check_bank_application_status":
                    out = _sync_request_86hc("POST", "bank-status", t_args)
                else:
                    out = json.dumps({"success": False, "error": f"Unknown tool: {t_name}"})

                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": out}], "isError": False},
                }
            except Exception as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": str(e)}], "isError": True},
                }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        elif msg_id is not None:
            resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def main() -> None:
    if HAS_FASTMCP:
        mcp.run()
    else:
        _run_stdlib_stdio_server()


if __name__ == "__main__":
    main()
