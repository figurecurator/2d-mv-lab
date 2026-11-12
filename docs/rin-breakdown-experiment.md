# Rin breakdown experiment v03

## Scope

The preceding Rin redraw pilot used 12 unique full-body drawings and 18 timeline keys for a 3-second clip. The character reference was Rin redrawn in the illustration style of the approved Belimumab sheet. The user identified popping at large pose changes as the central problem.

This experiment adds three inferred breakdown drawings at source frames 48, 49 and 50 between the existing frames 47 and 51. The original source itself changes drawing rapidly; these intermediate body poses are newly drawn, not frames recovered from the input video.

The added sequence represents weight transfer, knee bending/foot lift, arm crossing and partial leg extension. The original 18 keys and their images, endpoint times, renderer and model weights remain unchanged. Counts become 15 drawings and 21 timeline keys. The source interval remains [36,126) at 30fps; output remains 720×1280, 60fps, 180 frames/3 seconds.

## Observations and limits

Sequential review shows a knee-bend/foot-lift phase where the baseline jumped to an extended leg. Small appearance changes and support-foot displacement remain. The change affects only this transition; it does not fix the other pose changes in the full clip.

The maximum full-frame adjacent-pixel difference in the sampled transition decreased from about 9.783 to 8.932 on a 0–255 scale, while the sum over those steps increased from about 44.294 to 56.797. These are diagnostics, not perceptual quality scores or proof of an overall quality improvement. More intermediate drawings can add both meaningful motion and new appearance differences.

Full decode produced 180 frames, no character pixels touched the canvas boundary under the recorded threshold, decoded audio matched the baseline exactly, and renderer/model hashes matched the baseline.

## Local evidence

The local `projects/brainrot/rin-bel-style/v03-breakdown/` directory contains:

- `production/`: generation prompt, raw breakdown sheet, mapping, experiment description and preparation/review scripts.
- `project/`: original assets, additional drawings, unchanged audio input and the extended timeline.
- `renders/rin_breakdown_v03_3s.mp4`: the new full clip.
- `renders/before_after_3s.mp4`: baseline/new side-by-side at normal speed.
- `review/transition_slow_4x_repeat.mp4`: selected transition at quarter speed, three repeats, muted.
- `review/transition_frames.jpg`: consecutive before/after frames.
- `review/validation.json`: technical checks and pixel-step diagnostics.

These files are intentionally Git-ignored. This textual summary contains no character artwork, source video, audio or model weights.
