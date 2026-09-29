---
name: sop-procedural-modeling
description: Build and edit SOP geometry procedurally with the houdini_mcp_sop tools - primitives, curves, copy to points, bevel/extrude/boolean, remesh and triangulate, attributes, groups, for-each loops and UVs - checking measured results after each step and validating meshes with mesh_report. Use when modelling in SOPs, preparing geometry for simulation or export, or fixing topology, groups or UVs.
---

# Procedural SOP modelling

## Build in small measured steps

Every editing tool in this pack cooks the new node and returns before/after statistics. Read them after each call:

- Point/primitive counts that did not change mean the operation did not apply (wrong group, zero offset).
- A bounding box that jumped means a transform or pivot is wrong.
- `create_group` returns how many elements matched; zero means the pattern, bounding box or normal filter is wrong.

Name each node by role and give it an English `comment`. Chain nodes by passing the previous node's path as the next `path`.

Creating a node does **not** move the display flag by default (`display=False` on every SOP-creating tool). The node the user is looking at - typically a merge at the end of the network - stays displayed. Pass `display=True` on the node that should become visible (a final assembly, or a node you want to check in the viewport), or read results with `sop_report` / `geometry_stats` without moving the flag at all.

Assemble parts with `merge_sops(inputs, comment, name, display)`. It reports each input's counts and `attribute_mismatch`: attributes present on only some inputs, which Merge fills with defaults (a `Cd` on one input turns the others black). Fix those upstream before merging.

Fixed-choice arguments (`shape`, `group_type`, `operation`, `kind`, ...) are enums in the tool schema - pick from the listed values. Group types are singular everywhere in this pack: point / prim / edge / vertex / guess / breakpoint.

If a call fails, the pack deletes the nodes that call created and gives the display flag back to the previous node. Fix the arguments and call the same tool again - do not clean up by hand, and do not expect a half-built node to be left behind.

## Tool choice

| Goal | Tools |
|---|---|
| Base shapes | `create_primitive`, `create_curve`, `revolve_profile` |
| Instancing | `copy_to_points` (`pack=True` for many copies) |
| Assembly | `merge_sops` |
| Detail | `bevel`, `extrude_faces`, `bridge_edges`, `boolean_op` |
| Topology | `convert_geometry`, `triangulate`, `remesh_geometry`, `reduce_polygons`, `delete_geometry` |
| Placement | `transform_geometry` |
| Loops (for-each, repeat) | `create_loop_block` |
| Attributes | `create_attribute` (float / int / vector / vector4 / string), `add_normals`, `export_attribute` |
| Groups | `create_group` |
| UVs | `uv_project`, `auto_uv`, `uv_report` |
| Checking any SOP | `mesh_report`, `sop_report` |
| Queries | `nearest_point`, `nearest_prim`, `ray_intersect`, `volume_info` |

Moved to the base pack (context-free queries): `attrib_stats` (attribute distributions, with an `output` index for multi-output SOPs), `group_members`, `prim_intrinsics`.

Mirror, skin/loft and any other single-node SOP without a dedicated tool: use the base `create_node` with `report=True` - it cooks the node and returns the same before/after report. Wire extra inputs with `connect_nodes`, then check with `sop_report`.

## For-each and repeat loops

Never hand-wire `block_begin` / `block_end`. `create_loop_block` builds the begin/end pair, the metadata node and every `blockpath`, cooks the end node and reports the iteration count.

| `kind` | Use for |
|---|---|
| pieces | once per piece. Pieces are split by `piece_attrib` (defaults to prim `name` when present; otherwise each prim or point is a piece - add a connectivity node and pass `piece_attrib="class"` for connected pieces). `piece_class` chooses prim or point pieces |
| feedback | each iteration feeds the previous result back in (growth, repeated deformation). `iterations` defaults to 10 |
| count | the whole input `iterations` times, merged (numbered copies) |

The loop body starts empty. Build it by calling SOP tools with `path` set to the returned begin node, connect the last body node to input 0 of the end node with `connect_nodes`, pass `display=True` (or `set_flags`) if the end node should be displayed, then run `sop_report` on the end node. Read the iteration number in VEX with `detail("../<metadata node>", "iteration")`. For pieces, `iterations` caps the number of pieces while testing - turn the cap off afterwards as the tool's note says.

## Rules that save time

- **Simulation meshes**: cloth and soft bodies want evenly distributed triangles. Use `remesh_geometry` with a `target_size`, then run `mesh_report` before building constraints.
- **Bevel offsets** that are large relative to the geometry flip polygons. Start small and look.
- **Booleans**: `boolean_op` reports open edges on both inputs. If one is not closed, fill the holes (polyfill / fuse via `create_node`) and confirm with `mesh_report` that the open edge count is zero before calling `boolean_op` again.
- **Orient for copies**: `create_attribute` with `attrib_type="vector4"` makes a quaternion `orient` (identity when no value is given) that `copy_to_points` uses.
- **Per-element values**: `create_attribute` fills a constant. Values that differ per element belong in VEX - use `create_wrangle` from the VEX pack.
- **Large data**: never pull every point value into the conversation. Use the base `attrib_stats` for distributions, or `export_attribute` to write a `.npy` analysis dump. Asset output (bgeo, abc) goes through the base `write_cache` ROP, not `export_attribute`.
- **UVs**: run `uv_report` after `uv_project` / `auto_uv`; it reports the UV bounding box, out-of-range UVs, space occupancy and the island count. It does not measure island overlap - if overlap is suspected, re-layout with `auto_uv` (flatten).
- **Normals**: `add_normals` warns before overwriting existing `N`. Point `N` on a remeshed surface changes shading; check with a snapshot.

## Verify

For nodes this pack did not create (base `create_node`, hand-built or edited nodes), `sop_report` recooks the node and returns before/after against its first input (or `compare_to`), added/removed attributes and groups, and cook errors instead of throwing.

Before export, simulation or a boolean, run `mesh_report` on the output node. It reports open edges, non-manifold edges, faces whose winding disagrees with their neighbours, an inside-out closed mesh (negative volume), degenerate faces, duplicate points within `tolerance` and unused points - each with a note naming the node to fix it. Problem edges come as `p3-7` samples you can pass to `create_group`.

Finish with `geometry_stats` on the output node and a `viewport_snapshot`. For complex assemblies, `viewport_sequence` from several views (`set_viewport_direction`) catches flipped or hidden parts.
