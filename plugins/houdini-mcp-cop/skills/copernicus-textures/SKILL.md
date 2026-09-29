---
name: copernicus-textures
description: Build procedural textures in Houdini Copernicus (copnet) and check them as images and statistics with the houdini_mcp_cop tools, then export them correctly. Use when creating or editing COP networks, when a texture looks wrong in a render, when single-channel maps look black, or before exporting COP results to image files.
---

# Copernicus textures

> These tools are in the `cop` package, which is not loaded by default. If they are not in your tool list, call `load_package("cop")` first (`get_entries` shows every package).

Only Copernicus networks (`copnet`) are supported, not legacy COP2 (`cop2net`).

## Look at every step

A COP network's result is an image; you cannot judge it from parameters.

- `cop_preview(nodes, frame, tile_size, columns)` — one or more COP outputs as a contact sheet. Pick an output with `path:output` (name or index), e.g. `/img/tex/worley1:dist2`. Up to 16 tiles; use it to compare stages side by side.
  - Display adapts to the layer type: IDs get hash colors, data layers are stretched per channel (`normalize="auto"`), color layers are shown in sRGB. Use `normalize="off"` to see clipping in 0..1.
- `cop_layer_info(path)` — per output: resolution, channels, storage type, value ranges. A height map with min = max is flat; a mask stuck at 0 or 1 is clipped.

Preview after every change. Texture quality problems found only in the render cost a render cycle.

## Building

- Before wiring a node you don't know well, check the base tool `node_type_info(category="Cop", type_name=...)` — its `ports` field gives input/output connector names and data types (Mono/RGB/RGBA/UV/ID/Geometry/...). Connectors are typed; a wrong connection (e.g. `Geometry` into a `Mono` input) succeeds at wire time but only fails later as a cook error. `rop_image` (a `hou.RopNode`, not a real image COP) has no typed image ports, so its `ports` data types will be missing or `?` — see `validate_cop_network` below for how that's handled.
- Create nodes with the base `create_node` inside the copnet; connect with `connect_nodes` (use output indices for multi-output nodes).
- Noise node types are specific: `fractalnoise`, `worleynoise`, `cellularnoise`, `curlnoise`, `phasornoise`... there is no plain `noise` type. Use `list_node_types(category="Cop", pattern="*noise*")`.
- A `file` COP has **no output connectors even after its path is set and it has cooked**. Its outputs come from the `aovs` multiparm: set `filename`, then press the `addaovs` button (base `press_button`, or the equivalent parm call) — that fills the multiparm from the file's layers (a PNG gives one RGB output named `C`). Only then wire it or read it with `cop_preview`/`cop_layer_info`.
- Copernicus `wrangle` runs VEX on pixels; `opencl` runs OpenCL kernels.
- After wiring a network, run `validate_cop_network(path)` on the containing copnet. It reports cook errors/warnings, real type mismatches (via Houdini's own `isInputCompatible`, so Mono→RGB auto-conversion is not flagged), and unconnected inputs. An in-copnet `rop_image` and `output`/`input` nodes are included for errors/warnings but not type-checked; `nodes` lists every node it looked at.

## Exporting

- Use `export_cop_layers(cop_path, outputs, file_pattern, comment, frame_range=None)` (omit `frame_range` for the current frame only). It creates (or reuses) one `image` ROP per requested output, presses it, and re-reads the written file with OpenImageIO to confirm resolution/channels/stats — do not hand-build `create_node` + `set_parms` + `run_rop` for this.
  - `outputs` is a list of output names or numeric indices (check them with `cop_layer_info` or base `node_type_info(category="Cop", type_name=...)`'s `ports`).
  - `file_pattern` needs a `{output}` placeholder when exporting more than one output (each gets its own file — a single `image` ROP cannot fan multiple AOVs out to separate files, only to separate channels of one file), and a `$F4`-style frame token when `frame_range` spans more than one frame.
  - Color with `color="auto"` (the default) — know what it decides, because most procedural color layers (`constant`, `ramp`, ...) report `typeInfo` **`Raw`**, not `Color`:
    - `typeInfo` `Color` → OCIO-converted.
    - RGB/RGBA with `typeInfo` `Raw`, written to png/jpg/jpeg/tga/bmp → treated as color and converted (sRGB-looking file).
    - RGB/RGBA with `typeInfo` `Raw`, written to EXR or another linear format → raw, with a `color_warning` in the result. If it is an albedo/color map, re-export with `color="converted"`.
    - Mono/UV/ID and data `typeInfo`s (Normal/OffsetNormal/Position/SDF/...) → raw.
    - So: an RGB **data** map (e.g. a packed mask) going to PNG needs an explicit `color="raw"`; a color map going to EXR that should be display-encoded needs `color="converted"`. Check `color_reason` / `color_warning` in the result.
  - `resolution` must be two positive integers (max 16384), e.g. `[2048, 2048]`; omit it to use the network's resolution.
  - There is no `background` option on this tool — for a long batch, take the `rop` path it returns and run it with the base `run_rop(path=..., background=True)`. Background rendering needs a saved scene first (`save_scene`), same as any other ROP.
- The `/out` driver that `export_cop_layers` uses is type `image` (Driver category). `rop_image` is a different node: a ROP that lives **inside** a copnet (Cop category, a `hou.RopNode`) and has no typed image ports — base `node_type_info(category="Cop", type_name="rop_image")` gives its input name but no image `data_type` for it. If you ever fall back to raw `create_node`/`set_parms` for an `/out` COP export, use `image`.
- Apprentice/Education licenses watermark exported images. Do not try to remove or bypass the watermark (for example by writing layer buffers directly).
- `export_cop_layers` already re-reads and verifies its own output (resolution/channels/stats in `files[]`), so a separate check is usually unnecessary. If you need to inspect an exported file later, use render `image_info` (it replaced the old materials texture check), then attach with `assign_texture` using the right color space.
