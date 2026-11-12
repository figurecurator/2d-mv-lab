"""Render an explicit timeline; never infer choreography from output frame rate."""
from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .core import read_project, rgba, sample_timeline, sha256


def render(project: Path, output: Path, ffmpeg: str, backend: str,
           comfy_root: Path | None = None, weights: Path | None = None,
           device: str = "cuda") -> dict:
    if output.exists() or output.with_suffix(output.suffix + ".partial").exists():
        raise FileExistsError(output)
    data, root = read_project(project)
    width, height = data["canvas"]
    keys = data["keys"]
    images = []
    inputs = {str(project.name): sha256(project)}
    for key in keys:
        path = root / key["file"]
        pixels = rgba(path)
        if pixels.shape[:2] != (height, width):
            raise ValueError(f"Sprite canvas mismatch: {key['file']}")
        inputs[key["file"]] = sha256(path)
        pixels = pixels.astype(np.float32) / 255
        pixels[..., :3] *= pixels[..., 3:4]
        images.append(pixels)
    if backend == "rife":
        if comfy_root is None or weights is None:
            raise ValueError("rife requires --comfy-root and --weights")
        from .motion import RifeMotion
        motion = RifeMotion(comfy_root, weights, device)
    elif backend == "hold":
        motion = None
    else:
        raise ValueError("Choose rife or hold explicitly; no silent fallback")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".partial")
    start, end = data["source_range"]
    sfps, fps = data["source_fps"], data["output_fps"]
    count = round((end - start) / sfps * fps)
    duration = count / fps
    command = [ffmpeg, "-v", "error", "-n", "-f", "rawvideo", "-pixel_format", "rgb24",
               "-video_size", f"{width}x{height}", "-framerate", str(fps), "-i", "-"]
    audio = data.get("audio")
    if audio:
        path = root / audio["file"]
        inputs[audio["file"]] = sha256(path)
        command += ["-ss", str(audio.get("start_seconds", start / sfps)), "-i", str(path),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"]
    else:
        command += ["-an"]
    command += ["-t", str(duration), "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-pix_fmt", "yuv420p", "-threads", "2", "-movflags", "+faststart", "-f", "mp4", str(temporary)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    audit = []
    previous_pair = None
    background = np.array(data.get("background", [214, 214, 214]), np.float32).reshape(1, 1, 3)
    try:
        for n in range(count):
            source_frame = start + n * sfps / fps
            left, right, u = sample_timeline(keys, source_frame, data.get("max_transition_frames", 4))
            detail = {}
            if left == right or backend == "hold":
                pixels = images[left]
            else:
                if previous_pair != (left, right):
                    motion.pair(images[left], images[right])
                    previous_pair = left, right
                face_box = keys[left if u < .5 else right].get("face_box")
                pixels, detail = motion.at(u, face_box)
            result = np.uint8(np.clip(pixels[..., :3] * 255 + background * (1 - pixels[..., 3:4]), 0, 255) + .5)
            process.stdin.write(result.tobytes())
            audit.append({"output_frame": n, "source_frame": source_frame,
                          "left": keys[left]["frame"], "right": keys[right]["frame"], "u": u, **detail})
            if n % max(1, round(fps / 2)) == 0:
                print(f"Rendered {n + 1}/{count}", flush=True)
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("FFmpeg encoding failed")
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.wait()
        raise
    # Full decode before the final name becomes visible.
    subprocess.run([ffmpeg, "-v", "error", "-xerror", "-i", str(temporary), "-f", "null", "-"], check=True)
    capture = cv2.VideoCapture(str(temporary))
    decoded = 0
    timestamps = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame.shape[:2] != (height, width):
            raise ValueError("Decoded dimensions differ from project")
        timestamps.append(capture.get(cv2.CAP_PROP_POS_MSEC))
        decoded += 1
    capture.release()
    if decoded != count or any(b <= a for a, b in zip(timestamps, timestamps[1:])):
        raise ValueError(f"Decode/timestamp check failed: {decoded}/{count}")
    os.rename(temporary, output)
    receipt = {"backend": backend, "frames": count, "fps": fps, "duration_seconds": duration,
               "canvas": [width, height], "inputs_sha256": inputs, "output_sha256": sha256(output),
               "python": platform.python_version(), "opencv": cv2.__version__, "numpy": np.__version__,
               "ffmpeg_version": subprocess.check_output([ffmpeg, "-version"], text=True).splitlines()[0],
               "weights_sha256": sha256(weights) if weights else None,
               "code_sha256": {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")},
               "decode_validated": True, "strictly_increasing_timestamps": True,
               "upstream_revision": data.get("upstream_revision"), "timeline": audit}
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt


def contact(video: Path, output: Path, every: int = 6, columns: int = 8) -> None:
    from PIL import ImageDraw
    if output.exists():
        raise FileExistsError(output)
    if every <= 0 or columns <= 0:
        raise ValueError("every and columns must be positive")
    capture = cv2.VideoCapture(str(video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    pictures = []
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if index % every == 0:
            im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            im.thumbnail((180, 320))
            pictures.append((index, im))
        index += 1
    capture.release()
    if not pictures:
        raise ValueError("No decoded frames")
    canvas = Image.new("RGB", (columns * 180, ((len(pictures) + columns - 1) // columns) * 344), "#dddddd")
    draw = ImageDraw.Draw(canvas)
    for i, (frame, picture) in enumerate(pictures):
        x, y = i % columns * 180, i // columns * 344
        canvas.paste(picture, (x, y))
        draw.text((x + 3, y + 323), f"F{frame} {frame / fps:.3f}s", fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)
