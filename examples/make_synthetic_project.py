"""Create an original geometric fixture, not a substitute character artwork."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(sys.argv[1])
root.mkdir(parents=True, exist_ok=False)
for i, shift in enumerate([0, 12, 0]):
    image = Image.new("RGBA", (128, 192))
    draw = ImageDraw.Draw(image)
    draw.ellipse((44 + shift, 20, 84 + shift, 60), fill="#6750a4")
    draw.rectangle((50 + shift, 60, 78 + shift, 125), fill="#6750a4")
    draw.line((58 + shift, 120, 48, 172), fill="#6750a4", width=10)
    draw.line((70 + shift, 120, 84, 172), fill="#6750a4", width=10)
    image.save(root / f"pose_{i}.png")
data = {"canvas": [128, 192], "source_fps": 30, "output_fps": 60,
        "source_range": [0, 30], "keys": [{"frame": i * 15, "file": f"pose_{i}.png"} for i in range(3)]}
(root / "project.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
print(root / "project.json")
