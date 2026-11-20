#!/usr/bin/env python3
"""Validate this repo's Cursor plugin manifest.

The schema snapshot at scripts/cursor_plugin_schema.json is the unmodified
file from:

https://raw.githubusercontent.com/cursor/plugins/main/schemas/plugin.schema.json

Git blob 02903d117b6a0e3bf6acd35aab3d48d91cd54a5e
$id https://cursor.com/schemas/cursor-plugin/plugin.json

Checked against the plugin docs at https://cursor.com/docs/plugins and
https://cursor.com/docs/reference/plugins on 2026-11-20. This script does
not submit anything to the Marketplace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, List

SCHEMA_SHA256 = "31db124b1c7e43c22abb13ebf7e7c74556482e480fd492b80638d815c85b96b1"
SCHEMA_URL = "https://raw.githubusercontent.com/cursor/plugins/main/schemas/plugin.schema.json"
SCHEMA_ID = "https://cursor.com/schemas/cursor-plugin/plugin.json"
MCP_URL = "https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc"
API_KEY_VAR = "HK_COMPANY_API_KEY"
PLACEHOLDER = "${" + API_KEY_VAR + "}"
VARIABLE_KEYWORDS = {
    "type",
    "title",
    "description",
    "default",
    "enum",
    "const",
    "properties",
    "required",
    "items",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "pattern",
    "minItems",
    "maxItems",
    "uniqueItems",
}
SECRET_PATTERNS = (
    re.compile(r"hkq_live_[A-Za-z0-9]{8,}"),
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]+"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
ENV_PLACEHOLDER_RE = re.compile(r"\$\{env:[^}]+\}")
FORBIDDEN_BRAND_RE = re.compile(r"aliad", re.IGNORECASE)
CLAIM_RES = (
    re.compile(r"已合规"),
    re.compile(r"已经合规"),
    re.compile(r"marketplace[- ]certified", re.IGNORECASE),
    re.compile(r"official cursor partner", re.IGNORECASE),
)


def schema_path() -> Path:
    return Path(__file__).resolve().with_name("cursor_plugin_schema.json")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_tree(root: Path) -> List[str]:
    errors: List[str] = []
    root = root.resolve()
    manifest_path = root / ".cursor-plugin" / "plugin.json"
    mcp_path = root / "mcp.json"
    doc_path = root / "docs" / "cursor-marketplace.md"
    schema_file = schema_path()

    if sha256_file(schema_file) != SCHEMA_SHA256:
        errors.append("pinned Cursor plugin schema hash does not match the reviewed snapshot")
    if not manifest_path.is_file():
        errors.append("missing .cursor-plugin/plugin.json")
    if not mcp_path.is_file():
        errors.append("missing mcp.json")
    if not doc_path.is_file():
        errors.append("missing docs/cursor-marketplace.md")
    if (root / "plugin.json").exists():
        errors.append("root plugin.json must stay absent; it is a different manifest format and cannot declare Cursor variables")
    if (root / ".cursor-plugin" / "marketplace.json").exists():
        errors.append(".cursor-plugin/marketplace.json must stay absent; this repository packages one plugin, not a multi-plugin index")
    if errors:
        return errors

    try:
        import jsonschema
        from jsonschema import Draft7Validator, FormatChecker
    except ImportError:
        return ["jsonschema is not installed; pip install -r scripts/requirements-cursor-plugin-check.txt"]

    schema = load_json(schema_file)
    if schema.get("$id") != SCHEMA_ID:
        errors.append("pinned schema $id is not the Cursor plugin manifest schema")
    try:
        Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as exc:
        errors.append(f"pinned schema is not a valid Draft-07 schema: {exc.message}")
        return errors

    try:
        manifest = load_json(manifest_path)
    except json.JSONDecodeError as exc:
        return [f"plugin.json is not JSON: {exc}"]
    try:
        mcp = load_json(mcp_path)
    except json.JSONDecodeError as exc:
        return errors + [f"mcp.json is not JSON: {exc}"]

    validator = Draft7Validator(schema, format_checker=FormatChecker())
    for err in sorted(validator.iter_errors(manifest), key=lambda item: list(item.absolute_path)):
        loc = "/".join(str(part) for part in err.absolute_path) or "<root>"
        errors.append(f"plugin.json {loc}: {err.message}")

    errors.extend(_check_manifest_policy(manifest))
    errors.extend(_check_logo(root, manifest))
    errors.extend(_check_mcp(mcp, manifest))
    errors.extend(_check_secrets(manifest_path, mcp_path))
    errors.extend(_check_disclosure(doc_path.read_text(encoding="utf-8")))
    return errors


def _check_manifest_policy(manifest: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(manifest, dict):
        return ["plugin.json must be an object"]
    if manifest.get("name") != "86hc-hongkong-company":
        errors.append("plugin name must stay 86hc-hongkong-company")
    if manifest.get("publisher") != "HC BUSINESS LIMITED":
        errors.append("publisher must stay HC BUSINESS LIMITED")
    author = manifest.get("author")
    if not isinstance(author, dict) or author.get("name") != "HC BUSINESS LIMITED":
        errors.append("author.name must stay HC BUSINESS LIMITED")
    if manifest.get("homepage") != "https://www.86hc.com":
        errors.append("homepage must stay https://www.86hc.com")
    if manifest.get("license") != "MIT":
        errors.append("license must stay MIT")
    if manifest.get("mcpServers") != "./mcp.json":
        errors.append('mcpServers must be the relative path "./mcp.json"')
    description = manifest.get("description")
    if not isinstance(description, str) or "payment links" not in description:
        errors.append("plugin description must keep the payment-link disclosure")
    blob = json.dumps(manifest, ensure_ascii=False)
    if FORBIDDEN_BRAND_RE.search(blob):
        errors.append("plugin.json contains a brand that this package must not use")
    for claim in CLAIM_RES:
        if claim.search(blob):
            errors.append("plugin.json must not claim Marketplace compliance or endorsement")
    variables = manifest.get("variables")
    if not isinstance(variables, dict):
        errors.append("variables schema is required so the API key is injected by Cursor and not stored here")
        return errors
    properties = variables.get("properties")
    if not isinstance(properties, dict) or API_KEY_VAR not in properties:
        errors.append(f"variables.properties.{API_KEY_VAR} is required")
    else:
        spec = properties[API_KEY_VAR]
        if not isinstance(spec, dict):
            errors.append(f"{API_KEY_VAR} variable schema must be an object")
        else:
            unknown = sorted(set(spec) - VARIABLE_KEYWORDS)
            if unknown:
                errors.append(
                    f"{API_KEY_VAR} uses variable keywords outside the documented set: {', '.join(unknown)}"
                )
            if spec.get("type") != "string":
                errors.append(f"{API_KEY_VAR} must be a string variable")
            if spec.get("default") != "":
                errors.append(f"{API_KEY_VAR} default must stay an empty string")
            if len(properties) != 1:
                errors.append("declare only HK_COMPANY_API_KEY until another value is actually injected")
    required = variables.get("required", [])
    if not isinstance(required, list) or API_KEY_VAR in required:
        errors.append(
            f"{API_KEY_VAR} must stay optional; a required key would drop the published guest quota path"
        )
    return errors


def _check_logo(root: Path, manifest: Any) -> List[str]:
    if not isinstance(manifest, dict):
        return []
    logo = manifest.get("logo")
    if logo != "assets/logo.png":
        return ['logo must be the relative path "assets/logo.png"']
    path = root / "assets" / "logo.png"
    if path.is_symlink():
        return ["assets/logo.png must be a regular file"]
    if not path.is_file():
        return ["assets/logo.png is missing"]
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return ["logo path escapes the plugin root"]
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ["assets/logo.png is not a PNG"]
    if not 100 <= len(data) <= 1_000_000:
        return ["assets/logo.png has an unexpected file size"]
    return []


def _check_mcp(mcp: Any, manifest: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(mcp, dict):
        return ["mcp.json must be an object"]
    servers = mcp.get("mcpServers")
    if not isinstance(servers, dict) or list(servers) != ["hongkong-company"]:
        errors.append('mcp.json must define one server named "hongkong-company"')
        return errors
    server = servers["hongkong-company"]
    if not isinstance(server, dict):
        return ["hongkong-company server entry must be an object"]
    allowed = {"type", "url", "headers"}
    extra = sorted(set(server) - allowed)
    if extra:
        errors.append(f"hongkong-company has unsupported fields: {', '.join(extra)}")
    if server.get("type") != "http":
        errors.append('hongkong-company type must be "http"')
    if server.get("url") != MCP_URL:
        errors.append(f"hongkong-company url must stay {MCP_URL}")
    headers = server.get("headers")
    if headers != {"X-API-Key": PLACEHOLDER}:
        errors.append(f'X-API-Key must be exactly "{PLACEHOLDER}" and no other header may be set')
    raw = json.dumps(mcp, ensure_ascii=False)
    if ENV_PLACEHOLDER_RE.search(raw):
        errors.append("plugin mcp.json must use ${HK_COMPANY_API_KEY}, not ${env:...}")
    names = PLACEHOLDER_RE.findall(raw)
    declared = set()
    variables = manifest.get("variables") if isinstance(manifest, dict) else None
    if isinstance(variables, dict) and isinstance(variables.get("properties"), dict):
        declared = set(variables["properties"])
    for name in names:
        if name not in declared:
            errors.append(f"mcp.json placeholder ${{{name}}} is not declared in plugin variables")
    if isinstance(variables, dict) and isinstance(variables.get("properties"), dict):
        for name in variables["properties"]:
            if name not in names:
                errors.append(f"variable {name} is not used by mcp.json")
    if FORBIDDEN_BRAND_RE.search(raw):
        errors.append("mcp.json contains a brand that this package must not use")
    return errors


def _check_secrets(*paths: Path) -> List[str]:
    errors: List[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.name} contains a secret-shaped literal ({pattern.pattern})")
    return errors


def _check_disclosure(text: str) -> List[str]:
    errors: List[str] = []
    required_bits = (
        "3.1",
        "create_filing_order",
        "manage_account_credits",
        "HK$",
        "does not meet Marketplace listing approval conditions",
        "https://cursor.com/marketplace-publisher-terms",
        MCP_URL,
    )
    for bit in required_bits:
        if bit not in text:
            errors.append(f"docs/cursor-marketplace.md is missing {bit}")
    for claim in CLAIM_RES:
        if claim.search(text):
            errors.append("marketplace doc must not claim that the plugin is already compliant or endorsed")
    if FORBIDDEN_BRAND_RE.search(text):
        errors.append("marketplace doc contains a brand that this package must not use")
    return errors


def check_upstream() -> List[str]:
    try:
        with urllib.request.urlopen(SCHEMA_URL, timeout=25) as response:
            payload = response.read()
    except Exception as exc:  # noqa: BLE001 - report the network failure as a check result
        return [f"could not fetch upstream schema: {exc}"]
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SCHEMA_SHA256:
        return [
            "upstream Cursor plugin schema changed since the pinned snapshot "
            f"(upstream {digest}, pinned {SCHEMA_SHA256})"
        ]
    return []


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate the Cursor plugin manifest in this repository.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--check-upstream",
        action="store_true",
        help="Compare the pinned schema bytes with the current cursor/plugins copy.",
    )
    args = parser.parse_args(argv)
    errors = validate_tree(args.root)
    if args.check_upstream:
        errors.extend(check_upstream())
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"ok: {args.root}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
