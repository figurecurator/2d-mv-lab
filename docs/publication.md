# Public-source staging

Proposed destination: `figurecurator/2d-mv-lab`.

This directory is the source-only staging package. It contains an independent renderer and synthetic fixture; it does not contain the historical Rin outputs, reference dance video/music, private Space exports, generated character sheets, weights or accounts. The Belimumab pilot is a separate local project.

Before publishing, run core tests and the synthetic render from an installed copy, confirm that the tested pilot can be rendered from its recorded configuration, inspect the archive contents, and choose which character assets (if any) to distribute under a separately stated asset license. The source-code MIT grant does not change the status of the input/output media or dependencies.

Known remaining scope: the image-generation stage is human/agent operated, the optional RIFE adapter uses an internal upstream API, clean installation of the entire external GPU stack is not automated, and visual quality still requires review. Present these limitations in the initial release rather than promising a one-command video generator.

Never commit private runtime configuration, account keys, model caches, or the whole production archive. A source-only archive and a local reproducibility project are separate deliverables.
