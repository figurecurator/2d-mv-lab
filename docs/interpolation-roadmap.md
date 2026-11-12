# Reducing residual popping

Research and code review date: 2026-11-13. The approaches below are proposals; no new backend or algorithm described here has been implemented or benchmarked by this documentation commit.

## Primary issue in the current adapter

`RifeMotion.at` runs the RIFE model to obtain intermediate flows, but discards its final synthesized RGB result. It selects the full A drawing before `u=0.5` and the full B drawing afterward, filters that endpoint's flow, and warps only that selected drawing. This was designed to avoid ghosting but can create a discontinuity in face shape, linework and clothing when the chosen drawing changes.

The installed upstream RIFE implementation instead warps both inputs and combines them with its predicted visibility mask. Therefore the current result should not be treated as a benchmark of unmodified RIFE. The endpoint switch is a specific hypothesis to test, not proof that it explains every remaining artifact.

## Suggested experiment order

1. Preserve the present backend as the baseline. Test model-native RIFE synthesis and an alpha-aware, bidirectional alternative on the same short transition with identical drawings/timing. Both endpoints should first be warped to the same intermediate time, then combined using visibility/confidence. Simply fading the unwarped drawings risks double eyes and limbs. A native-RGB trial can use a fixed composite background; a transparent production path needs explicit alpha/visibility handling.
2. Register drawings using reviewed face/torso/support-foot landmarks. Apply whole-figure similarity alignment and contact-aware constraints. Fix a planted support foot over its contact interval; do not force every full-body bounding box to the same height. Pose-specific differences must not be mistaken for scale noise.
3. Regularize landmark/flow trajectories across adjacent key intervals, preserving intended holds and movement accents. Check continuity at key boundaries as well as the midpoint. Optimize acceleration/contact consistency rather than smoothing every frame indiscriminately.
4. Compare alternative model families only after matching inputs, synthesis policy and evaluation interval. Evaluate silhouettes, facial stability, limb occlusion and contact at normal speed and with consecutive frames. Pixel-change diagnostics alone are insufficient.

## Model candidates

| Candidate | Why test it | Practical limit |
| --- | --- | --- |
| [RIFE](https://github.com/hzwer/ECCV2022-RIFE) with model-native synthesis | Existing local model/runtime; separates our custom endpoint policy from model capability | Alpha-aware production integration still needs work; no guarantee of stable independently generated faces |
| [GMFSS Fortuna](https://github.com/98mxr/GMFSS_Fortuna) | Its authors explicitly target anime video interpolation | Published setup uses an older Python/PyTorch/CUDA stack; compatibility with this machine's runtime is untested |
| [FILM](https://github.com/google-research/frame-interpolation) | Designed for interpolation with large motion | Does not by itself establish anatomical or character consistency; local checkpoint/runtime integration untested |
| [AnimeInterp](https://github.com/lisiyao21/AnimeInterp) | Animation-specific segment matching and flow refinement target flat color regions and large nonlinear motion | Original environment is old; useful as a research comparison, not the first integration task |
| [ToonCrafter](https://github.com/Doubiiu/ToonCrafter) | Generative cartoon interpolation can propose motion absent between endpoint drawings | It may change drawing details/motion; that is an inference from its generative design. It is not validated here as a finishing filter for strict character-preserving repair |

The source repository descriptions support each candidate's purpose; they do not establish which model will look best on this pilot. No weights or upstream implementations are bundled or re-licensed by listing these candidates.

The first recommended test is changing synthesis/visibility handling while holding the current RIFE checkpoint and artwork fixed. A model swap first would confound that diagnosis.
