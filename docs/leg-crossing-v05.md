# Leg crossing repair v05

Experiment date: 2026-11-14. This is a local, manually guided repair of the crossing-leg interval that remained after the [native-RIFE follow-up in v04](interpolation-v04.md). It is not a change to the public CLI, the production default or the RIFE model.

## Problem

The full native-RIFE clip improved transition continuity, but where the legs cross, one leg could become thin, merge into the other or vanish. RIFE has no notion of front and back limbs, so the visibility mask cannot keep an occluded leg intact.

## Method

Only the 21 intermediate output frames in the three crossing transitions were modified: 111–117, 143–149 and 167–173 (for example, frame 111 lies between drawings 89 and 95 at u=0.125). Drawings, key timing, audio, renderer project and RIFE weights are unchanged from the v04 native clip.

1. Both legs were hand-annotated as separate polygons with strip "stations" (centre and width along each leg) on the drawings where both are visible, such as drawing 89.
2. Each visible source leg was warped independently on its own strip mesh (piecewise affine) toward the target pose.
3. Legs are composited back to front: support/rear leg first, foreground leg last, so occlusion order is explicit.
4. The upper body, hair and the background behind the removed legs keep the native-RIFE result.
5. At the exact key frames the original drawing is used, with no cross-dissolve.

## Variants

| Variant | Approach | Observed result |
| --- | --- | --- |
| Native baseline (v04) | Full-frame native RIFE | Crossing legs thin, merge or disappear |
| Guided | Pre-align both drawings' legs, then native RIFE on the lower body | Parts of the shoe go missing |
| Foreground only | Repair only the foreground leg | Support foot goes missing |
| Visible legs | Warp both legs, fade into the endpoint pose | Double outlines from the fade |
| Selected (v05) | Warp both legs, no fade, exact endpoint drawing | Faint background ghosting |
| **Selected b (v05b)** | As v05, with the remaining ghosting removed | Chosen candidate |

## Result and limits

In the sampled crossing frames, v05b keeps both legs visible and in a consistent front/back order, where the native clip lost them. Remaining defects:

- Shoe shape and angle can change abruptly at the exact endpoint drawing.
- Warped source texture can stretch along the strip mesh.
- Masks, meshes and occlusion order are manual; hidden texture is not inferred and there is no physical contact solver.

The full clip decoded to 180 frames at 720x1280 and 60fps (3 seconds). Decoded audio is identical to the native v04 clip.

Because the method depends on per-drawing hand annotations, it is a repair technique for a specific clip, not a candidate default. Generalising it would require reviewed limb landmarks or segmentation for each drawing.

## Local records

Everything below is relative to the ignored directory `projects/experiments/leg-crossing-v05/`:

- `rin_leg_crossing_v05b_3s.mp4`: selected full clip.
- `native_vs_leg_crossing_v05.mp4`: native v04 left, v05b right.
- `review/native_vs_crossing_slow.mp4`: frames 108–120 at 15fps, three repeats, muted. Per-variant slow previews and frame stills are in `review/`.
- The other variant clips (`rin_leg_guided_3s.mp4`, `rin_foreground_leg_3s.mp4`, `rin_visible_legs_3s.mp4`, `rin_leg_crossing_v05_3s.mp4`, `rin_native_baseline_3s.mp4`).
- `annotations.json`: leg polygons and strip stations.
- `receipt.json`, `*_receipt.json`, `validation.json`: input/model/script hashes, modified frames and limitations.
- `scripts/`: machine-specific experiment scripts requiring the private inputs.

Character art, media, weights and machine-specific scripts remain ignored.
