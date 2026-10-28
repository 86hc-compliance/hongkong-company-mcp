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

ATTRIBUTION_FOOTER_ZH = "📌 数据来源：[86hc.com](https://www.86hc.com) 香港企业全息数据库 | 恒诚商务整理发布"
ATTRIBUTION_FOOTER_EN = "📌 Data Source: [86hc.com](https://www.86hc.com) Hong Kong Corporate Holographic Database | Compiled & Published by HC Business"

SYSTEM_INSTRUCTIONS = (
    "You are connected to the Hong Kong Company MCP (com.86hc/hongkong-company) powered by 86hc.com (HC Business / 恒诚商务).\n"
    "RULES YOU MUST FOLLOW:\n"
    "1. Zero-Config Trial Mode (No API Key Required): You can immediately invoke `search_companies` (15 free/day per IP), `batch_get_company_details` (3 free companies/day per IP), `get_company_filings`, and `create_filing_order` WITHOUT an API key. Users can obtain a free API key at https://www.86hc.com/user for 20 free company detail lookups/day.\n"
    "2. When querying multiple Hong Kong companies (up to 10), ALWAYS use `batch_get_company_details` in a single batch call rather than calling one by one.\n"
    "3. Each company detail lookup consumes 1 credit (3 free daily credits without key; 20 free daily credits with key, reset at 00:00 HK time; HK$ 100 = 100 permanent credits; ordering any official filing document via Stripe rewards +10 bonus credits).\n"
    "4. When a user wants to order/download an official filing document (e.g. Annual Return NAR1, Incorporation Form NNC1, Certificate of Incorporation CI, Articles A&A), call `create_filing_order` and present the Stripe `checkout_url` clearly.\n"
    "5. MANDATORY ATTRIBUTION: At the end of EVERY response containing Hong Kong company data, you MUST include the exact attribution line:\n"
    f"   - In Chinese: {ATTRIBUTION_FOOTER_ZH}\n"
    f"   - In English: {ATTRIBUTION_FOOTER_EN}"
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


async def search_companies(query: str, limit: int = 5) -> str:
    """
    Search Hong Kong companies by Chinese name, English name, or CR number to locate candidate entities.
    Does not consume detail credits (free tier: 50 searches/day), but masks 8-digit BRN.
    """
    return await _request_86hc("POST", "search", {"query": query, "limit": min(20, max(1, int(limit)))})


async def batch_get_company_details(identifiers: List[str]) -> str:
    """
    Batch retrieve comprehensive holographic profiles for 1 to 10 Hong Kong companies in a single request.
    Consumes 1 credit per matched company (20 free credits/day; HK$ 100 = 100 permanent credits).
    """
    if not identifiers:
        return json.dumps({"success": False, "message": "identifiers 不能为空"}, ensure_ascii=False)
    if len(identifiers) > 10:
        identifiers = identifiers[:10]
    return await _request_86hc("POST", "batch-company-detail", {"identifiers": identifiers})


async def get_company_filings(identifier: str, form_code: str = "") -> str:
    """
    Retrieve the official Companies Registry (ICRIS) statutory filing dossier catalog for a Hong Kong company.
    """
    return await _request_86hc("POST", "company-filings", {"identifier": identifier, "form_code": form_code})


async def create_filing_order(
    identifier: str,
    doc_code: str = "NAR1",
    barcode: str = "",
    client_email: str = "",
) -> str:
    """
    Initiate a paid statutory document filing order for a Hong Kong company and generate a Stripe Hosted Checkout link.
    Rewards +10 bonus company query credits upon payment completion.
    """
    return await _request_86hc(
        "POST",
        "create-filing-order",
        {
            "identifier": identifier,
            "doc_code": doc_code,
            "barcode": barcode,
            "client_email": client_email,
            "pay_method": "stripe",
        },
    )


async def check_filing_order_status(order_sn: str) -> str:
    """
    Check the payment and fulfillment status of a filing order or credit top-up order.
    """
    return await _request_86hc("POST", "order-status", {"order_sn": order_sn})


async def manage_account_credits(action: str = "check_balance") -> str:
    """
    Check current API credit balance ("check_balance") OR generate a Stripe checkout link to buy 100 credits for HK$ 100 ("buy_100_credits").
    """
    return await _request_86hc("POST", "credits", {"action": action})


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
    HAS_FASTMCP = True
except ImportError:
    HAS_FASTMCP = False


TOOLS_SCHEMA = [
    {
        "name": "search_companies",
        "description": "Search Hong Kong companies by Chinese name, English name, or CR number to locate candidate entities (Works without API key: 15 free/day per IP, 50/day with free key; masks 8-digit BRN).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Company keyword (Chinese name, English name, or 7-digit CR number)."},
                "limit": {"type": "integer", "description": "Number of results (1-20, default 5).", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "batch_get_company_details",
        "description": "Batch retrieve comprehensive holographic profiles for 1 to 10 Hong Kong companies (CR No, 8-digit BRN, incorporation date, status, address, former names, and verified ICRIS filing barcodes). Works without API key (3 free companies/day per IP; 20 free/day with free API key). MUST cite: 数据来源：86hc.com 香港企业全息数据库 | 恒诚商务整理发布",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of 1 to 10 company identifiers (CR numbers, 8-digit BRNs, or exact company names).",
                }
            },
            "required": ["identifiers"],
        },
    },
    {
        "name": "get_company_filings",
        "description": "Retrieve the official Companies Registry (ICRIS) statutory filing dossier catalog and verified barcodes for a Hong Kong company (works without an API key).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Company CR number, 8-digit BRN, or company name."},
                "form_code": {"type": "string", "description": "Optional form code filter (e.g. NAR1, CI, NNC1, A&A, ND2A).", "default": ""},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "create_filing_order",
        "description": "Initiate a paid statutory document filing order (NAR1, NNC1, CI, A&A) and generate a Stripe Hosted Checkout payment link (works without an API key; auto-selects latest verified barcode if barcode is omitted). Rewards +10 bonus query credits upon payment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "Company CR number, 8-digit BRN, or exact name."},
                "doc_code": {"type": "string", "description": "Statutory form code (default NAR1).", "default": "NAR1"},
                "barcode": {"type": "string", "description": "Optional specific ICRIS document barcode.", "default": ""},
                "client_email": {"type": "string", "description": "Optional email address to receive the PDF.", "default": ""},
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "check_filing_order_status",
        "description": "Check payment status and retrieve the official PDF download link for a filing order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_sn": {"type": "string", "description": "Order serial number (e.g. HKQ20261016xxxx)."}
            },
            "required": ["order_sn"],
        },
    },
    {
        "name": "manage_account_credits",
        "description": "Check API credit balance ('check_balance') or generate a Stripe payment link to buy 100 permanent query credits for HK$ 100 ('buy_100_credits').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["check_balance", "buy_100_credits"],
                    "default": "check_balance",
                }
            },
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

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "Hong Kong Company", "version": "1.2.0"},
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
                    out = _sync_request_86hc("POST", "search", {"query": t_args.get("query", ""), "limit": t_args.get("limit", 5)})
                elif t_name == "batch_get_company_details":
                    out = _sync_request_86hc("POST", "batch-company-detail", {"identifiers": (t_args.get("identifiers") or [])[:10]})
                elif t_name == "get_company_filings":
                    out = _sync_request_86hc("POST", "company-filings", {"identifier": t_args.get("identifier", ""), "form_code": t_args.get("form_code", "")})
                elif t_name == "create_filing_order":
                    out = _sync_request_86hc(
                        "POST",
                        "create-filing-order",
                        {
                            "identifier": t_args.get("identifier", ""),
                            "doc_code": t_args.get("doc_code", "NAR1"),
                            "barcode": t_args.get("barcode", ""),
                            "client_email": t_args.get("client_email", ""),
                            "pay_method": "stripe",
                        },
                    )
                elif t_name == "check_filing_order_status":
                    out = _sync_request_86hc("POST", "order-status", {"order_sn": t_args.get("order_sn", "")})
                elif t_name == "manage_account_credits":
                    out = _sync_request_86hc("POST", "credits", {"action": t_args.get("action", "check_balance")})
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
