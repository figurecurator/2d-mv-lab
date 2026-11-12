# Local production results

Store production assets and outputs under `projects/`. This entire directory is excluded by the existing `.gitignore` rule. Do not force-add its contents.

The local collection includes:

- `projects/brainrot/belimumab-sales-log/v02/`: Belimumab pilot assets, project and renders.
- `projects/brainrot/rin-bel-style/v02-baseline/`: Rin redraw baseline assets, project and renders.
- `projects/brainrot/rin-bel-style/v03-breakdown/`: added-breakdown experiment, renders and review material.
- `projects/brainrot/rin-legacy/v82/`: previous Rin videos.
- `projects/review/higgsfield-belimumab/`: comparison input.
- `projects/deliverables/2026-11-13/`: previous delivery files.

`projects/RESULTS_INDEX.json` identifies the latest local result. `projects/collection_manifest.json` records hashes for the initial collection snapshot. It is not a continuously updated manifest for every later experiment. `projects/README.local.txt` provides local navigation.

Each new experiment should keep its assets, prompt provenance, placement mappings, timeline, input/model/code hashes, videos and validation together in a new version directory. Preserve earlier versions. Keep public documentation and reusable code outside `projects/`; keep character art, source media, model weights and machine-specific production records inside ignored local directories.

This repository convention keeps results available in the checkout without publishing them as source code. The public repository alone does not contain the private pilot media needed to reproduce these character-specific videos.
