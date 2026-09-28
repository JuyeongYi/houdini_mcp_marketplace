---
name: kinefx-apex-rigging
description: Build, animate and check character rigs in Houdini with the houdini_mcp_rig tools - FBX character import and export, KineFX skeletons and poses, skin capture, weight analysis and repair, MotionClips, retargeting, APEX rig graphs (read, decompile, write via APEX Script) and rig validation. Use when importing or exporting an FBX character, creating or inspecting a skeleton, skinning a mesh, fixing weights or deformation problems, retargeting mocap, reading or writing APEX rigs, or validating a rig before export.
---

# KineFX and APEX rigging

This pack owns **KineFX animation end to end**: FBX character import, MotionClips, retargeting and FBX character export. The data is SOP skeletons, so it lives here. CHOP channels and channel analysis (`channel_stats` and friends) belong to the CHOP pack.

## Character in -> retarget -> character out

1. `import_character(fbx_file, comment, parent="/obj", name)` — places `kinefx::fbxcharacterimport` and one null per output: `<name>_rest_geometry` (skin with `boneCapture`), `<name>_capture_pose` (bind skeleton), `<name>_animated_pose` (animation, with `clipinfo`). Read the report: missing_outputs, weight summary, joint name mismatches, `clip.frame_range`, animated_joints. An animation-only FBX (mocap) yields only `animated_pose`; pass `animation_file` to combine a character with separate motion.
2. `validate_rig(skeleton=<capture_pose>, skin=<rest_geometry>)` before touching anything.
3. `retarget_skeleton(source=<mocap animated_pose>, target=<character capture_pose>, comment, mapping)` — builds `rigmatchpose -> mappoints -> fullbodyik -> null`. `mapping` is `{target joint: source joint}`; without it joints pair by name (ignoring namespaces and case). Different naming schemes need an explicit mapping — check unmapped_target.
4. `retarget_report(source, target=<retarget out>, frame_range)` — per-frame world-rotation error per mapped joint (degrees), root drift as a fraction of height, and foot sliding compared with the source. Fix the mapping for the worst_joints first.
5. `export_character_fbx(path=<rest_geometry>, capture_pose, animated_pose, file, comment, frame_range)` — ROP FBX Character Output, left in the scene under `name` (default fbx_character_out) and reused on later calls. Always pass `frame_range` for animation; take it from `clip.frame_range` and try 1-2 frames first. Without a range on an animated character the tool refuses instead of cooking the whole timeline. Apprentice licences cannot write FBX; the error says so.

## MotionClips

- `skeleton_to_motionclip(path, comment, frame_range)` — bakes an animated skeleton into a MotionClip. Without `frame_range` it uses the input `clipinfo`; with neither it asks for a range.
- `motionclip_info(path)` — samples, frame range, root travel, most-moving joints and how many joints never move (a quick "did the animation come through" check).

## Skeleton

1. `create_skeleton(parent, joints, comment)` — joints as `{name, position, parent}`; names must be unique and English.
2. `skeleton_info(path)` — hierarchy summary. `skeleton_info(path, attributes=True)` adds each point attribute with its KineFX role and sample values. `list_joints(pattern)`, `joint_info(joint)` for details.
3. `pose_joints(path, poses, comment, space="local")` — one `kinefx::rigpose`, joints picked by name, descendants follow. `space="world"` rotates about world axes (values are baked from the current pose; re-run if upstream changes).
4. `compare_poses(path, reference, mapping)` — how far paired joints moved in one frame; pass `mapping` when names differ. For motion across frames use `retarget_report`.

## Skin

1. `capture_skin(mesh, skeleton, comment, method="proximity"|"biharmonic", max_influences, normalize=True)` — the skeleton must be in the bind pose.
2. `weight_stats(path)` — distribution, influences per point, top joints.
3. `find_unweighted_points(path)` — points that will stay behind when deforming.
4. `joint_influence(path, joint)` — which points a joint pulls.
5. `fix_weights(path, comment, normalize, prune_below, max_influences, smooth_iterations)` — repairs weights without recapturing (neighbour smoothing loop, then `capturecorrect`) and returns before/after summaries. Map validator findings to arguments: weight_sum_not_one -> `normalize`, negative_weights -> `prune_below=0`, excess_influences -> `max_influences=4`, small unweighted_points patches -> `smooth_iterations=3`. Large holes: recapture.
6. `deform_skin(rest, capture_pose, animated_pose, comment)` — deforms and measures whether the mesh really moved.

## APEX graphs

- `apex_graph_info(path)` — structure, callbacks, ports, errors. `nodes=True` (with `pattern`, `parms`) lists nodes.
- `apex_rig_script(path)` — decompiles the graph into APEX Script code; read it to understand an existing rig.
- `apex_script_apply(path, code, comment)` — writes APEX Script into an `apex::script` SOP (creates one after a SOP or inside a geo network), compiles, and returns `errors`, error_lines (1-based lines of your code) and the compiled graph summary. Loop: decompile -> edit -> apply -> fix the reported lines.
- `apex_callbacks(pattern, kind="callback")` / `apex_callbacks(pattern, kind="subgraph")` — callbacks, or subgraphs such as rig components (`component::FKIK`, `component::FBIK`). `apex_callback_info(name)` gives exact signatures for either. Look them up; do not guess port names.
- `build_fk_rig(skeleton, comment)` — wrapper around `apex::buildfkgraph`: FK rig graph from a skeleton with a `transform` attribute.

## Validate

`validate_rig(skeleton, skin, max_influences=4)` checks hierarchy, names, joint orientation, weight sums and bind pose in one pass, with a fix for every finding (most point at `fix_weights`). Run it after import, after weight fixes, and before exporting (game engines usually allow 4 influences).
