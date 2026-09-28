---
name: visual-review
description: Check Houdini results visually - viewport snapshots, multi-frame sheets, free-orbit views, display overlays (point numbers, normals, backfaces), deliverable videos rendered through an OpenGL ROP, and A/B comparison videos. Use after building or changing geometry, simulations or materials, when the user asks to see a result, or to compare before/after versions of a fix.
---

# Visual review

## Make sure you capture the right thing

Captures show exactly what the viewport shows. Before capturing:

- Check which node has the display flag (`node_info` → `flags`, or `network_graph`). A user's node may be displayed instead of yours, or a DOP object may be displaying the raw simulation.
- Do not move the user's display flag without asking. If you move one temporarily, restore it.
- Read `viewport_info` first and keep its `view`; pass it back to `set_view` when you are done so the user gets their view back.
- Frame the view:
  - `set_view(azimuth, elevation, distance, target)` — free orbit around a node or point (for example a 3/4 view from above), without creating a camera node.
  - `frame_node(path)` (SOP or OBJ) to fit one node, `frame_node()` with no path to fit the whole scene.
  - `set_viewport_direction` for orthographic top/front/side.
  - `set_viewport_camera` to see what a render camera sees. It takes an OBJ camera, or a USD camera prim path when the viewer shows a LOP stage; if the path is not a camera, the error lists the scene's cameras.
- Overlays for checking topology: `set_viewport_display(point_numbers=True, prim_normals=True, backfaces=True, ...)`. Turn them off again after the capture.

## Still images (for you to look at)

- `viewport_snapshot` — one frame, returned as an image.
- `viewport_sequence` — up to 16 frames on one sheet with frame numbers. Use it for anything that changes over time (simulations, loops). Later frames of an uncached simulation take long on first capture.

These are review captures only (temporary files). They are not deliverables.

## Videos (needs `FFMPEG_BIN_PATH`)

`scene_info` → `video` tells you in advance whether the video tools can run. If `FFMPEG_BIN_PATH` (bin directory with ffmpeg and ffprobe) is not set in Houdini's environment, tell the user to set it and restart Houdini.

- **Deliverable video = ROP.** `make_video` without `source` creates (or reuses) an OpenGL ROP `/out/<name>_flipbook`, renders `start`–`end` through `camera` to `$HIP/flip/<name>.$F4.jpg`, then encodes. The ROP stays in the scene so the user can re-render the same frames. Give `camera` explicitly unless the viewport is already looking through a camera.
- Up to 200 frames render in the foreground. For longer ranges: `run_rop(<the OpenGL ROP>, frame_range=[...], background=True)`, follow it with `job_status(job)`, then `make_video(source="$HIP/flip/<name>.$F4.jpg")`.
- `make_video` with `source` encodes an existing image sequence (`$F4`, `%04d`) or relabels a video file. Missing frames are filled with the previous frame and reported. Linear EXR/HDR get `exposure` and an sRGB transform.
- `compare_videos` — two sources side by side (`layout="horizontal"`) or stacked (`"vertical"`), each with its own label. The shorter one holds its last frame.
- If a source video already has a label baked in by `make_video`, pass `label_a=None` / `label_b=None` for it, or the labels overlap.
- Both tools read the result back with ffprobe; check `frames`, `width`, `height` and `warnings` in the response.
- The user cannot see files you write unless you tell them the path (or send the file).

## When a picture is not enough

Pair images with numbers: `geometry_stats`, `attrib_stats`, `list_groups`, and `geometry_over_time(path, frames)` for anything animated (point counts, bounding box, NaN per frame). All geometry tools take `frame=` and do not move the user's playhead. A picture can hide a flipped normal or an empty group; numbers can hide a wrong look.
