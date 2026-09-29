---
name: materialx-lookdev
description: "Create and debug MaterialX (and Karma/USD Preview) materials with the houdini_mcp_mat tools - shader graphs, textures (including normal and displacement maps), color spaces and material assignment."
when_to_use: "Use when building or fixing materials, attaching textures, when renders show wrong colors, flat grey or missing bump/displacement, or when an assignment does not seem to apply."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_mat tool pack loaded."
---

# MaterialX look development

> These tools are in the `mat` package, which is not loaded by default. If they are not in your tool list, call `load_package("mat")` first (`get_entries` shows every package).

## Build

1. `create_material(parent, name, comment, kind="materialx")` — comes with the MaterialX standard surface on the surface output and `mtlxdisplacement` on the displacement output. `kind` is one of `materialx` (default, saves to `.mtlx`), `karma`, `usdpreview`, `principled` (legacy Mantra).
2. Add nodes with base `create_node`, connect them with base `connect_nodes` using **port names** (`input_index="base_color"`, `output_index="out"`) — it checks the VOP data types — and break a link with base `disconnect_input`.
3. Set shader values with base `set_parms` — colors and vectors go in as lists, e.g. `{"base_color": [0.4, 0.25, 0.1], "specular_roughness": 0.55}`. A value on an input that has a connection is ignored at render time; disconnect first.
4. Before connecting, read the node's `ports` from base `node_info(path)` — exact input/output names, types and what is already connected (base `node_type_info` gives the same ports for a type you have not created yet). To see the whole shader graph with port names, use base `network_graph(path)` on the material; `material_info` adds textures and assignments.

## MaterialX node pitfalls

- Many MaterialX nodes have a **signature menu** that decides their types. The menu is dynamic; set it by token (for example `default` for float, `color3`, `vector2`, `color3FA`, `vector2FA`), then the inputs change to match.
- Math nodes name inputs `in1`, `in2` (multiply's second input is `in2`), not `a`/`b`.
- `validate_material` runs the MaterialX library's own validation. Run it after wiring.

## Textures

`assign_texture(material, to_input, file, comment, usage=..., output=...)` opens the file before it creates anything (missing file → no node), checks it against `usage`, and wires it the MaterialX way:

| Map | Call | Wiring it builds |
|---|---|---|
| Base color | `to_input="base_color", usage="color"` | `mtlximage` (color3) → surface input |
| Roughness / metalness / masks | `to_input="specular_roughness", usage="scalar"` | `mtlximage` (float) → surface input |
| Tangent-space normal map | `to_input="normal", usage="normal"` (or coat_normal) | `mtlximage` (vector3) → **`mtlxnormalmap`** → surface `normal` |
| Height / displacement | `to_input="displacement", usage="scalar", output="displacement"` | `mtlximage` (float) → **`mtlxdisplacement`** (rebuilt if it was deleted) |

- Never plug a normal map straight into `normal`; `usage="normal"` inserts the normalmap node for you (reported in `inserted`). A one-channel bump map is not a normal map — attach it as `scalar` and put `mtlxbump` in between.
- Displacement must go to the displacement output, not the surface shader. Tune amount with the `scale` parameter of `mtlxdisplacement` (`set_parms`).
- To inspect an image file on its own (resolution, channels, UDIM tiles, pixel statistics, usage check) use the render pack's `image_info(path, usage=...)`.
- After changing files on disk, `reload_textures`.

## Color spaces

- Color maps are sRGB; **data maps (roughness, height, normal, masks) must be `Raw`/linear**.
- `list_color_spaces()` reads the OCIO config (names, aliases, roles, displays) and returns parm_menu — the values the texture parameter actually accepts (aliases like srgb_texture, not display names). Pass `path=<texture node>` to see that node's menu and current value.
- `set_color_space(path, colorspace)` refuses values that are not in the menu.

## Assignment

- `assign_material(target, material, comment)` works on SOP, OBJ and LOP targets; for a LOP target the material must live in a `materiallibrary` LOP (or pass its USD prim path, e.g. `/materials/wall_stone`). On SOP/LOP it **inserts** the assign node right after `target` and rewires whatever was downstream (`rewired`), then verifies on the network's display node (reported as verified_at).
- `verified=false` with a hint that "a downstream node removed/overrode it" means something after the target (attribute delete, another assign) wins. Fix that node rather than assigning again.
- LOP: give a prim pattern (`prim_pattern="/wall_cube"`); the default `%type:Mesh` does not match `Cube`/`Sphere` gprims.
- `list_assignments(path)` reads the result (SOP attribute / USD binding), not parameters.
- **Colors from geometry**: when a SOP is imported into USD, a point `Cd` attribute overrides a primitive `Cd` for `displayColor`. If per-piece colors disappear, delete the point `Cd`.

## Presets

`save_material` writes a `.mtlx` (direct write — there is no `.mtlx` ROP) and reads it back; `load_material` rebuilds a material from one; `list_material_presets` scans a directory of `.mtlx` documents (not node parameter presets — those are base `list_node_presets`).

## Verify

A material is only right when it renders right: check with a viewport snapshot in a render delegate (`set_viewport_renderer`) or a small render (render pack).
