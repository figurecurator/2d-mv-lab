"""Generate full-body pose drawings with a local ComfyUI server.

The character's look comes from one approved reference image; each pose comes
from a guide image such as the matching source-video frame. Qwen-Image-Edit
receives both pictures and an instruction, and ComfyUI's background-removal
model supplies a foreground mask. Results are written as RGBA drawings that the
existing ``ingest`` step can place (one drawing per 1x1 sheet).

Nothing is downloaded: every model named in the plan must already be installed
in the ComfyUI instance. Generated drawings still need human review before use.
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .core import sha256

DEFAULT_MODELS = {
    "unet": "qwen-image-edit-2511-Q4_K_M.gguf",
    "clip": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    "vae": "qwen_image_vae.safetensors",
    "bg_removal": "birefnet.safetensors",
    "lora": None,
    "lora_strength": 1.0,
}
DEFAULT_PROMPT = (
    "Draw the character from Picture 1 performing the exact full-body pose of the person in Picture 2. "
    "Keep the face, hairstyle, outfit, colours and illustration style of Picture 1 unchanged. "
    "Show the whole body from head to feet, centred, on a plain white background, with no other people or objects."
)
SETTINGS = {"seed": 0, "steps": 40, "cfg": 4.0, "shift": 3.0, "sampler": "euler",
            "scheduler": "simple", "width": 832, "height": 1248, "negative_prompt": ""}


def read_plan(path: Path) -> tuple[dict, Path]:
    path = path.resolve()
    plan = json.loads(path.read_text(encoding="utf-8-sig"))
    root = path.parent
    if not (root / plan["reference"]).is_file():
        raise FileNotFoundError(f"Missing reference image: {plan['reference']}")
    frames = [p["frame"] for p in plan["poses"]]
    if not frames or len(frames) != len(set(frames)):
        raise ValueError("Poses need unique frame numbers")
    for key, value in {**SETTINGS, **plan}.items():
        if key in ("width", "height") and (int(value) <= 0 or int(value) % 16):
            raise ValueError(f"{key} must be a positive multiple of 16")
    return plan, root


def build_graph(plan: dict, reference: str, guide: str, seed: int, prompt: str, prefix: str) -> dict:
    """Return a ComfyUI API graph for one reference + pose-guide edit."""
    s = {**SETTINGS, **plan}
    m = {**DEFAULT_MODELS, **plan.get("models", {})}
    g = {
        "unet": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": m["unet"]}},
        "clip": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": "qwen_image"}},
        "vae": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
        "reference": {"class_type": "LoadImage", "inputs": {"image": reference}},
        "guide": {"class_type": "LoadImage", "inputs": {"image": guide}},
    }
    model = ["unet", 0]
    if m["lora"]:
        g["lora"] = {"class_type": "LoraLoaderModelOnly",
                     "inputs": {"model": model, "lora_name": m["lora"], "strength_model": m["lora_strength"]}}
        model = ["lora", 0]
    for name, text in [("positive", prompt), ("negative", s["negative_prompt"])]:
        g[name] = {"class_type": "TextEncodeQwenImageEditPlus",
                   "inputs": {"clip": ["clip", 0], "prompt": text, "vae": ["vae", 0],
                              "image1": ["reference", 0], "image2": ["guide", 0]}}
    g.update({
        "sampling": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": model, "shift": s["shift"]}},
        "cfgnorm": {"class_type": "CFGNorm", "inputs": {"model": ["sampling", 0], "strength": 1.0}},
        "latent": {"class_type": "EmptySD3LatentImage",
                   "inputs": {"width": s["width"], "height": s["height"], "batch_size": 1}},
        "sampler": {"class_type": "KSampler",
                    "inputs": {"model": ["cfgnorm", 0], "positive": ["positive", 0], "negative": ["negative", 0],
                               "latent_image": ["latent", 0], "seed": seed, "steps": s["steps"], "cfg": s["cfg"],
                               "sampler_name": s["sampler"], "scheduler": s["scheduler"], "denoise": 1.0}},
        "decode": {"class_type": "VAEDecode", "inputs": {"samples": ["sampler", 0], "vae": ["vae", 0]}},
        "save_rgb": {"class_type": "SaveImage", "inputs": {"images": ["decode", 0], "filename_prefix": prefix}},
        "bg_model": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": m["bg_removal"]}},
        "bg_mask": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["bg_model", 0], "image": ["decode", 0]}},
        "mask_image": {"class_type": "MaskToImage", "inputs": {"mask": ["bg_mask", 0]}},
        "save_mask": {"class_type": "SaveImage", "inputs": {"images": ["mask_image", 0], "filename_prefix": prefix + "_mask"}},
    })
    return g


def with_alpha(rgb: Image.Image, mask: Image.Image, threshold: int = 8) -> np.ndarray:
    """Attach a foreground mask as alpha; faint mask noise becomes fully transparent."""
    pixels = np.asarray(rgb.convert("RGB"), np.uint8)
    alpha = np.asarray(mask.convert("L").resize(rgb.size, Image.BILINEAR), np.uint8).copy()
    alpha[alpha < threshold] = 0
    if alpha.max() < 128:
        raise ValueError("Background removal found no opaque subject")
    return np.dstack([pixels, alpha])


class ComfyClient:
    """Minimal client for a local ComfyUI HTTP API."""

    def __init__(self, server: str = "http://127.0.0.1:8188", timeout: float = 1800):
        self.server = server.rstrip("/")
        self.timeout = timeout
        self.client_id = uuid.uuid4().hex

    def _request(self, path: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
        request = urllib.request.Request(self.server + path, data=data, headers=headers or {})
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()

    def upload(self, path: Path) -> str:
        boundary = uuid.uuid4().hex
        body = b"".join([
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n".encode(),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
            "Content-Type: image/png\r\n\r\n".encode(), path.read_bytes(), f"\r\n--{boundary}--\r\n".encode()])
        reply = json.loads(self._request("/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))
        return (reply.get("subfolder") + "/" if reply.get("subfolder") else "") + reply["name"]

    def run(self, graph: dict) -> dict:
        payload = json.dumps({"prompt": graph, "client_id": self.client_id}).encode()
        reply = json.loads(self._request("/prompt", payload, {"Content-Type": "application/json"}))
        if reply.get("node_errors"):
            raise RuntimeError(f"ComfyUI rejected the graph: {reply['node_errors']}")
        prompt_id = reply["prompt_id"]
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            history = json.loads(self._request(f"/history/{prompt_id}")).get(prompt_id)
            if history:
                status = history.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI execution failed: {status.get('messages')}")
                if status.get("completed", True):
                    return {"prompt_id": prompt_id, "outputs": history["outputs"]}
            time.sleep(1)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish")

    def image(self, info: dict) -> Image.Image:
        query = urllib.parse.urlencode({k: info.get(k, "") for k in ("filename", "subfolder", "type")})
        from io import BytesIO
        return Image.open(BytesIO(self._request("/view?" + query))).copy()


def generate(plan_path: Path, out: Path, client) -> list[dict]:
    """Run every pose in the plan; refuse to touch an existing output folder."""
    if out.exists():
        raise FileExistsError(out)
    plan, root = read_plan(plan_path)
    reference_path = root / plan["reference"]
    staging = out.with_name(out.name + ".partial")
    if staging.exists():
        raise FileExistsError(staging)
    (staging / "raw").mkdir(parents=True)
    reference = client.upload(reference_path)
    base_seed = int(plan.get("seed", SETTINGS["seed"]))
    records = []
    for index, pose in enumerate(plan["poses"]):
        guide_path = root / pose["pose_image"]
        prompt = " ".join(filter(None, [plan.get("prompt", DEFAULT_PROMPT), pose.get("prompt_extra")]))
        seed = int(pose.get("seed", base_seed + index))
        name = f"pose_{pose['frame']:04d}"
        graph = build_graph(plan, reference, client.upload(guide_path), seed, prompt, f"pose_mv/{uuid.uuid4().hex[:8]}_{name}")
        result = client.run(graph)
        rgb = client.image(result["outputs"]["save_rgb"]["images"][0])
        mask = client.image(result["outputs"]["save_mask"]["images"][0])
        rgb.save(staging / "raw" / f"{name}.png")
        mask.convert("L").save(staging / "raw" / f"{name}_mask.png")
        Image.fromarray(with_alpha(rgb, mask), "RGBA").save(staging / f"{name}.png")
        records.append({"frame": pose["frame"], "file": f"{name}.png", "seed": seed, "prompt": prompt,
                        "prompt_id": result["prompt_id"], "pose_image": pose["pose_image"],
                        "pose_image_sha256": sha256(guide_path), "output_sha256": sha256(staging / f"{name}.png"),
                        "graph": graph})
        print(f"Generated {index + 1}/{len(plan['poses'])}: {name}", flush=True)
    receipt = {"plan": plan_path.name, "plan_sha256": sha256(plan_path.resolve()),
               "reference": plan["reference"], "reference_sha256": sha256(reference_path),
               "models": {**DEFAULT_MODELS, **plan.get("models", {})}, "settings": {**SETTINGS, **{k: plan[k] for k in SETTINGS if k in plan}},
               "review_required": True, "poses": records}
    (staging / "generation.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    staging.rename(out)
    return records


def extract_frames(video: Path, frames: list[int], out: Path) -> list[Path]:
    """Save the listed source-video frames as PNG pose guides."""
    out.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise FileNotFoundError(video)
    written = []
    try:
        for frame in frames:
            target = out / f"frame_{frame:04d}.png"
            if target.exists():
                raise FileExistsError(target)
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame)
            ok, pixels = capture.read()
            if not ok:
                raise ValueError(f"Cannot read frame {frame} from {video.name}")
            Image.fromarray(cv2.cvtColor(pixels, cv2.COLOR_BGR2RGB)).save(target)
            written.append(target)
    finally:
        capture.release()
    return written
