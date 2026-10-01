---
name: houdini-mcp-workflow
description: "Working rules for driving a live Houdini session through the Houdini MCP tools."
when_to_use: "Use at the start of any Houdini task (building, editing, simulating, rendering, exporting) and whenever a Houdini MCP tool fails, times out, or the scene looks different from what you expected."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server (houdini_mcp)."
---

# Working in Houdini through MCP

The MCP server runs **inside a GUI Houdini session**. Every tool acts on the scene the user has open, in real time. Tool names below are bare names; the prefix depends on how the server is connected (plugin or project `.mcp.json`).

Each tool's MCP description is its full docstring, and every argument carries its own description in the input schema. Fixed choices (modes, kinds, types) are enums there: pick from the list instead of guessing.

## Start of a task

1. `scene_info` — scene path, unsaved changes, frame range, current frame.
2. `network_overview` on the network you will work in, then `explain_node` on nodes you plan to touch.
3. Packages: only the base package is loaded at start. `get_entries` lists every package (key, description, tools - even unloaded ones). Load what the task needs with `load_package(key)` (for example `sop`, `dop`, `lop`); only a few fit at once, so `unload_package` ones you are done with. The new tools appear in your tool list right after loading. If a tool you expect is in no entry, its package is not installed or failed to load (`failed` in the entry); say so instead of emulating it with `run_python`. `describe_tool` gives one loaded tool's full description and arguments.

## Look up names, don't guess them

- Node types: `list_node_types` (by category, name pattern or task keyword `query`) → `node_type_info` for parameter names and inputs (`detailed=True` adds menu tokens), **before** creating the node. For shader (Vop) and Copernicus (Cop) types it also gives `ports`: connector names and data types.
- After creating: `parm_info` / `list_parms` on the actual node. Attributes: `list_attributes`. VEX functions: `vex_function_info`.
- Vector parms are set by component (`tx`, `ty`, `tz`) or as a list, some parms are tuples, menus take tokens, and buttons are pressed, not set.
- Wiring: `node_info` → `ports` lists each input/output by name (and data type for VOP/COP) with what is connected. `connect_nodes` / `disconnect_input` take a port index or name (`"base_color"`); on VOP/COP they refuse a data-type combination Houdini cannot convert and say what to insert. Any network works the same way (SOP, VOP shader graphs, COP, CHOP) - `create_node` also makes networks such as `chopnet`.

## Respect the user's scene

- **Read before you change.** The user may have rewired nodes, moved display flags or added their own nodes since your last look. Re-read (`node_info`, `network_graph`) before acting. `network_graph(include_references=True)` also shows Object Merge and expression references.
- **Never silently override the user's edits.** If your plan conflicts with a change they made (a display flag on their node, a different input wiring), ask first.
- If you temporarily change a flag or the current frame to inspect something, restore it.

## Creating and editing nodes

- `comment` is required when creating nodes. Write it, node names and any string that ends up in the scene in **English**.
- Name nodes by role (`wall_body`, `flag_pin_edge`), never `box1`.
- Each node or parameter edit is **one undo step** (shown as `MCP: ...` in the undo history; `describe_tool` shows whether a tool is undoable). Scene loads, saves, `set_frame_range` and files written to disk are not undone by Ctrl+Z.
- Three or more connected nodes: build them with one `create_network` call instead of repeated `create_node`. It is all-or-nothing (a wrong type, parameter or input removes every node of the call) and `dry_run=True` validates without touching the scene. Inputs refer to other nodes of the same call by `name`, in any order.
- Took a wrong step: `undo` takes back your last tool call exactly (node, parameters, wiring, flags), `redo` re-applies it. `undo` stops at changes the user made by hand unless they agree (`allow_user_changes=True`).
- Many edits on a heavy network or simulation: `set_update_mode("manual")` first so each edit does not recook, and **always** set it back to `"auto"` when done.
- HDA parameters that rebuild something in a callback: `set_parms(..., run_callbacks=True)`. Setting a value by script does not fire callbacks.
- Tool errors are written to be acted on: read the message, it says what to do next.

## Output goes through ROPs

- Caches, renders and exports are made by ROP-based tools: `run_rop` for any ROP in the scene, and each pack's cache/export/render tools. The ROP stays in the scene so a person can re-run the same output later.
- **Never use `run_python` to write caches, renders or exports** (no `saveToFile` loops, no hand-launched `husk`).
- Pass `frame_range` explicitly and try 1–2 frames first. `run_rop` refuses a ROP whose range still follows `$FSTART`/`$FEND` unless you pass one, and the range you pass stays on the ROP - give the full range when you run it for real.

## Long operations and the main thread

- Tools that touch `hou` run on Houdini's main thread and the server waits **120 s** for them (`MainThreadTimeout`). A long foreground render, cache or sim blocks the main thread: later calls time out, and a timed-out call still runs once Houdini is free, so re-read the scene before retrying. `job_status` and `cancel_job` do not wait for the main thread.
- Run heavy work in the background: `run_rop(background=True)`, then poll `job_status`. For USD/Karma renders use the render package's `start_render`, which reports to the same `job_status`. `cancel_job(job)` stops any background job. Background runs work on a snapshot of the session, so the user's .hip is not overwritten, but the scene must have been saved once: a never-saved scene is refused (saving it would open a modal dialog that blocks Houdini), so ask the user where to save it (`save_scene(path)`).
- Do not press a ROP's "render in background" button parameter; use the tools above.

## Escape hatch

`run_python` is the last resort for things no tool covers. Always pass a meaningful `comment`. If you find yourself using it repeatedly for the same job, report the missing tool.

## Verify, don't assume

After building or changing something, look at it (`viewport_snapshot`, `viewport_sequence`) and read numbers (`geometry_stats`, `node_errors`). See the `visual-review` skill.

- Same attribute across several nodes or frames: `attrib_stats(paths=[...], frames=[...])` returns one compact table; `percentiles=[1, 50, 99]` shows outliers.
- Volumes: `sample_volume` reads fields at positions and `compare_volumes` shows how one field sits in the value bands of another. The `sampling` method changes the number: `index` is the stored voxel value unblended, `linear` (default) is trilinear, `smooth` and `cubic` are higher-order. A Copernicus layer is read the same way (`index` or `linear`; `space` = world / image / texture / pixel / index).
