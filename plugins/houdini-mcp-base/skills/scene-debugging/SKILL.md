---
name: scene-debugging
description: "Find out why a Houdini scene is wrong, slow or broken using the base inspection tools - errors, cook order, expensive nodes, references in both directions, geometry over time, background jobs, snapshots and diffs."
when_to_use: "Use when a node errors or warns, output is empty or unexpected, cooking is slow, files are missing, a background render/cache did not finish, or you need to know what changed."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_base tool pack loaded."
---

# Scene debugging

Work from the symptom to the cause. Prefer reading tools; change nothing until the cause is known.

## Errors and wrong output

1. `find_error_nodes` — every node with errors or warnings among those that have cooked, up to 500 nodes (check `truncated`). The default root is the whole scene (`/obj`, `/out`, `/stage`, `/mat` ...); pass a narrower `root` on big scenes.
2. `node_errors` / `explain_node` on the first failing node upstream. `explain_node` combines type, the help summary, parameters that differ from defaults, inputs, errors and comment in one call. If `node_errors` shows `cooked: false`, run `cook_node` first.
3. `cook_chain` on the output node — what cooks, in what order, to produce it. The broken link is usually the first node whose output stops looking right.
4. `geometry_stats` / `list_attributes` / `list_groups` at each step to see where points, attributes or groups disappear. Use `output` for nodes with several outputs. Passing an OBJ path reads its display SOP.
5. `attrib_stats` for distributions and NaN counts; `group_members`, `prim_intrinsics` for what a group holds or what a packed prim carries.

## Things that change over time

- `geometry_over_time(path, frames=[...], attribs=["v"])` — point counts, bounding box, attribute ranges and NaN per frame, with flags for sudden jumps (explosions). It does not move the playhead.
- Any geometry tool takes `frame=` to read a single frame.

## Slow scenes

- `find_expensive_nodes` reports measured cook times. Fix the top entries first; nodes that never cooked have no time yet (`cook_node` them first).
- `cook_node(path, cook=False)` reads cook count, last cook time and whether a node is time dependent (recooks every frame) without cooking.

## Background jobs

- `job_status()` lists recent background jobs from any pack (ROP renders, caches, sims); `job_status(job)` gives state, progress, exit code, the last log lines and which expected outputs exist. On `failed`, read those log lines first. Jobs that write a result summary (TOP cooks) return it as `summary`. `cancel_job(job)` stops a background job from any pack (ROP, cache, `start_render`, background TOP cook) together with its child processes.

## What changed?

- `scene_snapshot(label)` before an experiment, `diff_scene(label)` after, to show the user what you changed or to find what they changed. It records node types, comments, inputs and non-default parameters under `/obj` (3 levels) by default - pass `root` for `/stage`, `/mat` or `/out`; flags are not compared.

## Dependencies and portability

- `node_references(path, direction="uses" | "used_by" | "both")` — what a node depends on and who depends on it, including Object Merge paths and `ch()` expressions. Check who uses a node (`direction="used_by"`) before deleting it.
- `list_dependencies(missing_only=True)` — external files that do not exist.
- `list_dependencies(check="portability")` — missing files, absolute paths and references outside `$HIP`, each with how to fix it. `remap_paths` and `collect_dependencies` default to `dry_run=True`; show the plan before applying.

## Cleaning up

- `delete_unused(parent)` defaults to `dry_run=True` and lists what it would remove. It keeps flagged outputs, their inputs, and anything referenced by Object Merge or expressions. It refuses networks without display/render flags (VOP, ROP, most LOP/DOP) — delete those by hand.

## Parameters

- `list_parms(path, changed_only=True)` — only non-default values, the fastest way to see what someone set. `names=[...]` reads specific values; `search="velocity"` finds parameters by label, folder or tooltip.
- `parm_info` shows the instance menu (dynamic menus included), whether the menu is strict, ramp keys, and a button's callback.
- `list_animated_parms`, `get_expression` — values driven by keys or expressions are not what `set_parms` changes (`set_parms` warns when it hits one).
