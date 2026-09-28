# Vellum cloth in DOPs

Measured on Houdini 22.0 while building a looping flag simulation.

## Geometry

- Remesh the cloth to **uniform triangles** (`remesh_geometry` with a `target_size`); quads or uneven triangles wrinkle unevenly.
- Create the pin group on the points to hold (for a flag, the edge at the pole).

## Constraints (SOP side)

- Vellum Constraints: the **`group`** parameter selects the points to pin. `pingroup` is not the pin selection; setting it pins everything.
- Output the cloth geometry (first output) and the constraint geometry (second output) to two null nodes (OUT_cloth_geo, OUT_cloth_constraints). Put the display flag on the geometry null.

## DOP network

- `add_dop_object(dopnet, "vellumobject", comment, source_object="<cloth geo>", constraints_sop="<constraints null>")` — the Vellum object has no soppath; the tool sets `displaysoppath` (Initial Geometry) to the source object's display and `constraintsoppath` (Initial Constraints) to `constraints_sop`, wires it into input 0 of the Vellum solver and creates a DOP Import read-back.
- Wind: `add_dop_force(dopnet, "popwind", comment, parms={"wind": [3, 0, 0]})` — routed into **input 1** of the Vellum solver (Particle Forces). Its wind is the vector parm `wind`.
- Gravity stays after the solver in the chain (create_dopnet adds it).
- Continuous emission instead of a single initial state: `add_sim_source(dopnet, "<cloth geo null>", "<vellum object>", comment, constraints_sop=..., parms={"emittype": "continuous"})` adds a Vellum Source on the solver's Post-Solve input.
- `test_simulation` reports cloth motion from the geometry centre (a Vellum object's transform does not move).

## Seamless loop from a simulation

1. Pre-roll: start the simulation well before the loop range (for example frame -48) so the cloth settles.
2. Cache the simulation over the loop range plus the blend length (for example 60–210 for a 60–180 loop with a 30-frame blend) with `write_sim_cache`, then `load_sim_cache`.
3. Blend the tail back into the head with a weight that ramps over the blend window: `w = smoothstep(60, 90, F)`, `P = lerp(P(F + 120), P(F), w)`.
4. Blending positions shortens edges and creates crease buckling in the middle of the window. Correct it with iterative point operations weighted by `4 * w * (1 - w)` (zero at both ends, strongest in the middle):
   - edge-length relaxation toward rest lengths, then light Taubin smoothing;
   - run them as **point wrangles inside for-each feedback loops**, not detail wrangles.
5. Check the seam with `make_video` over the loop and `compare_videos` before/after the correction.
