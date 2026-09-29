---
name: channel-analysis
description: "Analyse, filter, transfer and bake animation channels in Houdini with the houdini_mcp_chop tools - channel statistics (including loop and spike detection), filters with before/after comparison, CHOP to keyframes, channel files and audio waveforms."
when_to_use: "Use when checking whether an animation loops, finding pops or jitter, smoothing motion, baking expressions or CHOPs to keys, or driving animation from audio. Not for KineFX skeleton animation (MotionClip, retargeting, character FBX) - that is houdini-mcp-rig's kinefx-apex-rigging skill."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_chop tool pack loaded."
---

# Channel analysis

> These tools are in the `chop` package, which is not loaded by default. If they are not in your tool list, call `load_package("chop")` first (`get_entries` shows every package).

Treat channels as data to be judged, not lists of numbers to read. Setting a single key or expression is the base pack's `anim` tools; this pack is for analysis and bulk transfer of **scalar CHOP channels** only.

**Boundary with rig**: KineFX skeleton animation - MotionClip creation/evaluation, retargeting, character FBX import/export - belongs entirely to `houdini-mcp-rig` (its `kinefx-apex-rigging` skill). This pack never touches MotionClips or skeletons; it only analyses `hou.Track` scalar channels. The one overlap: once rig has pulled a skeleton channel out as a CHOP, analyse it here with `channel_stats`.

## Look at channels

- `list_channels(path)` — names, sample counts, value ranges.
- `channel_stats(path, channels, sections)` — the main analysis: ranges, total change and path length, stillness, loop check, spikes and a sparkline per channel. Pass `sections=["loop"]` for a loop-only verdict (with a top-level failing-channels summary) or `sections=["spikes"]` for spike-only (with a total-spikes summary) instead of the full report.
- `channel_samples(path, channel, start_frame, end_frame, max_points)` — actual values over a window when you need them.

## Change

- CHOP networks and nodes are made with the base pack's `create_node`. Use `create_node(parent, node_type="chopnet", comment)` for the network, then `create_node(parent=<chopnet path>, node_type=<chop type>, comment, parms, inputs, report=True)` for each CHOP - `report=True` gives a channel summary just like this pack's tools do.
- `apply_chop_filter(path, filter, comment, strength)` — `lag` (lag1/lag2, seconds), `smooth` (width, frames), `limit` (no strength - use `parms={"min":..., "max":...}`), `shift` (scroll), `resample` (rate), `spring` (springk), `jiggle` (stiff). Returns before/after statistics (`comparison`) and the parameters actually set (`settings`) so you can see whether the spike or jitter is gone.

## Transfer

- `import_from_parms(parent, parms, comment)` — animated parameters into a Channel CHOP.
- `set_chop_export(path, enable)` — drive parameters live from the CHOP.
- `export_to_keyframes(path, targets)` — bake CHOP channels to keys and verify the values match.
- `bake_channels(parms, start_frame, end_frame, step)` — bake expressions on parameters to keys and verify.

## Files and audio

- `export_channels(path, file_path, start_frame, end_frame, step)` — Houdini clip files (`.clip`, `.bclip`, `.bclip.sc`) via a channel ROP under `/out` (reused across calls on the same CHOP, so it doesn't pile up nodes). The optional frame range is recorded on the ROP for later re-runs, but **does not crop the exported channel** (verified on Houdini 22.0.368 - the ROP writes the CHOP's full evaluated track regardless). To actually trim what gets exported, put a Trim CHOP in front (base `create_node`) and export that node instead.
- `import_channels(parent, file_path, comment, envelope_points, set_audio_flag)` — read `.clip`/`.bclip`/`.chan`/`.bchan` back into a File CHOP. For audio (`.wav`/`.aif`/`.aiff`, verified) it also analyses the waveform - peak/RMS/clipped samples and an envelope per channel - instead of just making the node; `set_audio_flag=True` makes it the scene audio (only valid for audio files).
- `export_parm_channels` / `import_parm_channels` — `.chan` / `.bchan` for other DCCs (column order = parameter order). These write with hscript `chwrite`/`chread` directly because the channel ROP cannot write `.chan` - the one exception to the ROP rule.
