---
name: hda-authoring
description: "Turn Houdini subnets into Digital Assets and maintain them with the houdini_mcp_hda tools - collapse nodes into a subnet, create the asset, build the parameter interface, promote/edit inner parameters, unlock and re-save instance contents, edit sections and callbacks, set Tab-menu/input/label/icon options, install/reload, validate by cooking (including required-input wiring), and expand/collapse for Git."
when_to_use: "Use when packaging a network as an HDA, changing an HDA's interface, contents or scripts, or when an HDA fails to install, cook or validate."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_hda tool pack loaded."
---

# HDA authoring

> These tools are in the `hda` package, which is not loaded by default. If they are not in your tool list, call `load_package("hda")` first (`get_entries` shows every package).

The tools below edit the HDA definition (create, interface, sections,
options, validation). Editing the **contents** of an unlocked instance
(adding and wiring the inner nodes) uses the base pack's node tools
(`create_node`, `connect_nodes`, `set_parms`).

## Definition vs instance

- This pack edits the **HDA definition**: changes apply to every instance of the type and are saved into the `.hda` file.
- Base `add_spare_parm` changes **one node instance** only. Do not use it to change an asset's interface.

## Create

1. If the nodes to bake are not already a single subnet, group them first: `collapse_to_subnet(paths, name, comment)` — `paths` must share the same parent network, and `name` must not already exist in that network (it is rejected rather than silently renamed to `name1`).
2. `create_hda(path, name, hda_file, comment, namespace, version, label, icon, min_inputs, max_inputs)` — `name` is the core name without `::` (for example `brick_maker`); namespace and version make `ns::brick_maker::1.0`.
3. `hda_info(target)` — confirm metadata, sections and instances.

## Interface

- `promote_parm(path, inner, parm, link=True, relock=True)` — lift an inner node's parameter and link it with an expression. Needs an instance path to reach inner nodes. Give vectors by tuple name (`size`). With `link=True` it bakes the instance's contents into the definition and then re-locks the instance (`relock=False` keeps it unlocked for further inner edits — but an unlocked instance stops following later definition updates). Ramps cannot be linked with `ch()`: promote them with `link=False` and wire the inner ramp by hand.
- `add_hda_parm(target, kind, name, label, ..., disable_when, hide_when, script_callback, script_callback_language)` — new parameters (`kind`: float, int, string, toggle, menu, button, ramp_float, ramp_color or separator), optionally in a folder. `button` kind needs `script_callback` or pressing it does nothing. A menu `default` may be the token (`"brick"`) or its 0-based index.
- `edit_hda_parm(target, name, label=, default=, min_value=, max_value=, disable_when=, hide_when=, help_text=, script_callback=, ...)` — change an **existing** parameter in place (label, default, range, conditionals, callback) without breaking `ch()`/`chs()` expressions that `promote_parm` wired to it. Do not remove+re-add a parameter just to change its label or default — that breaks internal expressions. Menu defaults accept a token or index; int ranges are truncated to integers. Ramps are edited as a single parameter (label, help, conditionals). Kind, size, menu items and folders cannot change in place: `remove_hda_parm`, `add_hda_parm`, then re-link with `promote_parm`.
- `hda_interface(target)` to read, `reorder_hda_parms` to order top-level entries, `remove_hda_parm` to remove.
- Labels, help text and script comments in English.

## Editing instance contents (not just the interface)

The definition's internal node network is edited through an instance, then baked back:

1. `set_hda_editable(path, editable=True)` — unlock the instance's contents (`allowEditingOfContents`). Required before adding/wiring nodes inside a baked instance with base's `create_node`/`connect_nodes`/other node-editing tools. Do not re-lock with `editable=False`: it reverts to the saved definition and discards the edits.
2. Edit the internal nodes as needed.
3. `save_hda_contents(path, note, relock=True)` — bakes the instance's contents into the definition (`updateFromNode`) and, by default, re-locks the instance (`matchCurrentDefinition`). This only touches the **node graph**, not the parameter interface, and it does **not** touch the definition comment (the asset's description from `create_hda`) — `note` is just what you changed this time, returned in the result, not stored on the definition.

Do not call `reload_hda` between steps 1–3 — unsaved edits are discarded.

## Sections and callbacks

`hda_sections(target)` lists sections and returns the known event section names (PythonModule, OnCreated, OnLoaded, OnDeleted, OnInputChanged, OnUpdated, PreFirstCreate, Help); `get_hda_section` / `set_hda_section(name="PythonModule"|"OnCreated"|"Help", language=...)` read and write (omit `language` and `Help` is written as plain text, every other section as Python) (the result flags a `warning` when the name looks like a typo of a known event name); `remove_hda_section` deletes. Write script comments in English.

## Tab menu, input-count and metadata options

`set_hda_options(target, preferred=, hidden=, tab_submenu=, min_inputs=, max_inputs=, label=, icon=)` changes definition metadata **after** baking — no need to re-bake just to fix input counts, Tab-menu placement, the Tab-menu label or the icon. `hidden`/`tab_submenu` rewrite the whole `Tools.shelf` section; if the asset had a hand-authored shelf tool, back it up with `get_hda_section` first. `hidden=True` also calls `hou.NodeType.setHidden(True)` so the change applies to this session immediately (that part is session-only, like `ophide` — it does not survive a restart, the `Tools.shelf` rewrite is what persists). Its effect on the actual Tab menu still needs a live GUI check — hython can only confirm the XML was written and that `NodeType.hidden()` flipped.

## Validate

`validate_hda(target, parms, frame, inputs, test_input)` instantiates the asset in a temporary node, cooks it with the given parameters and deletes the temporary node. Run it after every interface, contents or section change. `ok` is the verdict: cooked (ROP/Driver assets skip the cook by design and can still pass), no errors, and no missing parameters (ramps and multiparm blocks count as their single count parameter).

For assets with `min_inputs > 0`, calling it with neither `inputs` nor `test_input` reliably fails with "Not enough sources" — that is expected, not a broken asset. Give `inputs=[node_path, ...]` to wire real scene nodes (SOP inputs from a different network are pulled in via a temporary Object Merge node automatically), or `test_input="box"`/`"grid"` for instant throwaway geometry on input 0 (SOP category only; it cannot be combined with `inputs`, so assets that need more inputs take `inputs`).

## Libraries and versions

- `install_hda`, `uninstall_hda(force=...)`, `reload_hda` (updates scene instances), `list_installed_hdas(pattern, category)`.
- `save_as_hda` copies a definition to another file, optionally with a new name or version (for version bumps).
- Git: `expand_hda(file_path, directory)` writes a directory for Git. By default it first re-saves the `.hda` uncompressed so the node graph is readable; the interface and scripts diff as text, the node graph still looks binary to Git. `collapse_hda(directory, file_path, install=True)` builds the `.hda` back.
