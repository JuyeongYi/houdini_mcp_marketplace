---
name: pdg-cooking
description: "Cook Houdini TOP (PDG) networks and find out why work items failed with the houdini_mcp_top tools - generate, cook, dirty and cancel, in the foreground, asynchronously in the session or in a background hython, then status counts, failure causes grouped with commands, exit codes and log tails, per-item attributes and outputs, and scheduler slots."
when_to_use: "Use whenever you build or run a TOP network, a wedge or a batch of ROP fetches, or when work items fail, hang or cook slowly."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_top tool pack loaded."
---

# PDG cooking

> These tools are in the `top` package, which is not loaded by default. If they are not in your tool list, call `load_package("top")` first (`get_entries` shows every package).

TOP networks are built with the base pack (`create_node`, `connect_nodes`, `set_parms`) inside a topnet. Give every node a name that says what it does (for example render_frames or wedge_seeds), not genericgenerator1. This pack does what only PDG has: cooking and work items.

## Start small

1. Set the item count low (a few frames, a few wedges) for the first cook.
2. `cook_top(path, mode="generate")` — creates the work items without running them. Check the count and, with `work_item_info(<TOP node>, index=0)`, the attributes each item will get (a topnet path takes `id=` instead of `index`).
3. `cook_top(path, mode="cook")` — cook for real. The result carries per-node state counts; when anything failed its `next` points to `failed_work_items`.
4. Only then raise the count and cook the full batch.

`path` can be the topnet (cooks up to its display node) or one TOP node (cooks that node and what it depends on).

## Choosing how to cook

| Situation | Use |
|---|---|
| Small test, result needed now | `cook_top(path)` — blocking in the session |
| Longer cook, Houdini stays open, you want to dig into the items afterwards | `cook_top(path, wait=False)`, then poll `top_status(path)` until `cooking` is false |
| Long batch that must survive Houdini closing | `cook_top(path, background=True)`, then poll base `job_status(job=...)` |

- A blocking cook runs on Houdini's main thread. Past the main-thread time limit (120 s by default) later tool calls fail with `MainThreadTimeout`. Keep blocking cooks short.
- `background=True` cooks a snapshot of the current session in a separate hython. The user's .hip is not saved or overwritten (`$HIP` still resolves to the scene's directory); a scene that was never saved is refused, so call `save_scene` once before.
- A background cook does not fill this session's TOP graph. Poll it with base `job_status(job=...)` (progress, log tail, and the finished summary) and read failures with `failed_work_items(job=...)`. A background hython that dies without writing its summary (no license, crash) shows as `failed` or `exited` in `job_status`, and `failed_work_items(job=...)` returns its `error` and log tail; read the tail, fix, and cook again. For a job, `failed_work_items` keeps at most 20 cause groups and 20 log lines per example.
- Do not cook TOPs with `run_python` loops. Do not use base `cook_node` on TOP nodes; it does not cook work items.

## When items fail

1. `failed_work_items(path)` — failures grouped by cause. Each group has the cause line, how many items share it, their node and index, and one full example: command, exit code, log path and log tail. Fix the cause once, not per item.
2. If the failed count is 0 but nothing cooked, look at `node_errors`: an in-process Python Script TOP that raises removes its work items and leaves only a node error.
3. `work_item_info(path, index=...)` (or `id=...` from the failure report) — every attribute, output files, expected outputs, input files, dependencies and a longer log tail for one item.
4. After fixing, `cook_top(path, mode="dirty")` (add `remove_outputs=True` to delete files the items wrote) and cook again.

## Stopping and clearing

- `cook_top(path, mode="cancel")` stops a cook running in this session.
- Base `cancel_job(job=...)` ends a background cook, including the processes its work items started. `cook_top` has no `job` argument. If the process already died, nothing is killed and `cancelled` is false.
- `cook_top(path, mode="dirty")` on a topnet clears every node; on one node, only that node.

## Slow cooks

`list_schedulers(topnet)` — scheduler type, whether it is the default, key parameters, the slot count PDG computed (`slots`) and how many items are cooking or queued right now. The local scheduler defaults to a quarter of the CPU count; raise it with `set_parms` (maxprocsmenu to 1 and maxprocs to the count you want) when many items sit queued.

## Files written by work items

Work items that write caches, renders or exports should do it through ROP-based TOPs (ROP Fetch, ROP Geometry Output, USD Render) so the output path lives in the scene. Check the result files with `probe_file` (io package) or `image_info` (render package); base `geometry_stats` reads a SOP, so load a geometry cache into a File SOP first.
