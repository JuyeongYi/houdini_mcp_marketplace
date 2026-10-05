---
name: sop-procedural-modeling
description: "Build and edit SOP geometry procedurally - nodes from the base pack (create_network / create_node + set_parms), and the houdini_mcp_sop tools for what generic creation cannot do: merge and copy-to-points with input reports, for-each loops, attributes with explicit type info, and mesh/UV/SOP reports and geometric queries - checking measured results after each step."
when_to_use: "Use when modelling in SOPs, preparing geometry for simulation or export, or fixing topology, groups, attribute meaning or UVs."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server; the houdini_mcp_sop tool pack must be loaded for the sop tools."
---

# Procedural SOP modelling

> The tools named here without a package are in the `sop` package, which is not loaded by default. If they are not in your tool list, call `load_package("sop")` first (`get_entries` shows every package).

## Build with the base pack, check with this one

Ordinary SOPs (box, sphere, polybevel, polyextrude, boolean, remesh, divide, xform, blast, normal, groupcreate, uvflatten, uvlayout ...) have no tool of their own. Build them with the base pack:

- `create_network(parent, nodes=[...], report=True)` for three or more connected nodes - one atomic call; `dry_run=True` validates first; `box="..."` draws a titled network box around them.
- `create_node(..., report=True)` for one node, `set_parms` to change it (`batch=` for several nodes in one call).
- Look parameter names and menu tokens up with `node_type_info` before setting them; never guess.

`report=True` cooks the end nodes and returns point/prim counts and errors. Read them after each step:

- Counts that did not change mean the operation did not apply (wrong group, zero offset).
- A bounding box that jumped means a transform or pivot is wrong.

Name each node by role and give it an English `comment`. Creating a node does **not** move the display flag (`display=False` by default everywhere). Pass `display=True` on the node that should become visible, or read results without moving the flag.

Wrangle code goes through `create_wrangle` / `update_wrangle` (vex package) - the base tools refuse a `snippet`.

## What this pack adds

| Goal | Tools |
|---|---|
| Assembly | `merge_sops` - per-input counts and `attribute_mismatch` (an attribute on only some inputs is filled with defaults: a `Cd` on one input turns the others black) |
| Instancing | `copy_to_points` (`pack=True` for many copies) |
| Loops (for-each, repeat) | `create_loop_block` |
| Attributes with a meaning | `create_attributes` (constant values, several at once, each with class / data type / optional type info), `set_attrib_typeinfo` (fix the meaning of existing attributes) |
| Large data | `export_attribute` (`.npy` analysis dump) |
| Checking any SOP | `sop_report`, `mesh_report`, `uv_report` |
| Queries | `nearest_point`, `nearest_prim`, `ray_intersect`, `volume_info` |

Base pack measurements that work on any SOP: `geometry_stats`, `list_attributes` (shows type info), `attrib_stats` (distributions; `paths=[...]` compares nodes), `geometry_over_time`, and `measure_geometry` for anything else - a VEX snippet that computes your own metric on a copy of the geometry and returns statistics, without touching the scene.

If a call of this pack fails, the nodes it created are deleted and the display flag is given back. Fix the arguments and call the same tool again.

## Attribute type info

Type info is the meaning of an attribute - point, vector, normal, color, quaternion, matrix, texturecoord, hpoint, integer, integer-blend, indexpair or none. The Transform SOP and other nodes that move geometry rotate and scale attributes by it, and USD export writes the primvar role from it (normal3f, color3f, point3f, texCoord2f). VEX gives it only to well-known names (P, N, v, up, Cd, orient, uv); custom names such as `rest` or `dir` get none and are left behind by transforms.

- New attributes with constant values: one `create_attributes(path, comment, attributes=[...])` call, each entry `{"name", "class", "type", "typeinfo"?, "value"?}` - every element of the class gets the value. Types: float, int, string, vector2, vector, vector4, matrix3, matrix and arrays (float[], int[], string[], vector2[], vector[], vector4[]). For Copy to Points: `{"name": "pscale", "class": "point", "type": "float", "value": 0.2}`, `{"name": "orient", "class": "point", "type": "vector4", "typeinfo": "quaternion"}` (identity by default), `{"name": "up", "class": "point", "type": "vector", "typeinfo": "vector", "value": [0, 1, 0]}`. Without `typeinfo` Houdini's default applies (N, Cd, v, up, orient, uv get their meaning; other names none - the result notes vectors left without one). It is one detail wrangle with a `{ }` block per attribute, so it can also build matrices and typed ints.
- Values that differ per element: `create_wrangle` (vex package). Whoever creates an attribute sets its type info, so a wrangle that creates a position- or direction-like vector or matrix (rest, center, dir, aim, offset, restN, xform ...) sets it in its own code with `setattribtypeinfo()` - the tool refuses the code otherwise and gives the lines to add. Writing an attribute that already exists keeps its type info.
- Attributes made by other nodes: `set_attrib_typeinfo(path, {"rest": "point"}, comment)` wires one detail wrangle after `path` (and moves downstream wiring onto it).
- Check with `list_attributes` - `typeinfo` is listed for every attribute that has one.

## For-each and repeat loops

Never hand-wire `block_begin` / `block_end`. `create_loop_block` builds the begin/end pair, the metadata node and every `blockpath`, cooks the end node and reports the iteration count.

| `kind` | Use for |
|---|---|
| pieces | once per piece. Pieces are split by `piece_attrib` (defaults to prim `name` when present; otherwise each prim or point is a piece - add a connectivity node and pass `piece_attrib="class"` for connected pieces). `piece_class` chooses prim or point pieces |
| feedback | each iteration feeds the previous result back in (growth, repeated deformation). `iterations` defaults to 10 |
| count | the whole input `iterations` times, merged (numbered copies) |

The loop body starts empty. Build it with `create_network` / `create_node` whose first input is the returned begin node, connect the last body node to input 0 of the end node with `connect_nodes`, then run `sop_report` on the end node. To display the end node, pass `display=True` to `create_loop_block` itself (or use `set_flags` later). Read the iteration number in VEX with `detail("../<metadata node>", "iteration")`. For pieces, `iterations` caps the number of pieces while testing - turn the cap off afterwards as the tool's note says.

## Rules that save time

- **Simulation meshes**: cloth and soft bodies want evenly distributed triangles. Add a Remesh SOP (`node_type="remesh"`, target size), then run `mesh_report` before building constraints.
- **Bevel offsets** that are large relative to the geometry flip polygons. Start small and look.
- **Booleans**: a Boolean SOP on a mesh with open edges gives garbage. Run `mesh_report` on both inputs first; fill holes (polyfill / fuse) until the open edge count is zero.
- **Large data**: never pull every point value into the conversation. Use `attrib_stats` or `measure_geometry` for distributions, or `export_attribute` for a `.npy` analysis dump. Files for other tools go through the IO package (`write_geometry` for bgeo, `export_alembic` for abc) and a cache that stays in the SOP chain through base `write_cache` - not `export_attribute`.
- **UVs**: after UV nodes (uvproject, uvflatten + uvlayout, uvunwrap), `uv_report` gives bounding box, out-of-range UVs, space occupancy and island count. It does not measure island overlap - if overlap is suspected, re-layout.
- **Normals**: a Normal SOP replaces an existing `N`. Point `N` on a remeshed surface changes shading; check with a snapshot.

## Verify

`sop_report` recooks any SOP and returns before/after against its first input (or `compare_to`), added/removed attributes and groups, and cook errors instead of throwing.

Before export, simulation or a boolean, run `mesh_report` on the output node. It reports open edges, non-manifold edges, faces whose winding disagrees with their neighbours, an inside-out closed mesh (negative volume), degenerate faces, duplicate points within `tolerance` and unused points - each with a note naming the node to fix it. Problem edges come as `p3-7` samples you can use as a group pattern in a Group or Blast SOP.

Finish with `geometry_stats` on the output node and a `viewport_snapshot`. For complex assemblies, a `viewport_snapshot` from several views (`set_viewport_direction`) catches flipped or hidden parts.
