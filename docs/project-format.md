# Project and placement format

All media paths in a project are resolved relative to its JSON file. Tool installation paths are command-line arguments, never hard-coded in the package.

```json
{
  "canvas": [720, 1280],
  "background": [214, 214, 214],
  "source_fps": 30,
  "output_fps": 60,
  "source_range": [36, 126],
  "max_transition_frames": 4,
  "keys": [
    {"frame": 36, "hold_until": 46, "file": "poses/pose_0036.png", "face_box": [285, 200, 385, 310]},
    {"frame": 47, "file": "poses/pose_0047.png", "face_box": [285, 200, 385, 310]},
    {"frame": 126, "file": "poses/pose_0126.png", "face_box": [285, 200, 385, 310]}
  ]
}
```

This is a schema example, not a complete choreography. Each PNG must already match the canvas dimensions and contain native RGBA. Keys cover the exclusive output end so the final transition has a destination; the destination frame itself need not be encoded. Source and output frame rates are separate. `[36,126)` at 30fps is 3 seconds and produces 180 frames at 60fps. Frame 36 with `hold_until:46` retains its original hold rather than slowly drifting for eleven source frames.

Optional source audio:

```json
{"audio": {"file": "source.mp4", "start_seconds": 1.2}}
```

Audio is re-encoded to AAC, not copied bit-for-bit. The supplied input must contain audio covering the entire requested interval. Use the video receipt plus an audio comparison before calling synchronization verified.

A grid mapping is used by `pose-mv ingest sheet.png mapping.json new-output-directory`:

```json
{
  "grid": [2, 3],
  "canvas": [720, 1280],
  "poses": [
    {"cell": 0, "frame": 36, "scale": 2.0, "anchor": [256, 80], "target": [350, 260]}
  ]
}
```

Cells are numbered left-to-right/top-to-bottom from zero. Anchor coordinates are local to the cell before any crop; target coordinates are in the output canvas. A single uniform scale and translation preserves the entire drawing's proportions. All supplied figures must be safely inside the sheet cell and the final canvas. Small disconnected alpha regions are not deleted automatically.

Generation provenance belongs in a separate project manifest: provider/tool, actual prompt, character-reference digest, pose-guide digest, returned asset digest, grid mapping, accepted/rejected decision, and review notes. Do not put account tokens or personal machine paths in public examples.
