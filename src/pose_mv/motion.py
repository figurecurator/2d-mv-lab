"""Optional adapter to a separately installed ComfyUI RIFE implementation.

No upstream model source or weights are vendored. The adapter's tested upstream
revision and weight hash belong in the per-run validation receipt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from .core import flatten, protect_flow


class RifeMotion:
    def __init__(self, comfy_root: Path, weights: Path, device: str = "cuda"):
        import torch
        from safetensors.torch import load_file

        self.torch = torch
        self.device = device
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable; request --device cpu explicitly")
        self.dtype = torch.float16 if device.startswith("cuda") else torch.float32
        sys.path.insert(0, str(comfy_root.resolve()))
        from comfy_extras.nodes_frame_interpolation import FrameInterpolationModelLoader

        self.model = FrameInterpolationModelLoader._detect_and_load(load_file(str(weights))).eval().to(device=device, dtype=self.dtype)
        self.captured = []
        self.original_warp = self.model.warp

        def record(pixels, flow):
            if pixels.shape[1] == 3:
                self.captured.append(flow)
            return self.original_warp(pixels, flow)

        self.model.warp = record
        torch.set_num_threads(2)

    def tensor(self, pixels):
        torch = self.torch
        t = torch.from_numpy(np.ascontiguousarray(pixels)).permute(2, 0, 1)[None].to(self.device, self.dtype)
        h, w = pixels.shape[:2]
        return torch.nn.functional.pad(t, (0, (-w) % 64, 0, (-h) % 64), mode="replicate")

    def pair(self, a, b):
        with self.torch.inference_mode():
            self.a, self.b = self.tensor(a), self.tensor(b)
            self.sa = self.a[:, :3] + .5 * (1 - self.a[:, 3:4])
            self.sb = self.b[:, :3] + .5 * (1 - self.b[:, 3:4])
            self.cache = {"img0": self.model.extract_features(self.sa), "img1": self.model.extract_features(self.sb)}
            self.height, self.width = a.shape[:2]

    def at(self, u, face_box=None):
        torch = self.torch
        with torch.inference_mode():
            self.captured.clear()
            self.model(self.sa, self.sb, float(u), cache=self.cache)
            if len(self.captured) < 2:
                raise RuntimeError("Unsupported upstream RIFE warp API; no output written silently")
            choose_a = u < .5
            raw = self.captured[-2 if choose_a else -1][0].float().permute(1, 2, 0).cpu().numpy()
            flow, audit = protect_flow(raw, face_box)
            flow = torch.from_numpy(flow).permute(2, 0, 1)[None].to(self.device, self.dtype)
            result = self.original_warp(self.a if choose_a else self.b, flow)
            pixels = result[0, :, :self.height, :self.width].float().permute(1, 2, 0).cpu().numpy()
            return np.clip(pixels, 0, 1), {**audit, "endpoint": "a" if choose_a else "b"}


class NativeRifeMotion(RifeMotion):
    """Model-native RIFE RGB synthesis on the final opaque background.

    Both drawings are first composited over the render background, then the
    model's own bidirectional warp and visibility mask produce each frame. No
    endpoint switching or flow/face guard is applied. The output is opaque, so
    this backend cannot produce a transparent render.
    """

    def __init__(self, comfy_root: Path, weights: Path, device: str = "cuda", background=(214, 214, 214)):
        super().__init__(comfy_root, weights, device)
        self.model.warp = self.original_warp
        self.background = background

    def pair(self, a, b):
        with self.torch.inference_mode():
            self.sa = self.tensor(flatten(a, self.background))
            self.sb = self.tensor(flatten(b, self.background))
            self.cache = {"img0": self.model.extract_features(self.sa), "img1": self.model.extract_features(self.sb)}
            self.height, self.width = a.shape[:2]

    def at(self, u, face_box=None):
        with self.torch.inference_mode():
            result = self.model(self.sa, self.sb, float(u), cache=self.cache)
            rgb = result[0, :3, :self.height, :self.width].float().permute(1, 2, 0).cpu().numpy()
        rgb = np.clip(rgb, 0, 1)
        opaque = np.ones(rgb.shape[:2] + (1,), rgb.dtype)
        return np.concatenate([rgb, opaque], axis=-1), {"synthesis": "native-rgb"}
