---
name: export-and-verify
description: "Export Houdini geometry and stages to disk through named ROPs and bring files in, verifying every file by reading it back, with the houdini_mcp_io tools - native geometry caches, USD, Alembic, FBX, glTF, file probing, FBX scene import and scene merging."
when_to_use: "Use when writing geometry or USD for another tool, DCC or game engine, importing external files, or when an exported file looks empty or wrong elsewhere."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_io tool pack loaded."
---

# Export and import with verification

> These tools are in the `io` package, which is not loaded by default. If they are not in your tool list, call `load_package("io")` first (`get_entries` shows every package).

Never trust that a write succeeded because it did not raise. Every export tool here writes through a ROP, then reopens the file with a reader for its format and compares counts.

## Pick the right tool

Start with `export_formats`: it says which tool writes which format, which ROP it uses, what this installation and license support, and which tool reads each format back in.

| Format | Tool | ROP left in the scene | Verified with |
|---|---|---|---|
| `.bgeo.sc`, `.bgeo`, `.geo`, `.obj`, `.ply`, `.stl`, `.vdb` | `write_geometry` | `/out` Geometry ROP | reloaded point/prim/attribute counts, per frame |
| `.usd`, `.usda`, `.usdc` | `export_usd` | `/stage` sopimport + USD ROP (or a USD ROP after your LOP) | reopened with `pxr` |
| `.abc` | `export_alembic` | `/out` Alembic ROP | point count from Houdini + `abcinfo` hierarchy |
| `.fbx` | `export_fbx` | `/out` Filmbox FBX ROP for an OBJ, an FBX output SOP ROP next to a SOP | file header only |
| `.gltf`, `.glb` | `export_gltf` | `/out` glTF ROP | glTF JSON: meshes, positions, triangle count |

- Every export tool requires `comment` (English): the ROP stays in the scene with that comment, so a person can rerun the same output later. Exporting the same node again reuses its ROP instead of piling up new ones.
- Do not write `.usd`, `.abc`, `.fbx` or `.gltf` through `write_geometry`: a geometry save accepts those extensions but writes ASCII `.geo` content. It refuses them and names the right tool.
- Do not write files with `run_python` (`saveToFile`, pxr `Export`). Disk output goes through these ROP tools.
- `export_usd(flatten=True)` writes a self-contained file; `False` keeps file references that break if the file moves. Keep `set_metadata=True` so `upAxis` and `metersPerUnit` are authored (a SOP source also gets `defaultPrim`; for a LOP stage pass `default_prim`); `run_usdchecker=True` for delivery. `.usdz` is not written by the USD ROP: write `.usd`, then package it.
- On an Apprentice license USD ROPs write `.usdnc` instead of `.usd` (the result carries a license note), and Alembic/FBX export is refused before any node is made. glTF works on every license.
- `export_fbx`: give an OBJ to export that subtree, a SOP to export only that SOP. `convert_units=True` converts meters to FBX centimeters; `axis` picks the axis system (`yupright`, `yupleft`, `zupright`, `currentup`). Binary is the default; `ascii_format=True` only for debugging.
- `export_gltf`: give a SOP to export only that SOP, or an OBJ to export that object and the objects parented under it. A subnet is accepted only when it has one root object: the Houdini glTF ROP writes just the last root-level object and drops the rest, so a multi-root subnet is refused. Export each object separately, parent them under one geometry object, or gather them with an Object Merge SOP and export that SOP. The verification also checks that the object's glTF node is present and that the scene lists a root node.
- KineFX characters (skeleton, skin, animation clips) are not exported or imported here: use the houdini_mcp_rig tools.

## Frames and long jobs

- `frame_range` is `[start, end]` or `[start, end, step]`; omit it for the current frame. It overrides the ROP's `$FSTART`/`$FEND` range. `write_geometry` needs a frame token (`$F4`) in the path for a range; Alembic, USD and FBX store time samples in one file.
- Try one or two frames first. Long ranges in the foreground hit the 120-second main-thread limit, and more than 500 frames is refused in the foreground.
- `background=True` snapshots the current session to a copy in the job directory (the user's .hip is not saved or overwritten), starts a separate hython on the same ROP and returns at once with `job` (its `job` field is the id for `job_status`) and no verification. Follow it with `job_status`, then `probe_file` on the output. It needs a scene that has been saved once.
- Existing files are not overwritten unless `overwrite=True`.

## Read the verification

Check `verified` and `verification.mismatches` against the source (`write_geometry` reports `all_verified` and a `verification` per file in `files`). A mismatch is reported, not raised: read it. `.obj`, `.ply`, `.stl` and `.vdb` are marked `lossy` because their counts legitimately change on a round trip. An empty file never passes.

## Import

- `probe_file(file_path, detail=True)`: look inside a file before bringing it in (layers for USD, hierarchy and point count for Alembic, meshes/skins/animations for glTF, header only for FBX). `$F4` and `<UDIM>` paths are counted.
- `import_geometry(parent, file_path, comment, name)`: creates the right reader SOP (Alembic, USD Import, glTF, or File), cooks it and returns what came in. It refuses `.fbx`, because the File SOP cannot read FBX. This is file -> SOP; putting a SOP from the scene onto a USD stage is houdini_mcp_lop `import_sop` (SOP -> stage).
- `import_fbx(file_path, comment, as_subnet=True, name)`: brings a scene FBX (cameras, lights, object hierarchy, animation) into one `/obj` subnet and counts what arrived. A character FBX goes to houdini_mcp_rig `import_character` instead.
- `import_scene(file_path, node_pattern)`: merges nodes from another `.hip`. `overwrite_on_conflict` replaces nodes at the same path and is hard to undo; ask first.

Scene-wide file references, collection and path remapping are base pack tools (`list_dependencies`, `collect_dependencies`, `remap_paths`). A File Cache node that stays in the SOP chain is base `write_cache`; DOP simulation caches are dop `write_sim_cache`.
