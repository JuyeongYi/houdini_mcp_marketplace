"""Check that every tool a skill or subagent names still exists in the Houdini MCP tool packs.

Plugins and tools live in different repositories. Nothing else ties them together: a tool can
be renamed in HoudiniMCP and the skill that teaches it keeps compiling, so this script is the
seam. It reads the tool inventory straight from the HoudiniMCP source (its own AST scanner,
`scripts/gen_pack_readmes.py`, no Houdini needed) and scans every Markdown file under
`plugins/` for backticked snake_case identifiers.

An identifier passes when it is a tool name, a tool argument name or a package key (`sop`,
`dop_rbd` ... - read from the same source, so a new package needs no edit here). Anything else must be
listed in `scripts/tool_check_allowlist.txt` (node names used as examples, Houdini node types
such as `block_begin`), one per line. Unknown identifiers fail the check so a renamed tool is
caught before the plugin ships.

Also verifies the catalog: every plugin listed in `.claude-plugin/marketplace.json` exists,
its `plugin.json` name matches the folder, and declared dependencies are plugins in the catalog.

    python scripts/check_tools.py                    # HoudiniMCP clone next to this repository
    python scripts/check_tools.py --mcp-repo D:/src/HoudiniMCP
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
CATALOG = ROOT / ".claude-plugin" / "marketplace.json"
ALLOWLIST = ROOT / "scripts" / "tool_check_allowlist.txt"

TOKEN = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")
"""A backticked lowercase identifier with at least one underscore - how skills name tools."""


def inventory(mcp_repo: Path) -> tuple[set[str], set[str], set[str]]:
    """(tool names, argument names, package keys) from the HoudiniMCP source, via its own README generator."""
    script = mcp_repo / "scripts" / "gen_pack_readmes.py"
    if not script.is_file():
        raise SystemExit(f"HoudiniMCP checkout not found: {script}. Pass --mcp-repo.")
    spec = importlib.util.spec_from_file_location("hmcp_gen_pack_readmes", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    tools: set[str] = set()
    args: set[str] = set()
    keys: set[str] = set()
    prefix = f"{module.SERVER_PACKAGE}_"
    for pack in module.load_packs():
        if pack.name.startswith(prefix):
            keys.add(pack.name.removeprefix(prefix))  # the key load_package takes
        for mod in pack.modules:
            for tool in mod.tools:
                tools.add(tool.name)
                args.update(arg.name for arg in tool.args)
    return tools, args, keys


def load_allowlist() -> set[str]:
    if not ALLOWLIST.is_file():
        return set()
    return {
        line.strip()
        for line in ALLOWLIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def check_catalog() -> list[str]:
    problems: list[str] = []
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    names = {entry["name"] for entry in catalog["plugins"]}
    for entry in catalog["plugins"]:
        folder = ROOT / entry["source"]
        manifest = folder / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            problems.append(f"{entry['name']}: missing {manifest.relative_to(ROOT)}")
            continue
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("name") != entry["name"]:
            problems.append(f"{entry['name']}: plugin.json name is {data.get('name')!r}")
        if folder.name != entry["name"]:
            problems.append(f"{entry['name']}: folder is {folder.name!r}")
        for dep in data.get("dependencies", []):
            if dep not in names:
                problems.append(f"{entry['name']}: dependency {dep!r} is not in the catalog")
    on_disk = {p.name for p in PLUGINS.iterdir() if p.is_dir()}
    for orphan in sorted(on_disk - names):
        problems.append(f"plugins/{orphan} exists but is not listed in marketplace.json")
    return problems


def check_tools(tools: set[str], args: set[str], allow: set[str]) -> tuple[list[str], dict[str, set[str]]]:
    problems: list[str] = []
    used: dict[str, set[str]] = defaultdict(set)
    for path in sorted(PLUGINS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        plugin = path.relative_to(PLUGINS).parts[0]
        for match in TOKEN.finditer(text):
            token = match.group(1)
            if token in tools:
                used[plugin].add(token)
            elif token not in args and token not in allow:
                line = text.count("\n", 0, match.start()) + 1
                problems.append(f"{path.relative_to(ROOT)}:{line}: `{token}` is not a tool, argument or allowlisted name")
    return problems, used


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument("--mcp-repo", type=Path, default=ROOT.parent / "HoudiniMCP",
                        help="HoudiniMCP checkout to read the tool inventory from")
    parsed = parser.parse_args()

    tools, args, keys = inventory(parsed.mcp_repo.resolve())
    problems = check_catalog()
    tool_problems, used = check_tools(tools, args, load_allowlist() | keys)
    problems.extend(tool_problems)

    referenced = set().union(*used.values()) if used else set()
    print(f"inventory: {len(tools)} tools, {len(args)} arguments, {len(keys)} packages from {parsed.mcp_repo}")
    print(f"plugins reference {len(referenced)} distinct tools; "
          f"{len(tools - referenced)} tools are not mentioned by any skill or agent")
    for problem in problems:
        print("FAIL", problem)
    if problems:
        print(f"{len(problems)} problem(s). Rename the tool reference, or add a non-tool name to {ALLOWLIST.relative_to(ROOT)}.")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
