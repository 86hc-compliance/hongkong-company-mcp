"""Offline checks for the Cursor plugin package.

The network handshake lives in scripts/mcp_readonly_handshake.py and is not
run from this module.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mcp_readonly_handshake as handshake  # noqa: E402
import validate_cursor_plugin as validator  # noqa: E402


class CursorPluginManifestTest(unittest.TestCase):
    def test_repository_manifest_is_valid(self) -> None:
        self.assertEqual(validator.validate_tree(ROOT), [])

    def test_existing_server_still_advertises_paid_tools(self) -> None:
        server = (ROOT / "server.py").read_text(encoding="utf-8")
        index = (ROOT / "index.js").read_text(encoding="utf-8")
        self.assertIn('"name": "create_filing_order"', server)
        self.assertIn('"name": "manage_account_credits"', server)
        self.assertIn("https://www.86hc.com/wp-json/hkquery/v1/mcp/rpc", index)

    def test_hardcoded_key_is_rejected(self) -> None:
        root = self._stage()
        mcp_path = root / "mcp.json"
        mcp = json.loads(mcp_path.read_text(encoding="utf-8"))
        mcp["mcpServers"]["hongkong-company"]["headers"]["X-API-Key"] = "hkq_" + "live_" + "abcdefghijklmnop"
        mcp_path.write_text(json.dumps(mcp), encoding="utf-8")
        errors = validator.validate_tree(root)
        self.assertTrue(errors)
        self.assertTrue(any("secret-shaped" in item or "X-API-Key" in item for item in errors))

    def test_second_manifest_is_rejected(self) -> None:
        root = self._stage()
        (root / "plugin.json").write_text("{}\n", encoding="utf-8")
        errors = validator.validate_tree(root)
        self.assertTrue(any("root plugin.json" in item for item in errors))

    def test_required_key_is_rejected(self) -> None:
        root = self._stage()
        manifest_path = root / ".cursor-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["variables"]["required"] = ["HK_COMPANY_API_KEY"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        errors = validator.validate_tree(root)
        self.assertTrue(any("must stay optional" in item for item in errors))

    def test_handshake_refuses_tool_calls_before_the_network(self) -> None:
        with self.assertRaises(RuntimeError):
            handshake._post_checked(
                handshake.MCP_URL,
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {}},
                {},
            )

    def _stage(self) -> Path:
        holder = tempfile.TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        root = Path(holder.name)
        shutil.copytree(ROOT / ".cursor-plugin", root / ".cursor-plugin")
        shutil.copyfile(ROOT / "mcp.json", root / "mcp.json")
        docs = root / "docs"
        docs.mkdir()
        shutil.copyfile(ROOT / "docs" / "cursor-marketplace.md", docs / "cursor-marketplace.md")
        return root


if __name__ == "__main__":
    unittest.main()
