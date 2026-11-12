# 2D MV Lab

[한국어 안내](README.ko.md) · [Belimumab pilot: actual production steps](docs/belimumab-pilot.md)

Human-reviewed 2D dance animation from a fixed character design and explicitly timed pose drawings. Intended repository: `figurecurator/2d-mv-lab`. This is an experimental extraction of a production workflow, not an automatic character-video model.

The artist/agent generates and reviews drawings separately. This repository ingests transparent pose sheets, places each drawing using recorded anchors, preserves source holds, renders bounded motion with a separately installed RIFE implementation, and emits a frame-by-frame receipt. It does not require the historical v37–v82 project folders.

## What is implemented

- Native RGBA grid ingestion with explicit scale/anchor placement and clipping checks. Detached details are preserved rather than removed as small components.
- A frame-based timeline with explicit holds, a bounded transition window, and arbitrary source/output frame rates.
- Optional ComfyUI/RIFE adapter using one complete endpoint drawing at a time, bounded local flow, and a rigid translation in the face core to reduce facial stretching.
- FFmpeg output with optional source audio; full decode, frame count, strictly increasing decoded timestamps, input hashes, model hash, and a per-frame timeline receipt.
- Contact sheets and small synthetic fixtures for tests and installation verification.

The `hold` backend is an explicit diagnostic mode. It is not a motion-generation substitute. There is no silent fallback if RIFE is unavailable.

## Install and verify the core

Python 3.10+ and an FFmpeg executable are required. From this repository:

```sh
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/make_synthetic_project.py ./projects/synthetic
pose-mv check ./projects/synthetic/project.json
pose-mv render ./projects/synthetic/project.json ./renders/synthetic.mp4 --backend hold --ffmpeg ffmpeg
pose-mv contact ./renders/synthetic.mp4 ./renders/synthetic.jpg
```

## Render reviewed drawings with RIFE

Install ComfyUI and the dependencies required by its frame-interpolation loader separately. Use a Python environment that can import its PyTorch and safetensors dependencies. Supply an existing compatible RIFE checkpoint yourself. No download, account connection, model, or upstream implementation is bundled here.

```sh
pose-mv render ./projects/my-character/project.json ./renders/my-character-v01.mp4 \
  --backend rife --comfy-root /path/to/ComfyUI \
  --weights /path/to/rife_v4.26.safetensors --ffmpeg ffmpeg
```

On Windows PowerShell, write the command on one line or use PowerShell's continuation syntax. If the console script was installed into another Python environment, use `python -m pose_mv.cli` in the desired environment instead.

The adapter currently calls `FrameInterpolationModelLoader._detect_and_load`, `extract_features`, `warp`, and the model's feature-cache interface. These are upstream implementation details, not a stable ComfyUI service API. A future upstream change can require an adapter update. A mismatching API raises an error; it does not quietly select another interpolation method. GPU is the tested path. Explicit `--device cpu` exists but is not validated for performance.

## Character workflow

1. Pick one approved design, one face crop, one costume, and one line/color style. Keep the immutable reference and its digest in the private project record.
2. Inspect the source motion. Record support foot, lifted foot, pelvis tilt, torso counterbalance, arm overlap, and holds. Do not equate a bounding box with a skeleton.
3. Generate several complete figures per sheet using the same reference. Use previous accepted drawings as a secondary consistency reference. Image generation is a manual/provider step, not an API implemented by this package.
4. Review every key drawing before ingestion. Record placement anchors and face-protection regions. Use a common whole-figure scale when drawings already share proportions; any additional scale correction needs pose-aware review. Do not stretch the face or normalize every pose to an identical full-body height.
5. Ingest using a grid/placement mapping. Retain the native alpha. The tool does not manufacture transparency from an opaque background.
6. Build the timeline with source frame numbers, end coverage, and explicit holds. Reuse the same drawing for equivalent held poses.
7. Render a short version, inspect transitions at native frame resolution, and change only the faulty drawing/transition. Never overwrite a reviewed version.

See [the project format](docs/project-format.md), [quality review](docs/quality-review.md), and [publication boundaries](docs/publication.md).

## Current limitations

This is sparse-drawing interpolation, not a 3D body simulation or a learned choreography controller. The face-protection step reduces geometric distortion inside a drawing; it cannot correct a wrongly drawn face or guarantee identical faces across drawings. Endpoint switching can still pop. Hair/coat motion and support-foot contact need human review. A 60fps container does not imply 60 independently drawn or physically correct poses per second.

The historical Rin v82 renderer was a targeted repair built on earlier outputs. This extracted package does **not** recreate v82 byte-for-byte. The new Belimumab pilot uses the extracted tools and separately recorded character assets.

## Distribution

The original code and documentation in this repository are MIT licensed. Character artwork, source videos, audio, generated project assets, checkpoints, and third-party code are outside that grant and are not part of the public source archive. See [THIRD_PARTY.md](THIRD_PARTY.md). No GitHub repository is created by running these tools.

## Local results and follow-up experiments

Production outputs live under Git-ignored `projects/`. See [local storage conventions](docs/local-results.md), [the Rin breakdown experiment](docs/rin-breakdown-experiment.md), and [the residual-popping investigation plan](docs/interpolation-roadmap.md). The investigation plan is not an implemented backend change.
