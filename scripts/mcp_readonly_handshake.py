#!/usr/bin/env python3
"""Read-only MCP handshake against the existing 86hc.com endpoint.

Sends initialize and tools/list only. It does not send tools/call, does not
read HK_COMPANY_API_KEY from the environment, and does not print response
bodies. An empty header and the unsubstituted placeholder are compared with
the no-header guest handshake so the plugin config can be checked without
placing an order or retrieving a company record.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

MCP_URL = "https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc"
ALLOWED_METHODS = {"initialize", "tools/list"}
EXPECTED_TOOLS = (
    "search_companies",
    "batch_get_company_details",
    "get_company_filings",
    "create_filing_order",
    "check_filing_order_status",
    "manage_account_credits",
    "assess_bank_account_eligibility",
    "submit_bank_account_application",
    "check_bank_application_status",
)
PAID_SURFACE = ("create_filing_order", "manage_account_credits")
LIVE_SECRET_RE = re.compile(r"hkq_live_[A-Za-z0-9]{8,}|sk_(?:live|test)_[A-Za-z0-9]+")
FEE_WORDS = ("stripe", "alipay", "payment", "checkout", "credit", "hk$")


def _post_checked(url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], bytes]:
    method = payload.get("method")
    if method not in ALLOWED_METHODS:
        raise RuntimeError(f"refusing to send MCP method {method!r}")
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            host = (urlparse(response.geturl()).hostname or "").lower()
            if host != "www.86hc.com":
                raise RuntimeError("refusing a redirect away from www.86hc.com")
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read(200000)
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read(200000)


def _base_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "86hc-cursor-plugin-readonly-check/1.3.2",
    }
    if extra:
        headers.update(extra)
    return headers


def _decode_message(body: bytes) -> Dict[str, Any]:
    text = body.decode("utf-8", "replace")
    if LIVE_SECRET_RE.search(text):
        raise RuntimeError("response contained a live-secret-shaped token; output suppressed")
    if text.lstrip().startswith("data:") or text.lstrip().startswith("event:"):
        data_lines = [line[5:].strip() for line in text.splitlines() if line.startswith("data:")]
        if not data_lines:
            raise RuntimeError("SSE response had no data line")
        text = data_lines[-1]
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise RuntimeError("MCP response was not a JSON object")
    return parsed


def _tool_rows(message: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = message.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("tools/list result missing")
    tools = result.get("tools")
    if not isinstance(tools, list):
        raise RuntimeError("tools/list did not return a tool array")
    rows = []
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            raise RuntimeError("tools/list contained an unnamed tool")
        annotations = tool.get("annotations") if isinstance(tool.get("annotations"), dict) else {}
        rows.append(
            {
                "name": tool["name"],
                "readOnlyHint": annotations.get("readOnlyHint"),
                "destructiveHint": annotations.get("destructiveHint"),
            }
        )
    return rows


def _fee_flags(message: Dict[str, Any]) -> Dict[str, bool]:
    result = message.get("result")
    descriptions = []
    if isinstance(result, dict) and isinstance(result.get("tools"), list):
        for tool in result["tools"]:
            if isinstance(tool, dict) and isinstance(tool.get("description"), str):
                descriptions.append(tool["description"].lower())
    blob = "\n".join(descriptions)
    return {word: word in blob for word in FEE_WORDS}


def run(url: str) -> Dict[str, Any]:
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "86hc-cursor-plugin-readonly-check", "version": "1.3.2"},
        },
    }
    status, headers, body = _post_checked(url, init, _base_headers())
    message = _decode_message(body)
    result = message.get("result") if isinstance(message.get("result"), dict) else {}
    server_info = result.get("serverInfo") if isinstance(result.get("serverInfo"), dict) else {}
    summary: Dict[str, Any] = {
        "url": url,
        "methods_sent": ["initialize", "tools/list"],
        "tools_call_sent": False,
        "api_key_sent": False,
        "initialize_status": status,
        "protocolVersion": result.get("protocolVersion"),
        "server_name": server_info.get("name"),
        "server_version": server_info.get("version"),
        "session_header": "mcp-session-id" in headers,
    }
    modes = {
        "no-header": None,
        "empty-key": {"X-API-Key": ""},
        "literal-placeholder": {"X-API-Key": "${HK_COMPANY_API_KEY}"},
    }
    listings = {}
    for name, extra in modes.items():
        list_payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        list_status, _, list_body = _post_checked(url, list_payload, _base_headers(extra))
        listed = _decode_message(list_body)
        rows = _tool_rows(listed)
        listings[name] = {
            "status": list_status,
            "tools": rows,
            "fee_words_in_descriptions": _fee_flags(listed),
        }
    names = [row["name"] for row in listings["no-header"]["tools"]]
    same = all([row["name"] for row in item["tools"]] == names for item in listings.values())
    summary["modes"] = {
        name: {
            "status": item["status"],
            "tool_count": len(item["tools"]),
            "fee_words_in_descriptions": item["fee_words_in_descriptions"],
        }
        for name, item in listings.items()
    }
    summary["tools"] = listings["no-header"]["tools"]
    summary["tool_names_match_across_header_modes"] = same
    summary["expected_tools_present"] = list(names) == list(EXPECTED_TOOLS)
    summary["paid_tools_advertised"] = all(tool in names for tool in PAID_SURFACE)
    return summary


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Read-only initialize and tools/list handshake.")
    parser.add_argument("--url", default=MCP_URL)
    args = parser.parse_args(list(argv))
    if args.url != MCP_URL:
        print("error: this check is pinned to the existing public 86hc MCP endpoint", file=sys.stderr)
        return 2
    try:
        summary = run(args.url)
    except Exception as exc:  # noqa: BLE001 - the operator needs the failure class, not a traceback
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if (
        summary["initialize_status"] != 200
        or summary["protocolVersion"] != "2025-03-26"
        or not summary["tool_names_match_across_header_modes"]
        or not summary["expected_tools_present"]
        or not summary["paid_tools_advertised"]
        or any(item["status"] != 200 for item in summary["modes"].values())
    ):
        return 1
    if not all(summary["modes"]["no-header"]["fee_words_in_descriptions"].values()):
        print("error: tools/list descriptions did not expose the known payment vocabulary", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
