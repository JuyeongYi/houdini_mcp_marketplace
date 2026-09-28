---
name: vex-wrangle-authoring
description: Write, compile-check and debug VEX wrangle code and OpenCL SOP kernels with the houdini_mcp_vex tools (vex_function_info, expression_function_info, validate_vex, create_wrangle, update_wrangle, diagnose_wrangle, diagnose_opencl). Use whenever you write VEX or VEXpression code for Houdini, when a wrangle or OpenCL SOP errors, or when iterative point operations (relaxation, smoothing) are needed.
---

# VEX wrangles and OpenCL kernels

## Find the function first, don't guess

- Know the exact name already? `vex_function_info(name=...)` gives the vcc
  signature plus a one-line summary and named usage examples pulled from the
  installed help (the named-usages field has real argument names; vcc's own
  signatures do not).
- Only know what you want to do? `vex_function_info(query=...)` (same tool,
  the other argument — this absorbed the old search-by-purpose tool) searches
  by purpose (e.g. `"closest point"`, `"curl noise"`) across the installed
  function help (name/summary/tags/group/argument names). Results where all
  your words match somewhere come first; results that match only some of the
  words are still included, ranked lower, so a query is not lost just because
  no single function's help contains every word.
- Need a **parameter expression** function (`ch()`, `centroid()`, `clamp()` —
  used inside a parameter's HScript expression, not inside wrangle code)?
  Use `expression_function_info(name=...)` or `expression_function_info(query=...)`.
  This is a different function set from VEX.

## Compile before you commit code to the scene

1. `validate_vex(code)` — compiles with Houdini's `vcc` without touching the
   scene and returns line/column diagnostics.
   - Wrangle snippets use the default `context="cvex"`. Do **not** pass
     `sop`; the snippet is wrapped as CVEX.
   - Use `attrib_types` for unprefixed attributes that are not float
     (`{"rest": "vector"}`).
   - Pass `input_path` (and optionally `run_over`) to also cross-check that
     every attribute the code reads exists on that input — this works even
     when the code fails to compile, since it's static analysis.
2. `create_wrangle` / `update_wrangle` compile again before writing, then set
   the code. Give the wrangle an English comment describing what it does.
   - `input_paths` connects up to 4 inputs in order. Read the 2nd+ input's
     attributes as `@opinput1_P` (index 1 = second input); `create_wrangle`'s
     cross-check follows those too.
   - `create_channel_parms` defaults to `True`: every ch-family call
     (`ch`/`chf`/`chi`/`chv`/`chu`/`chp`/`ch2`/`ch3`/`ch4`/`chs`/`chsop`/
     `chdict`/`chramp`) whose argument is a **valid parameter
     name** (letters/digits/underscore, no `/`) gets a matching spare
     parameter automatically (no more manual "Create Spare Parameters").
     A `ch()` argument that points at another node's parameter
     (`ch("../ctrl/amp")`) or that isn't a valid name at all
     (`ch("my amp")`) is never turned into a spare parameter — it's reported
     under `channel_parms.external_refs` instead, with `resolved: true/false`
     so you know whether the reference actually exists. The same split shows
     up on `create_wrangle`/`update_wrangle`/`diagnose_wrangle`'s top-level
     report: the local-and-missing field is fixable by re-running with
     `create_channel_parms=True`, while the unresolved-external-reference
     field (points elsewhere, or invalid) will not be fixed by that — a
     spare parameter on this node can't satisfy a reference to another one.
     Set initial values with `channel_values={"scale": 0.5}`. If a
     differently-typed parameter already exists under that name, it is
     reported under `channel_parms.conflicts` instead of being overwritten.
     Reading one name with differently shaped functions in the same snippet
     (`chf("k")` and `chv("k")`) creates nothing for it and is also reported
     under `conflicts` (with `functions`) — rename one of them.
     If a value's type doesn't match the parameter (e.g. a string for a
     vector parm), the node is still created/updated normally and the
     mismatch is reported under `channel_parms.invalid_values` (with the
     expected type and size) instead of raising.
3. `diagnose_wrangle(path)` — compile errors, cook errors, attribute problems
   (including opinputN) and missing channel parameters in one call.
   - When `cook=True` (default), the report also includes a per-attribute
     min/max/mean summary for every attribute the code writes.

## Type pitfalls that fail compilation

- `point()`, `prim()` and friends are overloaded by return type. Passing them
  straight into `len()`, `distance()` or `setpointattrib()` is ambiguous.
  Assign to a typed variable first:

  ```c
  vector p = point(0, "P", pt);
  float d = distance(p, v@P);
  ```
- `foreach` over an array literal does not compile; declare a typed array
  variable and loop over it.
- Declare array types explicitly (`int nbrs[] = neighbours(0, @ptnum);`).

## Iterative point operations

For relaxation, smoothing or any "repeat N times" point update:

- Use a **point wrangle inside a for-each feedback loop** (`block_begin` with
  feedback method, `block_end` with count iterations), not a detail wrangle
  that loops over all points itself. Point wrangles run in parallel and the
  loop keeps each iteration's result as the next input.
- Put the iteration count on the `block_end`, and keep per-iteration weights
  (for example a blend mask) as attributes computed once before the loop.
- There is no dedicated tool for wiring up the `block_begin`/`block_end` pair
  yet — create and connect them with the base pack's `create_node` /
  `connect_nodes` and set `blockpath`/`method`/`iterations` with `set_parms`.

## OpenCL SOP kernels

`diagnose_opencl(path, input_path=None)` cooks an `opencl` node and reports
compile errors, the `#bind` pragmas found in the kernel code, and the
Bindings multiparm. Two failure modes show up constantly and are called out
explicitly in the summary:

- **The Bindings multiparm's default empty entry.** A fresh `opencl` node
  starts with one empty binding (`bindings=1`, name `""`). If you author the
  kernel with `#bind` pragmas (`atbinding=1`) and don't clear it
  (`bindings=0`), the cook fails with `Binding named '' has invalid name.`
  even though the kernel code itself is correct.
- **`kernelname` must exactly match the kernel function's name** when using
  `usecode=1` + `atbinding=1`. A mismatch fails with
  `clCreateKernel (-46: CL_INVALID_KERNEL_NAME)`, not a helpful message from
  OpenCL itself — `diagnose_opencl` explains this one for you.

Pass `input_path` to also check that every `#bind point|prim|vertex|detail`
attribute name actually exists on that input, matched within that bind's own
class (a `#bind prim P` does not match a point attribute named `P`). This
applies to write binds (`&name`) too — OpenCL SOP only writes to an attribute
that already exists on the input; it does not create one for you. When a
write bind is missing, cooking actually fails with `Invalid attribute
'<name>'`, and `diagnose_opencl`'s summary leads with the specific
missing-attribute explanation rather than the raw error.

## Reading existing code

- `list_wrangles(root, contains="@Cd")` finds wrangles by content.
- `list_vex_contexts(context)` lists global variables available in a
  context.
