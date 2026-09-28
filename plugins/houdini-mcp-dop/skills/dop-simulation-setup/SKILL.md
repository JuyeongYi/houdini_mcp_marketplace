---
name: dop-simulation-setup
description: Build, test, cache and debug Houdini simulations as DOP networks with the houdini_mcp_dop tools - recipes per object type, objects, solvers, sources, forces, fields, low-resolution test runs, stepping, .sim caches through a Dynamics ROP and setup validation. Use when setting up any simulation (rigid bodies, pyro/smoke, FLIP, Vellum cloth, particles), when a simulation explodes, is empty or behaves unexpectedly, or when caching a simulation.
---

# DOP simulations

## Build the DOP network directly

Set simulations up as an explicit DOP network (dopnet → objects → solver → sources → forces), not as SOP-level solver shortcuts (Pyro/Vellum/FLIP/RBD Bullet Solver SOPs). The tools only work on dopnets, and every object, source and force stays visible and inspectable.

1. `dop_recipes(object_type)` — before adding anything: which solver pairs with the object type, which parameter takes the source SOP, which source node and solver input feed it, and how the result is read back. `exists` tells whether the type exists in this Houdini build.
2. `create_dopnet(parent, name, comment, gravity, substeps)` — gravity, solver merge and output come wired.
3. `add_dop_object(dopnet, object_type, comment, source_object)` — creates the object, picks and wires the solver, and creates the read-back SOP (DOP Import fetch for geometry, DOP Import Fields for smoke/pyro containers). Read what it returns: every node it created, parameters set and next steps.
4. `add_sim_source(dopnet, source_sop, target_object, comment)` — for pyro, FLIP, POP and continuous Vellum emission: creates the source node and wires it into the solver's sourcing input by label.
5. `add_dop_force(dopnet, force_type, comment, parms)` — DOP forces (gravity, drag, windforce) go after the solvers; POP forces (popforce, popwind, popdrag) and gas microsolvers are routed into the right solver input (`target_solver` when there are several). Vectors take a list (`{"wind": [3, 0, 0]}`) or component names; a wrong name returns the closest ones.
6. `validate_simulation(dopnet)` before running — it also checks object/solver pairs, missing sources and read-back nodes.

## Assembly order per simulation type

- **Rigid bodies**: `add_dop_object(..., "rbdobject", source_object=...)`, then a collider with `object_type="staticobject"`.
- **Pyro / smoke**: build the SOP source (pyrosource in Volume Scatter mode with density, temperature and v → volumerasterizeattributes). `add_dop_object(..., "smokeobject_sparse")` (auto-resizing; the dense smokeobject also works) with no source object, then `add_sim_source(dopnet, "<rasterize SOP>", "<container>")`. The default mapping adds density, temperature and v → vel; change it with `fields_map` and `op` (add, max, copy ...).
- **FLIP**: put a flipsource SOP on display in the source object, `add_dop_object(..., "flipobject", source_object=..., parms={"particlesep": ...})`. To keep emitting, `add_sim_source` with the flipsource SOP (surface, min). The shelf name flipfluidobject does not exist as a DOP type.
- **Vellum**: see [vellum-cloth.md](vellum-cloth.md). `add_dop_object(..., "vellumobject", source_object=..., constraints_sop=...)`.
- **Particles**: `add_dop_object(..., "popobject")`, then `add_sim_source(dopnet, "<emitting SOP>", "<object>", parms={"emittype": "surface"})`, then POP forces with `add_dop_force`.

## Run cheaply first

- `test_simulation(dopnet, start, end, resolution_factor)` — low-resolution run with a per-frame report (divergence, idle objects, element and field trends). SOP-side resolution parameters (for example the flipsource `particlesep`) go in `extra_parms` so they are lowered together. If nothing could be lowered the verdict says it ran at full resolution.
- `step_simulation(dopnet, frames)` — advance from the current frame and see each frame's state.
- `reset_simulation(dopnet, cook_first_frame=True)` — discard the cache and check the initial state.
- Look at motion with `viewport_sequence` over several frames, not a single snapshot. Make sure the viewport displays the read-back node, not the raw DOP object.

## Inspect

`list_dop_objects`, `dop_object_info` (`group_subdata=True` splits fields / containers / other and gives the creator node's comment), `dop_relationships`, `simulation_info` (solver input labels, nodes not connected to the output), `list_dop_fields`, `field_stats(deep=True)` for NaNs, `sim_memory`.

## Cache

`write_sim_cache(dopnet, directory, start, end, comment)` bakes `.sim` files through a Dynamics ROP in `/out` (one file per frame, kept in the scene so it can be re-run). In the foreground it returns a per-frame report; bake one or two frames first. Long ranges: `background=True` (the scene must have been saved once) and follow the returned job with `job_status`. Then `load_sim_cache(dopnet, comment)` puts a File DOP in read mode at the end of the chain (`enable=False` solves again) — do not set the File DOP mode with `set_parms`. `sim_cache_status` compares memory and disk.
