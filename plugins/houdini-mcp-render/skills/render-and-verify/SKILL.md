---
name: render-and-verify
description: Set up, run and verify Houdini Karma renders with the houdini_mcp_render tools - render settings and AOVs, pre-render validation, background renders through a USD Render ROP, progress via job_status, cancelling, and pixel-level checks of the results. Use whenever you configure, start, monitor or check a render, or when a render is black, missing frames, blocked or taking over Houdini.
---

# Render and verify

## Set up the render settings

1. `list_aov_sources(pattern=...)` — AOV names this Houdini install really has (Karma toggles and Extra Render Vars with their source names). Do not guess AOV names from memory.
2. `set_render_settings(lop, comment, camera=..., resolution=[w, h], samples=..., output="$HIP/render/<name>.$F4.exr", aovs=[...])`
   - On a `karmarendersettings` LOP it edits that node; on any other LOP it creates one after it.
   - `camera` is a USD prim path such as `/cameras/shot_cam`, not a node path.
   - It reads the stage back and reports `verified` / `mismatches`. Fix every mismatch before rendering.
3. `render_settings(path)` — what the stage will actually render (resolution, camera, products, AOVs).

## Before rendering

- `validate_render(path)` on the LOP or the USD Render ROP — missing camera, lights, geometry, materials, output path.
- The scene must have been saved once (`save_scene`). Background renders read a copy of the current state; the user's .hip is not overwritten.
- Do a small check render first: one or two frames, `samples_percent` around 25, or a low `resolution` override.

## Start the render

| Situation | Use |
|---|---|
| Any Karma render (LOP, USD Render ROP or .usd file), Houdini must stay usable | `start_render(target, comment, frame_range=[start, end])` |
| Other ROP types (geometry, Alembic, OpenGL...) or a short blocking run | `run_rop(path, frame_range, background=...)` (base pack) |

- `start_render` creates or reuses a USD Render ROP (`render_<lop name>`) in the scene and renders it in a separate hython process. Give `rop_name` a role-revealing name when you want to keep several.
- Always pass `frame_range`. Without it only the current frame is rendered; the tool clears the ROP's `$FSTART`/`$FEND` expressions itself.
- `renderer` must be a token from `list_renderers` (for example `BRAY_HdKarma`, `BRAY_HdKarmaXPU`).
- Do not press the ROP's "Render to Disk in Background" button and do not render with `run_python`; use the tools above.

## While rendering

- `job_status(job)` (base pack) — progress from `ALF_PROGRESS`, log tail, and whether the expected output files exist. Poll every few seconds, not in a tight loop.
- `cancel_job(job)` (base pack) — stops the hython process and its husk. Frames already written stay. This render pack has no cancel tool of its own; `cancel_job` cancels a background job from any pack by its id.

## Verify the output

- `image_info(path, frame)` — resolution, AOVs actually in the file, per-channel statistics; black, NaN, empty-alpha images are flagged in `diagnosis`. Use `stats=False` for a quick AOV list and compare it with `render_settings`.
- `image_sequence_report(path, start, end)` — missing frames, black frames, flicker across the sequence.
- `image_preview(path, exposure=...)` — look at a frame.
- `compare_images(a, b)` — confirm a fix actually changed pixels.
- For review, turn the sequence into a video with `make_video` (base pack) and send or point the user to it.

`image_info(path, usage="color"|"scalar"|"normal")` also checks textures (channel count, bit depth, colour space) and counts `<UDIM>` tiles.

Apprentice/Education licenses watermark renders. Do not try to remove or work around the watermark.
