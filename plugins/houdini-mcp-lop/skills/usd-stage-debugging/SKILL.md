---
name: usd-stage-debugging
description: "Inspect and edit USD stages in Solaris with the houdini_mcp_lop tools - composed prims, attribute values and where they come from, schemas, layers, references, variants, layout (transforms, activation, SOP import), cameras, lights and light linking."
when_to_use: "Use when geometry, materials or lights are missing or wrong on a LOP stage, when SOP data does not arrive in USD, when laying out or lighting a shot, or before rendering a stage."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_lop tool pack loaded."
---

# USD stages in Solaris

> These tools are in the `lop` package, which is not loaded by default. If they are not in your tool list, call `load_package("lop")` first (`get_entries` shows every package).

## Query the composed stage, not node parameters

These tools read the `pxr.Usd.Stage` a LOP node produces, after sublayers, references, payloads, variants and inherits have been applied. Node parameters can say one thing while the composed stage says another.

1. `stage_info(lop)` — prim counts by type, layers, up axis, time range.
2. `list_prims(lop, root, depth, limit)` / `find_prims(lop, pattern, traversal)` — always keep `limit`; stages are large. Patterns: `/world/**`, `%type:Mesh`, `%kind:component`. `traversal="all"` includes inactive prims.
3. `prim_info(lop, primpath)` — type, visibility, bounds, material binding, **variant sets with their choices and current selection**, and instance/prototype counts for a PointInstancer. For a light it adds a `light` section (intensity, exposure, color, shape, shaping, shadow, light/shadow links, world position and direction) keyed by USD attribute names.
4. `get_usd_attribute(lop, primpath, name, frame)` — the resolved value. `list_usd_attributes` lists names first.
5. **Wrong value?** `prim_origin(lop, primpath, attribute=...)` shows which layer and arc wins. `layer_contents(lop, identifier, primpath)` shows the USDA of that layer; `layer_stack(lop)` lists the layers and the LOP nodes that wrote them.

## Finding schema and attribute names

`usd_schema_info(query="Light")` lists prim types and API schemas; `usd_schema_info(name="SphereLight", property_query="shadow")` gives each property's USD type, fallback value and the encoded LOP parameter name (lop_parm). Use it before `set_usd_attribute` on an attribute the prim does not have yet — the USD type there is what `type_name` takes. Schema names (SphereLight) and type names (UsdLuxSphereLight) both work; `%type:` patterns use the type name.

LOP node parameters are USD names punycode-encoded (inputs:intensity becomes xn__inputsintensity_i0a), and each has a companion `_control` menu. When the control is `none` the value is not written to the stage — shadow and Karma light inputs default to `none`. The lop creation tools raise it to `set` for you and report what they changed.

## Editing

Every edit inserts a LOP node after the given node, with your English comment, and rewires downstream connections. Continue the chain from the node it returns. `import_sop`, `create_camera`, `create_light` and `create_light_rig` can start an empty LOP network (`/stage`) with a first node that has no input; the other edit tools need an existing stage.

- `set_usd_attribute(lop, primpath, comment, name=..., value=...)` or `values={...}` for several attributes of one prim in one node (one undo step). An attribute the prim does not have yet gets its type from the API schema that defines it, and that schema is applied (e.g. `inputs:shaping:cone:angle` applies ShapingAPI, `inputs:shadow:enable` ShadowAPI; the result lists the schemas it applied). A name only other prim types define is refused - check the name, or set it alone with `type_name`.
- `set_variant`, `add_reference` (`reference_type`: file, payload, prim, inherit, specialize), `add_sublayer`.

## Layout

- `import_sop(lop, sop_path, primpath, comment)` — SOP geometry lands under `primpath`; the result has type and point/polygon counts. It warns about loose points and Houdini volumes.
- `set_prim_transform(lop, primpath, comment, translate, rotate, scale, space)` — absolute placement; components you omit keep their current value. `space="world"` solves the local transform under the parent.
- `set_prim_active(lop, primpath, active, comment)` — deactivate (removes the prim and its children from the stage, reversibly) or reactivate. `primpath` accepts a pattern. For hiding only, set the `visibility` attribute to invisible instead.

## Cameras

`create_camera(lop, primpath, comment, frame_prims="/world/hero", resolution=[1920, 1080], focal=35, direction=[0, 0, 1])` frames the target bounds so they fill the narrower field of view. Without `direction` it uses a three-quarter view. The result gives the world position, field of view and framing distance. Connecting the camera to render settings is the render pack's job.

## Lights

- `create_light(lop, light_type, primpath, comment, intensity, exposure, color, translate, rotate, texture, properties)` — one UsdLux light. Name prims by role: /lights/key_light, not light1.
- Change an existing light (including lights from references) with `set_usd_attribute(..., values={"inputs:intensity": 2, "inputs:shaping:cone:angle": 30})`. The keys of `prim_info`'s `light` section can be passed straight back.
- `prim_info(lop, primpath)` / `list_lights(lop)` — read back what you set.
- `set_light_link(lop, light, comment, include, exclude, link)` — which geometry a light illuminates (`link="light"`) or which casts its shadows (`link="shadow"`). The result lists linked and unlinked geometry.
- `create_light_rig(lop, comment, target, camera)` — a verification rig: key, fill and rim distant lights placed relative to the camera's view of the target, plus an environment dome. Use it to see a look quickly; build final lighting light by light.

## SOP data that goes missing in USD

- **Loose points** (points without primitives) are skipped on import. Give them a particle system (for example an Add SOP creating points as a particle primitive) before importing.
- **Houdini volumes** do not import; convert to VDB first (`convertvdb`).
- **Pyro volumes** need a pyro shader (`kma_pyroshader`) inside a `collect` material node to render.
- Per-piece colors: a point `Cd` overrides primitive `Cd` for `displayColor` (see the materials skill).

Check the result with `prim_stats(lop, primpath, geometry_counts=True)` after import.

## Before rendering

`validate_stage(lop)` finds broken asset paths, empty prims, inactive prims and geometry without material bindings, and warns if there are no lights; each issue says which tool fixes it. The result's `next` field points to the render pack's `validate_render`, which checks camera, render settings and whether the stage actually renders — call that one before starting a render.
