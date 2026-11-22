# Interpolation comparison v04

Experiment date: 2026-11-13. Twenty local runs compare ten configurations on two input suites. Native RIFE synthesis visibly improves the continuity of the reviewed pose change compared with the custom endpoint-switching adapter. It is the preferred next integration candidate, with leg occlusion still unresolved.

## Controlled setup

All short comparisons use source frames 47 through 51 inclusive, rendered as nine frames at 720x1280 and 60fps. The sparse suite uses the two endpoint drawings; the breakdown suite also uses three reviewed intermediate drawings. The comparison previews play at 15fps (four times slower), repeat three times and contain no audio. Drawings and timing are held fixed within each suite.

| Configuration | Observed result |
| --- | --- |
| Current endpoint switch | Abrupt contour changes when the selected drawing switches |
| Native RIFE RGB | Better continuity while retaining relatively clear face and line detail |
| Native RIFE RGBA | Premultiplied-alpha synthesis using the native flows and mask; not a validated transparent production backend |
| Guarded bidirectional synthesis | Existing independent flow guards can misalign the warped inputs and double shoe outlines |
| Face/support-foot registration | Stabilizes selected anchors but changes whole-body orientation; no consistent improvement |
| Bounded C1 flow-velocity correction | No clear benefit here; the sparse suite has no internal key boundary and is an expected no-op |
| GMFSS anime Union | Relatively smooth but softer face and clothing detail |
| FILM | Doubled or fragmented moving-leg outlines in the sparse transition |
| AnimeInterp, zero initialization | Softer detail; original SGM preprocessing was not run |
| AnimeInterp, DIS initialization | Softer detail; original SGM preprocessing was not run |

These are observations for one character and motion interval, not a general model ranking. There are no ground-truth inbetweens. Smaller pixel-change measurements can result from blur and must not be read as higher quality.

## Full three-second native-RIFE follow-up

The same 21-key project was rendered with native RIFE RGB synthesis on the fixed gray background, using the existing checkpoint and timing. This uses the model's final synthesized output rather than the custom whole-endpoint switch and flow/face guards.

The side-by-side review supports a visible improvement in transition continuity. Crossing legs can still become thin, merged or warped: visibility and anatomy through occlusion need further work. This remaining defect does not negate the continuity improvement. The next experiment should focus on the crossing interval and explicit front/back limb handling before adopting a new default. That follow-up is documented in [leg crossing repair v05](leg-crossing-v05.md).

Both full clips decoded to 180 frames at 720x1280, with no figure contact at the frame edges. Decoded audio was identical. Maximum pixel-step changed from about 14.60 to 14.27; this is a diagnostic, not evidence that the visual improvement is only that numerical difference.

## Runtime and scope

RIFE and FILM used the installed ComfyUI frame-interpolation implementations. GMFSS used its author-provided PyTorch softsplat fallback on CUDA. AnimeInterp used the author's NoCupy architecture and checkpoint with zero/DIS initial flow; these runs do not evaluate the full paper pipeline because SGM preprocessing was omitted. ToonCrafter was not tested in this comparison.

Official upstream references: [RIFE](https://github.com/hzwer/ECCV2022-RIFE), [GMFSS Fortuna](https://github.com/98mxr/GMFSS_Fortuna), [FILM](https://github.com/google-research/frame-interpolation), [AnimeInterp](https://github.com/lisiyao21/AnimeInterp).

## Local records

Everything below is relative to the ignored directory `projects/experiments/interpolation-v04/`:

- `runs/`: per-configuration frames, previews and receipts.
- `review/models_sparse.mp4` and `review/models_breakdowns.mp4`: six-model grids.
- `review/algorithms_sparse.mp4` and `review/algorithms_breakdowns.mp4`: six synthesis/alignment controls.
- `full/rin_native_rife_3s.mp4`: full native-RIFE follow-up.
- `full/before_after_native_rife.mp4`: current v03 left, native RIFE right.
- `scripts/`: local experiment and assembly scripts, requiring the private inputs and machine-specific runtime.
- `all_results.json`, `diagnostics.csv`, `conclusions.json`, `downloads.json` and per-run receipts: provenance, measurements and limitations.

Media, weights, upstream code and machine-specific scripts remain ignored. This commit documents completed experiments; the public CLI and production default remain unchanged.
