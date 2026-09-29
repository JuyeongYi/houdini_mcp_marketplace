---
name: groom-inspection
description: Inspect Houdini grooms and hair cards with the houdini_mcp_groom tools - strand counts, length and width distributions and bad strands, Guides/Skin/Skin VDB stream wiring along a groom chain, and how well a hair card mesh covers the source strands. Use when building or debugging a groom (Guide Groom, Guide Process, Hair Clump, Hair Gen), checking guides or hair before card generation, or comparing hair card results (Hair Card Generate, a hair card HDA, hand-made cards).
---

# Groom inspection

> These tools are in the `groom` package, which is not loaded by default. If they are not in your tool list, call `load_package("groom")` first (`get_entries` shows every package).

The groom pack only measures. It builds nothing and leaves no nodes in the scene; the math runs in VEX on a copy of the geometry. Build and rewire with the base tools (`create_node`, `set_parms`, `connect_nodes`), then measure again with these tools.

There are no per-step hair card tools. The hair card pipeline lives in an HDA: drive it through its parameters, then judge each stage's output with the tools below.

## Strands: `strand_stats`

`strand_stats(path, output, group, width_attribs)` summarises the curves a SOP outputs:

- curve count and non-curve prims mixed in (a skin mesh merged into the guides shows up here),
- length distribution and histogram, points per curve and whether every curve has the same count,
- width ranges for `width_attribs` (default width, pscale, thickness; point or prim),
- root bounding box,
- anomalies with prim numbers: zero-length strands, NaN/Inf positions, one-point strands.

Groom nodes have three outputs; `output` picks one (0 Guides, 1 Skin, 2 Skin VDB). Hair Gen's output 0 is the generated hair. Use `group` to look at a subset, for example the guides of one partition.

Check it before generating hair or cards: a hair card pipeline that resamples to a fixed count expects uniform points per curve and no zero-length strands.

## Chain wiring: `groom_chain_info`

Groom nodes carry three streams, Guides / Skin / Skin VDB, on inputs and outputs 0/1/2. The rule: **pass all three down the chain, output k to input k of the next groom node. Never re-feed Skin or Skin VDB from the original source or from a groom node further up.** Re-feeding silently drops whatever the nodes in between did to the skin or VDB. Plain nodes (wrangle, null) between groom nodes are fine; the check follows their first input.

`groom_chain_info(path)` accepts a groom node (checks it and everything upstream) or the network that holds the groom (checks every groom node inside). Streams are recognised by input/output labels, so Hair Gen (Rest Skin on input 0, Guides on input 1) and Guide Deform are checked by the same rule.

Each violation names the node, the input and a ready `connect_nodes` call with `output_index` and `input_index` filled in. Kinds:

- refed from source (error): the stream comes from the original geometry, not the chain,
- refed from upstream (error): it skips the nearest groom node and comes from an older one,
- crossed output (error): wrong output index, for example Skin plugged into Skin VDB,
- missing (warning): the upstream groom node provides the stream but the input is empty,
- foreign chain (warning): the stream comes from a different groom chain.

Run it after every wiring change and before handing a groom back.

## Hair cards: `card_fit_report`

`card_fit_report(cards_path, strands_path, tolerance, card_attrib, skin_path)` measures how well a card mesh covers the strands it replaces:

- distance from every strand sample to the nearest card surface (distribution),
- sample coverage and strand coverage within `tolerance` (default 1% of the strand bounding box diagonal; pass an explicit value when comparing runs),
- samples per card, cards that received no strands, the cards with the largest mean distance,
- with `skin_path`, cards whose front faces the skin (flipped winding; fix with a Reverse SOP).

A card is one connected piece of polygons unless you name an int prim attribute in `card_attrib`.

Compare card sets at the same card count and the same `tolerance`: Hair Card Generate as the baseline, then the HDA. Low coverage means too few cards or too little width margin; many unused cards means too many cards or cards floating away from the hair.

## Look at it

Numbers first, then eyes: capture the viewport with the base pack's viewport tools after the report says the result is plausible.
