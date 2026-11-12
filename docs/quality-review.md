# Review a short pilot

Review the same pose sequence at normal speed, as sequential frames, and as fixed face crops. Compare equivalent body poses rather than treating every pose-dependent silhouette difference as a scale error.

## Character consistency

- Same face/jaw, eye spacing and size, horns, hairstyle, costume, and rendering style.
- Whole-figure similarity placement from measured face landmarks; avoid head-only nonrigid rescaling.
- Check differences at sheet boundaries. Shared references improve consistency but do not establish it automatically.
- Inspect semi-transparent edges against both light and dark backgrounds.

## Motion

- Support foot stays planted during weight transfer; the opposite knee and pelvis react.
- Head, torso, and pelvis counterbalance rather than moving as unrelated parts.
- Elbows, wrists, knees, shoe soles and coat overlap remain anatomically readable.
- Preserve intentional source holds and short accents. Do not smooth them away just to increase fps.
- Check face-protection boundary and endpoint swaps. The flow guard is a distortion limit, not a correctness certificate.

## Technical receipt

Check complete decode, expected duration/count, timestamp order, source/input hashes, native alpha, and no canvas clipping. If audio is included, compare the decoded output against the intended source interval and record the result separately. These checks do not establish perceptual quality or character approval.

Retain rejected drafts under distinct filenames. Write a new version if changing drawings, timing or motion parameters.
