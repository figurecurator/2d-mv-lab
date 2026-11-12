# Initial repository publication plan

## Repository settings

| Field | Prepared value |
| --- | --- |
| Owner | `figurecurator` |
| Name | `2d-mv-lab` |
| Visibility | Public |
| Default branch | `main` |
| Description | Human-reviewed 2D pose-sheet animation tools with explicit timing, optional RIFE interpolation, and validation receipts. |
| Code/documentation license | MIT |
| Suggested initial commit | `Initial release of pose-sheet animation tools` |

## Initial contents

Publish the package sources, six core tests, synthetic fixture, English/Korean README, MIT license, dependency notices, project format, review guidance, and the textual Belimumab case study. Keep the public source archive separate from the private pilot project archive.

The source tree contains no character sheets, production video/music, model weights, machine-specific runtime configuration or historical Rin version folders. The case study states which steps are manual, which are source-specific, and what the renderer does not guarantee.

## Validation already performed

- Six core tests passed.
- Python source distribution and wheel built; the wheel was installed into a separate target directory.
- The installed wheel rendered the synthetic fixture and decoded its expected 60 frames.
- The source renderer produced the 180-frame GPU Belimumab pilot, recorded input/model/code hashes, and decoded the result.
- Pilot audio and frame-edge checks are recorded separately from perceptual review.

These are local checks, not a GitHub Actions run. A fresh installation of the external GPU stack has not been automated or validated. The optional RIFE adapter uses internal upstream APIs.

## Current status

Prepared locally. GitHub search returned no matching accessible repository for this name at the time of preparation; that is not a guarantee that the name can be created. No repository creation, push, release upload, or public media upload has been performed.
