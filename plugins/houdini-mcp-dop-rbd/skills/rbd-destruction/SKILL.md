---
name: rbd-destruction
description: "Set up and diagnose rigid-body destruction in Houdini with the houdini_mcp_dop_rbd tools - fractured or stacked pieces, glue constraints, density and mass, pinned foundations, and frame-by-frame simulation reports."
when_to_use: "Use when building an RBD destruction, when pieces fall apart at frame one, the whole structure slides, nothing breaks, or you need to know what moved and broke when."
compatibility: "Needs a GUI Houdini 22+ session running the HoudiniMCP server with the houdini_mcp_dop_rbd tool pack loaded."
---

# RBD destruction

> These tools are in the `dop_rbd` package, which is not loaded by default. If they are not in your tool list, call `load_package("dop_rbd")` first (`get_entries` shows every package).

This pack diagnoses dopnet-based RBD only. The SOP-level "RBD Bullet Solver"
node (`rbdbulletsolver`) hides its own dopnet inside itself, so these tools
cannot see into it and reject it outright. Build a dopnet with a Bullet RBD
Solver DOP inside it, and read pieces/constraints from the dopnet's own
output SOP or a DOP Import SOP.

## Check pieces before simulating

`rbd_piece_stats(path, constraints=..., constraints_output=1)` on the
fractured/assembled output:

- slivers (volume under `sliver_volume`, default 0.05 m³ - lower it for small bricks) that explode or jitter;
- estimated mass per piece (a point `density` on packed pieces, otherwise the `density` argument, default 1000 kg/m³);
- constraints per piece — pieces with zero constraints fall immediately.
  `constraints` should point to a stage that still has point `name` (piece
  linkage). RBD Constraint Properties keeps it on its Constraint Geometry
  output (index 1); `connectadjacentpieces` keeps it on output 0.

Fix the pieces before the simulation, not after.

## Wire RBD Constraint Properties correctly

`rbdconstraintproperties` takes the pieces (e.g. `assemble` output) on
**input 0** and the constraint-linkage geometry (e.g.
`connectadjacentpieces` output) on **input 1**. Read its **output 1**
("Constraint Geometry") — output 0 just passes the pieces through. With
default parameters (no UI painting needed) that output already carries
`s@constraint_name` ("Glue"/"Hard"/"Soft") plus the matching per-type
parameter attributes (glue: `strength`, propagate_rate; hard: `cfm`,
`erp`; soft: `stiffness`, `dampingratio`), and it still has point `name`
for per-piece connection counts.

## Check constraint types and strength

`rbd_constraint_stats(path, output=1)` on RBD Constraint Properties'
Constraint Geometry output (or `output=0` on `connectadjacentpieces` before
it has a type at all):

- breaks constraints down by their real type (the `s@constraint_name` prim
  attribute) — never assume everything is glue;
- reports each type's own parameter distribution (glue: strength; hard:
  cfm/erp; soft: stiffness/dampingratio) from whatever is actually on the
  geometry, with an inferred type (glue/hard/soft) per `s@constraint_name` value — the
  names can be renamed on RBD Constraint Properties (Glue/Hard/Soft
  Constraint Name parameters), so a "wall_hard" is recognised as hard from its
  cfm/erp;
- the top-level `strength` covers glue prims only (`strength_scope="glue"`),
  so merged glue + hard/soft geometry is not dragged down by the 0 that the
  merge gives non-glue prims;
- per-piece connection counts, when point `name` survives on that stage.

The `s@name` fallback (for hand-built setups that never reach
s@constraint_name) is unverified against `rbdconstraintsfromlines`/
`rbdconstraintsfromrules` — a default-parameter run of both produced no
name/constraint_name attribute at all in testing. The tool flags this
fallback in its result when used; treat its type breakdown with suspicion
until you have checked the geometry yourself.

## Structures built from pieces

- Stacked blocks (bricks) make believable collapses; each block is a piece. Mortar is glue between neighbouring pieces.
- **Pin the foundation**: set `active = 0` on the bottom row / ground-contact pieces, or the whole structure slides as one.
- Use a string attribute such as `part` (`wall`, `roof`, `tower`) on every piece so reports can be split by it.

## Density and mass pitfalls

- The solver ignores a `density` attribute on **unpacked** pieces. Packed fragments from RBD Configure honor it.
- RBD Configure moves `name` to **points**; merging its output with geometry that has primitive `name` gives a name class mismatch. Match the class before merging.
- RBD Pack packs the whole geometry/constraints/proxy triplet together, not individual pieces.

## Read the simulation

`rbd_sim_report(path, start, end, quiet_until=..., group_by="part", constraints=...)` with `path` on the dopnet SOP or a DOP Import of the pieces:

- per sampled frame (about 12 between `start` and `end`, or your `frames`, at most 50): how many pieces moved, maximum displacement (mean per `group_by` group), and — when `constraints` is given — remaining and broken constraints;
- `constraints` must be a **separate** SOP: the dopnet SOP and DOP Import have a single output, so constraints cannot come from another port of the pieces node. Add a second DOP Import next to the dopnet with Import Style = Fetch Geometry, Object Mask = the RBD object, Geometry Data Path = `ConstraintGeometry` (the Constraint Network DOP's data name) and pass its path (`constraints_output` is that node's port, default 0). Without it no broken counts or start-break warning are produced;
- `group_by` splits counts by the attribute: shows whether only the roof falls or the walls slide too;
- `quiet_until` flags anything that moved before the impact frame;
- `exclude="projectile*"` keeps the projectile out of the statistics (whole-name globs, space-separated).

Interpretation:

- Constraints broken but **nothing moved**: glue can break without motion; it is not a fragment problem.
- High mean displacement in a group with few broken constraints: the group moves as a block (unpinned foundation, or too strong glue).
- One point per piece is the fastest to read: a DOP Import SOP with Import Style = Create Points to Represent Objects (`pointsquicksetup`) on the RBD object, passed as `path`. That point is the pivot, which jumps from the bounding-box center to the center of mass on the first step, so rest positions are taken one frame after the start.

## Verify visually

`viewport_sequence` across the impact, and a `make_video` of the whole collapse for review.
