# Houdini MCP marketplace

A Claude Code plugin marketplace for [HoudiniMCP](https://github.com/JuyeongYi/HoudiniMCP): for each
tool pack, skills and subagents that teach **when and how to use its tools**. The tools themselves
(the MCP server and the Houdini packages) live in the HoudiniMCP repository; this repository holds
only the material that teaches them.

Why two repositories: the audiences differ. Houdini needs only `packages/`; Claude Code needs only
the skills. Kept together, a plugin install copied the pack's Python code, Houdini scanned the skill
folders, and a one-line skill edit landed in the tool code history.

한국어: [README.md](README.md)

## Install

```text
/plugin marketplace add JuyeongYi/houdini_mcp_marketplace
/plugin install houdini-mcp@houdini-mcp
/plugin install houdini-mcp-dop@houdini-mcp
```

- Pack plugins depend on `houdini-mcp` and `houdini-mcp-base`, which are installed with them.
- A plugin only **teaches** the tools. The tools appear only when the HoudiniMCP packages are loaded
  in the Houdini session; install them as the HoudiniMCP README describes.
- `houdini-mcp` declares the MCP server connection (`plugins/houdini-mcp/.mcp.json`,
  `http://127.0.0.1:<port>/mcp`). The port is a plugin option (default `22926`, the server's
  `HOUDINI_MCP_PORT`). If a project `.mcp.json` connects the same server, the tools appear twice under
  two prefixes; use one connection.

Update:

```text
/plugin marketplace update houdini-mcp
/plugin update houdini-mcp-dop@houdini-mcp
```

Installed copies update only when the `version` in `plugin.json` changes. **Bump the plugin's
`version` whenever you change its skills or agents.**

## Plugins

```
plugins/<plugin>/
  .claude-plugin/plugin.json     manifest (name houdini-mcp-<domain>)
  skills/<skill>/SKILL.md        skills
  agents/<agent>.md              subagents (only where useful)
```

| Plugin | HoudiniMCP pack | Skills | Subagents |
|---|---|---|---|
| `houdini-mcp` | `houdini_mcp` | `houdini-mcp-workflow` (+ MCP server connection) | |
| `houdini-mcp-base` | `houdini_mcp_base` | `visual-review`, `scene-debugging` | `houdini-scene-auditor` |
| `houdini-mcp-sop` | `houdini_mcp_sop` | `sop-procedural-modeling` | |
| `houdini-mcp-vex` | `houdini_mcp_vex` | `vex-wrangle-authoring` | |
| `houdini-mcp-mat` | `houdini_mcp_mat` | `materialx-lookdev` | |
| `houdini-mcp-lop` | `houdini_mcp_lop` | `usd-stage-debugging` | |
| `houdini-mcp-render` | `houdini_mcp_render` | `render-and-verify` | `render-qc` |
| `houdini-mcp-dop` | `houdini_mcp_dop` | `dop-simulation-setup` | `simulation-debugger` |
| `houdini-mcp-dop-rbd` | `houdini_mcp_dop_rbd` | `rbd-destruction` | `rbd-diagnostician` |
| `houdini-mcp-hda` | `houdini_mcp_hda` | `hda-authoring` | |
| `houdini-mcp-rig` | `houdini_mcp_rig` | `kinefx-apex-rigging` | |
| `houdini-mcp-chop` | `houdini_mcp_chop` | `channel-analysis` | |
| `houdini-mcp-io` | `houdini_mcp_io` | `export-and-verify` | |
| `houdini-mcp-cop` | `houdini_mcp_cop` | `copernicus-textures` | |
| `houdini-mcp-top` | `houdini_mcp_top` | `pdg-cooking` | |
| `houdini-mcp-groom` | `houdini_mcp_groom` | `groom-inspection` | |

## Staying in step with the tools

With two repositories, a tool rename in HoudiniMCP breaks nothing here on its own. `scripts/check_tools.py`
is the seam: it reads the tool and argument names from the HoudiniMCP source (through its
`scripts/gen_pack_readmes.py`, no Houdini needed) and checks that every backticked snake_case
identifier in the skills and agents exists. Names that are deliberately not tools (node names used as
examples, node types) go in `scripts/tool_check_allowlist.txt`.

```text
python scripts/check_tools.py                    # reads ../HoudiniMCP
python scripts/check_tools.py --mcp-repo <path>
claude plugin validate . --strict                # the marketplace
claude plugin validate plugins/houdini-mcp-dop --strict
```

Run both after editing a skill and after changing tools in HoudiniMCP.

## Writing rules

- Plugin content is English.
- A skill states only facts measured in Houdini or stated by the tool itself. Tool lists and arguments
  live in each pack's generated `README.md` in HoudiniMCP; a skill explains when and how to use tools,
  not every argument.
- Tools are named bare (`make_video`), without a prefix: the prefix depends on how the server is connected.
- Skill frontmatter: `name`, `description` (what it does), `when_to_use` (when), `compatibility` (the pack it needs).
- Subagent frontmatter: `tools` opens only Read/Grep/Glob, `ToolSearch` (loads deferred MCP tools) and the Houdini server's tools, under both prefixes -
  the plugin connection (`mcp__plugin_houdini-mcp_houdini__*`) and a project `.mcp.json` server keyed `houdini`
  (`mcp__houdini__*`). A server under another key is invisible to the agents. `run_python` is blocked with
  `disallowedTools`; `model` and `effort` are set per job (sonnet for mechanical checks, opus for diagnosis).
