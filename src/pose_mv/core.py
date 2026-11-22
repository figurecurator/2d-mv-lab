"""Portable project validation, transparent-sheet ingestion, and bounded flow warps."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_project(path: Path) -> tuple[dict, Path]:
    path = path.resolve()
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    width, height = data["canvas"]
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError("Canvas dimensions must be positive even integers")
    start, end = data["source_range"]
    sfps, fps = data["source_fps"], data["output_fps"]
    if not all(math.isfinite(float(v)) for v in [start, end, sfps, fps]):
        raise ValueError("Non-finite timing value")
    if start < 0 or end <= start or sfps <= 0 or fps <= 0:
        raise ValueError("Invalid frame range or frame rate")
    count = (end - start) * fps / sfps
    if abs(count - round(count)) > 1e-6:
        raise ValueError("Duration must contain a whole number of output frames")
    keys = data["keys"]
    frames = [k["frame"] for k in keys]
    if len(frames) < 2 or frames != sorted(set(frames)):
        raise ValueError("Keys must have unique, increasing source frame numbers")
    if frames[0] > start or frames[-1] < end:
        raise ValueError("Key drawings must cover both ends of source_range")
    for left, right in zip(keys, keys[1:]):
        hold = left.get("hold_until", left["frame"])
        if not left["frame"] <= hold < right["frame"]:
            raise ValueError("hold_until must lie within the key interval")
    return data, path.parent


def rgba(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        if image.mode != "RGBA":
            raise ValueError(f"Native RGBA required: {path.name}")
        pixels = np.asarray(image, dtype=np.uint8).copy()
    if pixels[..., 3].min() != 0 or pixels[..., 3].max() < 128:
        raise ValueError(f"Expected transparent background and opaque subject: {path.name}")
    return pixels


def flatten(pixels: np.ndarray, background) -> np.ndarray:
    """Composite premultiplied RGBA in [0, 1] over an opaque RGB background given in 0-255."""
    bg = np.asarray(background, np.float32).reshape(1, 1, 3) / 255
    return pixels[..., :3] + bg * (1 - pixels[..., 3:4])


def alpha_box(pixels: np.ndarray) -> tuple[int, int, int, int]:
    yy, xx = np.where(pixels[..., 3] > 16)
    if len(xx) == 0:
        raise ValueError("Empty sprite")
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def ingest(sheet_path: Path, mapping_path: Path, out: Path) -> list[dict]:
    """Split a grid without discarding detached hair, fingers, or translucent parts.

    Cell landmarks are explicit coordinates, so no character-specific detector or
    hidden body-proportion heuristic is needed. All paths are supplied by caller.
    """
    if out.exists():
        raise FileExistsError(out)
    image = rgba(sheet_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    columns, rows = mapping["grid"]
    if columns <= 0 or rows <= 0 or len(mapping["poses"]) > columns * rows:
        raise ValueError("Invalid grid")
    cw, ch = image.shape[1] // columns, image.shape[0] // rows
    width, height = mapping["canvas"]
    results = []
    prepared = []
    for entry in mapping["poses"]:
        cell = entry["cell"]
        if not 0 <= cell < columns * rows:
            raise ValueError("Cell index outside sheet")
        x, y = cell % columns * cw, cell // columns * ch
        sprite = image[y:y + ch, x:x + cw]
        box = alpha_box(sprite)
        if box[0] <= 1 or box[1] <= 1 or box[2] >= cw - 1 or box[3] >= ch - 1:
            raise ValueError(f"Figure touches cell edge: {cell}; inspect cropping")
        scale = float(entry["scale"])
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("Scale must be finite and positive")
        anchor = np.array(entry["anchor"], dtype=float)
        target = np.array(entry["target"], dtype=float)
        offset = target - scale * anchor
        matrix = np.array([[scale, 0, offset[0]], [0, scale, offset[1]]], np.float32)
        # Warp premultiplied color to avoid dark fringes at transparent edges.
        floating = sprite.astype(np.float32) / 255
        floating[..., :3] *= floating[..., 3:4]
        placed = cv2.warpAffine(floating, matrix, (width, height), flags=cv2.INTER_LANCZOS4)
        placed = np.clip(placed, 0, 1)
        placed[..., :3] = np.divide(placed[..., :3], placed[..., 3:4], out=np.zeros_like(placed[..., :3]), where=placed[..., 3:4] > 1 / 255)
        pixels = np.uint8(np.clip(placed, 0, 1) * 255 + .5)
        pb = alpha_box(pixels)
        if pb[0] <= 0 or pb[1] <= 0 or pb[2] >= width or pb[3] >= height:
            raise ValueError(f"Placed figure clipped by canvas: {cell}")
        name = f"pose_{entry['frame']:04d}.png"
        prepared.append((name, pixels))
        results.append({"frame": entry["frame"], "file": name, "cell": cell,
                        "source_alpha_box": box, "placed_alpha_box": pb,
                        "scale": scale, "anchor": anchor.tolist(), "target": target.tolist()})
    out.mkdir(parents=True)
    for name, pixels in prepared:
        Image.fromarray(pixels).save(out / name)
    (out / "ingest.json").write_text(json.dumps({"sheet_sha256": sha256(sheet_path), "poses": results}, indent=2), encoding="utf-8")
    return results


def sample_timeline(keys: list[dict], frame: float, max_transition: float = 4) -> tuple[int, int, float]:
    frames = np.array([key["frame"] for key in keys])
    index = max(0, min(int(np.searchsorted(frames, frame, side="right")) - 1, len(keys) - 1))
    if index == len(keys) - 1 or abs(frame - frames[index]) < 1e-8:
        return index, index, 0.0
    left, right = keys[index], keys[index + 1]
    begin = max(left.get("hold_until", left["frame"]), right["frame"] - max_transition)
    if frame <= begin:
        return index, index, 0.0
    return index, index + 1, float((frame - begin) / (right["frame"] - begin))


def protect_flow(field: np.ndarray, face_box: list[float] | None, sigma: float = 5, limit: float = .30) -> tuple[np.ndarray, dict]:
    """Bound local stretching and use one translation through the face core."""
    field = cv2.GaussianBlur(np.asarray(field, np.float32), (0, 0), sigma)
    gradient = np.stack([np.gradient(field, axis=0), np.gradient(field, axis=1)])
    energy = np.sqrt(np.sum(gradient ** 2, axis=(0, 3)))
    peak = float(energy.max())
    # A bad hand/hair correspondence must not attenuate the entire body's
    # motion. Keep smooth fields intact; taper only the problematic region.
    gain = np.minimum(1.0, limit / np.maximum(energy, 1e-6))
    gain = cv2.GaussianBlur(gain, (0, 0), 4)
    base = np.median(field.reshape(-1, 2), axis=0)
    field = base + (field - base) * gain[..., None]
    if face_box:
        x0, y0, x1, y1 = map(int, face_box)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(field.shape[1], x1), min(field.shape[0], y1)
        if x1 <= x0 or y1 <= y0:
            raise ValueError("Face protection box outside canvas")
        shift = np.median(field[y0:y1, x0:x1].reshape(-1, 2), axis=0)
        yy, xx = np.mgrid[:field.shape[0], :field.shape[1]]
        dx = np.maximum(np.maximum(x0 - xx, xx - x1), 0)
        dy = np.maximum(np.maximum(y0 - yy, yy - y1), 0)
        weight = np.clip(1 - np.hypot(dx, dy) / 35, 0, 1)[..., None]
        field = field * (1 - weight) + shift * weight
    return np.ascontiguousarray(field, dtype=np.float32), {
        "raw_gradient_peak": peak, "local_gain": float(gain.min()),
        "median_local_gain": float(np.median(gain)),
    }
