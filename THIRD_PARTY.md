# External components

No third-party source code or model weights are included in this archive.

| Component | Role | Acquisition |
| --- | --- | --- |
| NumPy, Pillow, OpenCV | Arrays, transparent assets, video inspection | Installed dependencies from pyproject.toml |
| FFmpeg | Encode, mux and full decode | User-supplied executable |
| PyTorch, safetensors | Optional RIFE execution and checkpoint loading | Separately installed GPU/runtime environment |
| ComfyUI frame-interpolation implementation | Optional model loader and inference | User-supplied ComfyUI checkout |
| RIFE checkpoint | Optional optical-flow/interpolation weights | User-supplied compatible weights |

ComfyUI's locally inspected LICENSE identifies GPL version 3. This project does not copy or relicense that code. The optional adapter imports the user's installation and records the checkpoint digest. Check the exact versions and their own license notices when distributing a combined runtime. Model weights and source media need their own provenance; the source-code license does not grant rights to them.

The pilot's character reference is the approved Belimumab v1 sheet in the user's private 《이계약국 영업일지》 Space. It is intentionally outside the public-source archive. The original dance video and audio are also outside the archive.
